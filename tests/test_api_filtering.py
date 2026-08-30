import json
import os
import sys
import tempfile

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
    inner_json = json.dumps({
        "state": {
            "data": {
                "data": {
                    "games": [
                        {"gameId": "2026-A-001", "gameSno": 1, "kindCode": "A", "preExeDate": "2026-08-30T17:05:00"},
                        {"gameId": "2026-B-001", "gameSno": 1, "kindCode": "B", "preExeDate": "2026-08-30T13:00:00"},
                        {"gameId": "2026-D-001", "gameSno": 1, "kindCode": "D", "preExeDate": "2026-08-30T14:00:00"},
                    ]
                }
            }
        },
        "queryKey": ["game", "list", "2026-08-30"]
    })
    escaped_json = inner_json.replace('"', '\\"')
    sample_rsc = f'self.__next_f.push([1,"{escaped_json}"]);'

    monkeypatch.setattr(collector, "fetch_cpbl_url", lambda url: sample_rsc)
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
    def mock_schedule(date_str):
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
                                "pitch": {"location": {"plateLocSide": 0.5, "plateLocHeight": 0.5}},
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
