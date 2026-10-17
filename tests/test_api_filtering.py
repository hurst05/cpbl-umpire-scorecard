import json
import os
import sys
import tempfile
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import app as app_module
import collector
import db as db_module


@pytest.fixture
def client(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    monkeypatch.setattr(db_module, "DB_PATH", temp_db)
    db_module.init_db()

    c = TestClient(app_module.app)
    yield c

    if os.path.exists(temp_db):
        os.remove(temp_db)


def test_fetch_schedule_filters_tier1_only(monkeypatch):
    sample_json = json.dumps({
        "Data": {
            "Games": [
                {"GameId": "2026-A-001", "GameSno": 1, "KindCode": "A", "PreExeDate": "2026-08-30T17:05:00"},
                {"GameId": "2026-B-001", "GameSno": 1, "KindCode": "B", "PreExeDate": "2026-08-30T13:00:00"},
                {"GameId": "2026-D-001", "GameSno": 1, "KindCode": "D", "PreExeDate": "2026-08-30T14:00:00"},
            ]
        }
    })

    monkeypatch.setattr(collector, "fetch_cpbl_url", lambda url: sample_json)
    games = collector.fetch_schedule_by_date("2026-08-30")
    assert len(games) == 1
    assert games[0]["game_id"] == "2026-A-001"
    assert games[0]["kind_code"] == "A"


def test_save_game_skips_non_tier1_and_zero_calls(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    monkeypatch.setattr(db_module, "DB_PATH", temp_db)
    db_module.init_db()

    # 1. Non-tier-1 game
    db_module.save_game(
        "2026-B-001",
        {
            "game_info": {"game_id": "2026-B-001", "game_sno": 1, "kind_code": "B", "date": "2026-08-30"},
            "umpire_metrics": {"total_called_pitches": 150, "overall_accuracy": 95.0},
        },
    )
    assert db_module.get_game("2026-B-001") is None

    # 2. Zero called pitches game
    db_module.save_game(
        "2026-A-002",
        {
            "game_info": {"game_id": "2026-A-002", "game_sno": 2, "kind_code": "A", "date": "2026-08-30"},
            "umpire_metrics": {"total_called_pitches": 0, "overall_accuracy": 100.0},
        },
    )
    assert db_module.get_game("2026-A-002") is None

    # 3. Valid Tier-1 with calls > 0
    db_module.save_game(
        "2026-A-003",
        {
            "game_info": {"game_id": "2026-A-003", "game_sno": 3, "kind_code": "A", "date": "2026-08-30"},
            "umpire_metrics": {"total_called_pitches": 120, "overall_accuracy": 92.0},
        },
    )
    assert db_module.get_game("2026-A-003") is not None

    if os.path.exists(temp_db):
        os.remove(temp_db)


def test_api_game_analysis_rejects_non_tier1(client, monkeypatch):
    def mock_fetch(gid):
        return {"game": {"gameId": gid, "kindCode": "B", "liveLog": []}, "players": {}}

    monkeypatch.setattr(app_module, "fetch_game_detail", mock_fetch)
    resp = client.get("/api/game/2026-B-001")
    assert resp.status_code == 400
    assert "非一軍" in resp.json()["detail"]


def test_api_game_analysis_rejects_zero_calls(client, monkeypatch):
    def mock_fetch(gid):
        return {"game": {"gameId": gid, "kindCode": "A", "liveLog": []}, "players": {}}

    monkeypatch.setattr(app_module, "fetch_game_detail", mock_fetch)
    resp = client.get("/api/game/2026-A-001")
    assert resp.status_code == 400
    assert "判決數為 0" in resp.json()["detail"]


def test_batch_collect_skips_non_tier1_and_zero_calls(client, monkeypatch):
    def mock_schedule(date_str, kind_code="A"):
        return [
            {"game_id": "2026-B-001", "kind_code": "B", "has_trackman": True, "status": "FINISHED"},
            {"game_id": "2026-A-002", "kind_code": "A", "has_trackman": True, "status": "FINISHED"},
            {"game_id": "2026-A-003", "kind_code": "A", "has_trackman": True, "status": "FINISHED"},
        ]

    def mock_detail(gid):
        if gid == "2026-A-002":
            return {"game": {"gameId": gid, "kindCode": "A", "liveLog": []}, "players": {}}
        elif gid == "2026-A-003":
            return {
                "game": {
                    "gameId": gid,
                    "kindCode": "A",
                    "liveLog": [
                        {
                            "inningSeq": 1,
                            "visitingHomeType": 1,
                            "pitchCnt": 1,
                            "ballCnt": 1,
                            "strikeCnt": 0,
                            "content": "壞球",
                            "trackman": {
                                "play": {"pitchTag": {"pitchCall": "BallCalled"}},
                                "pitch": {
                                    "location": {"zoneTime": 0.4, "plateLocSide": 0.5, "plateLocHeight": 0.5},
                                    "flight": {"polyFit": {"pitchTrajectory": {
                                        "x": [16.0, -40.0, 0.0], "y": [0.5, 0.0, 0.0], "z": [0.0, 0.0, 0.0],
                                    }}},
                                },
                            },
                        }
                    ],
                },
                "players": {},
            }
        return {"game": {"gameId": gid, "kindCode": "B", "liveLog": []}, "players": {}}

    monkeypatch.setattr(app_module, "fetch_schedule_by_date", mock_schedule)
    monkeypatch.setattr(app_module, "fetch_game_detail", mock_detail)

    resp = client.post("/api/batch-collect?date=2026-08-30")
    assert resp.status_code == 200
    results = resp.json()["processed"]

    assert len(results) == 3
    # 2026-B-001: skipped non-tier-1
    assert results[0]["game_id"] == "2026-B-001"
    assert results[0]["status"] == "skipped"
    assert "非一軍" in results[0]["reason"]

    # 2026-A-002: skipped 0 called pitches
    assert results[1]["game_id"] == "2026-A-002"
    assert results[1]["status"] == "skipped"
    assert "判決數為 0" in results[1]["reason"]

    # 2026-A-003: success
    assert results[2]["game_id"] == "2026-A-003"
    assert results[2]["status"] == "success"


@pytest.fixture
def live_game():
    return {
        "gameId": "2026-A-1",
        "gameSno": 1,
        "kindCode": "A",
        "preExeDate": "2026-10-11T17:05:00",
        "gameStatus": "START",
        "home": {"score": 1},
        "liveLog": [{
            "inningSeq": 1,
            "visitingHomeType": 1,
            "pitchCnt": 1,
            "content": "壞球",
            "trackman": {
                "play": {"pitchTag": {"pitchCall": "BallCalled"}},
                "pitch": {
                    "location": {"zoneTime": 0.4, "plateLocSide": 0.5, "plateLocHeight": 0.5},
                    "flight": {"polyFit": {"pitchTrajectory": {
                        "x": [16.0, -40.0, 0.0], "y": [0.5, 0.0, 0.0], "z": [0.0, 0.0, 0.0],
                    }}},
                },
            },
        }],
    }


@pytest.mark.parametrize("kind_code", ["A", "G", "E", "C"])
@pytest.mark.parametrize("status", ["START", "FINISHED"])
def test_batch_collect_includes_live_and_finished_games(client, monkeypatch, live_game, kind_code, status):
    gid = f"2026-{kind_code}-1"
    live_game.update(gameId=gid, kindCode=kind_code, gameStatus=status)
    monkeypatch.setattr(app_module, "fetch_schedule_by_date", lambda date, kind: [
        {"game_id": gid, "kind_code": kind_code, "has_trackman": True, "status": status},
    ])
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda game_id: {"game": live_game, "players": {}})

    response = client.post(f"/api/batch-collect?date=2026-10-11&kind_code={kind_code}")

    assert response.status_code == 200
    assert response.json()["processed"] == [{"game_id": gid, "status": "success"}]
    cached = db_module.get_game(gid)
    assert cached["game_info"]["status"] == status
    assert cached["umpire_metrics"]["total_called_pitches"] == 1


@pytest.mark.parametrize(("status", "has_trackman"), [
    ("NOTSTART", True), ("DELAYED", True), (None, True), ("START", False), ("FINISHED", False),
])
def test_batch_collect_skips_unavailable_games(client, monkeypatch, status, has_trackman):
    monkeypatch.setattr(app_module, "fetch_schedule_by_date", lambda date, kind: [
        {"game_id": "2026-A-1", "kind_code": "A", "has_trackman": has_trackman, "status": status},
    ])

    response = client.post("/api/batch-collect?date=2026-10-11")

    assert response.status_code == 200
    assert response.json()["processed"][0]["status"] == "skipped"
    assert db_module.get_game("2026-A-1") is None


def test_live_game_queries_refresh_until_finished(client, monkeypatch, live_game):
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda gid: {"game": live_game, "players": {}})
    first = client.get("/api/game/2026-A-1")
    assert first.status_code == 200
    assert first.json()["game_info"]["status"] == "START"

    live_game["liveLog"].append({**deepcopy(live_game["liveLog"][0]), "pitchCnt": 2})
    live_game["home"]["score"] = 2
    second = client.get("/api/game/2026-A-1")
    assert second.status_code == 200
    assert second.json()["game_info"]["home_score"] == 2
    assert second.json()["umpire_metrics"]["total_called_pitches"] == 2

    live_game["gameStatus"] = "FINISHED"
    finished = client.get("/api/game/2026-A-1")
    assert finished.status_code == 200
    assert finished.json()["game_info"]["status"] == "FINISHED"
    assert db_module.get_game("2026-A-1") == finished.json()

    def unavailable(gid):
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(app_module, "fetch_game_detail", unavailable)
    assert client.get("/api/game/2026-A-1").json() == finished.json()


def test_legacy_cache_without_status_remains_readable(client, monkeypatch, live_game):
    cached = app_module.analyze_game(live_game)
    cached["game_info"].pop("status", None)
    db_module.save_game("2026-A-1", cached)

    def unavailable(gid):
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(app_module, "fetch_game_detail", unavailable)
    response = client.get("/api/game/2026-A-1")
    assert response.status_code == 200
    assert response.json() == cached


def test_live_refresh_without_called_pitches_preserves_cache(client, monkeypatch, live_game):
    cached = app_module.analyze_game(live_game)
    cached["game_info"]["status"] = "START"
    db_module.save_game("2026-A-1", cached)
    live_game["liveLog"] = []
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda gid: {"game": live_game, "players": {}})

    response = client.get("/api/game/2026-A-1")

    assert response.status_code == 200
    assert response.json()["game_info"] == cached["game_info"]
    assert "上次" in response.json()["refresh_warning"]
    assert "非完整完賽結果" in response.json()["refresh_warning"]
    assert db_module.get_game("2026-A-1") == cached


def test_finished_game_without_trackman_retries_until_full_data_arrives(client, monkeypatch, live_game):
    cached = app_module.analyze_game(live_game)
    db_module.save_game("2026-A-1", cached)
    tracked_pitch = deepcopy(live_game["liveLog"][0])
    live_game["gameStatus"] = "FINISHED"
    live_game["liveLog"][0]["trackman"] = None
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda gid: {"game": live_game, "players": {}})

    pending = client.get("/api/game/2026-A-1")
    assert pending.status_code == 200
    assert pending.json()["game_info"]["status"] == "START"
    assert pending.json()["umpire_metrics"]["total_called_pitches"] == 1
    assert "refresh_warning" in pending.json()
    assert db_module.get_game("2026-A-1") == cached

    live_game["liveLog"] = [tracked_pitch, {**deepcopy(tracked_pitch), "pitchCnt": 2}]
    completed = client.get("/api/game/2026-A-1")
    assert completed.status_code == 200
    assert completed.json()["game_info"]["status"] == "FINISHED"
    assert completed.json()["umpire_metrics"]["total_called_pitches"] == 2
    assert "refresh_warning" not in completed.json()
    assert db_module.get_game("2026-A-1") == completed.json()


def test_force_refresh_without_trackman_still_reports_unavailable_data(client, monkeypatch, live_game):
    cached = app_module.analyze_game(live_game)
    db_module.save_game("2026-A-1", cached)
    live_game["gameStatus"] = "FINISHED"
    live_game["liveLog"][0]["trackman"] = None
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda gid: {"game": live_game, "players": {}})

    response = client.get("/api/game/2026-A-1?force_refresh=true")

    assert response.status_code == 400
    assert "Trackman" in response.json()["detail"]
    assert db_module.get_game("2026-A-1") == cached


@pytest.mark.parametrize(("kind_code", "total_calls"), [("B", 1), ("A", 0)])
def test_unavailable_trackman_does_not_return_invalid_cache(client, monkeypatch, live_game, kind_code, total_calls):
    cached = app_module.analyze_game(live_game)
    cached["game_info"]["kind_code"] = kind_code
    cached["umpire_metrics"]["total_called_pitches"] = total_calls
    monkeypatch.setattr(db_module, "get_game", lambda gid: cached)
    live_game["liveLog"][0]["trackman"] = None
    monkeypatch.setattr(app_module, "fetch_game_detail", lambda gid: {"game": live_game, "players": {}})

    response = client.get("/api/game/2026-A-1")

    assert response.status_code == 400
    assert "Trackman" in response.json()["detail"]
