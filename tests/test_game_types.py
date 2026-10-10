import json

import app as app_module
import collector
import db
import pytest
from export_static import export_all
from fastapi.testclient import TestClient
from stats import calculate_season_stats


def game_analysis(kind_code, score=3):
    return {
        "game_info": {
            "game_id": f"2026-{kind_code}-1",
            "game_sno": 1,
            "kind_code": kind_code,
            "date": "2026-10-10",
            "home_team": "主隊",
            "visiting_team": "客隊",
            "home_score": score,
            "visiting_score": 0,
            "hp_umpire": kind_code,
            "field": kind_code,
            "game_duration_minutes": score * 10,
        },
        "umpire_metrics": {
            "total_called_pitches": 1,
            "overall_accuracy": score * 10,
            "ball_accuracy": score * 10,
            "strike_accuracy": score * 10,
            "missed_count": score,
        },
        "plate_appearances": [],
        "all_called_pitches": [],
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "games.db"))
    db.init_db()
    return TestClient(app_module.app)


@pytest.mark.parametrize("kind_code", ["A", "G", "E", "C"])
def test_query_sno_accepts_supported_game_types(client, monkeypatch, kind_code):
    analysis = game_analysis(kind_code)
    monkeypatch.setattr(
        app_module, "fetch_game_detail", lambda gid: {"game": {"gameId": gid, "kindCode": kind_code}, "players": {}}
    )
    monkeypatch.setattr(app_module, "analyze_game", lambda game, players: analysis)
    response = client.get(f"/api/game/sno/1?kind_code={kind_code}")
    assert response.status_code == 200
    assert response.json()["game_info"]["game_id"] == f"2026-{kind_code}-1"
    assert db.get_game(f"2026-{kind_code}-1") == analysis


def test_cached_lists_and_all_year_stats_stay_separate(client):
    for kind_code, score in [("A", 3), ("G", 4), ("E", 5), ("C", 6)]:
        db.save_game(f"2026-{kind_code}-1", game_analysis(kind_code, score))

    assert [g["game_id"] for g in client.get("/api/games/cached").json()] == ["2026-A-1"]
    for kind_code, score in [("A", 3), ("G", 4), ("E", 5), ("C", 6)]:
        games = client.get(f"/api/games/cached?kind_code={kind_code}").json()
        assert [g["game_id"] for g in games] == [f"2026-{kind_code}-1"]
        for year in ["2026", "all"]:
            stats = client.get(f"/api/stats/season/{year}?kind_code={kind_code}").json()
            assert stats["total_games"] == 1
            assert stats["scores"]["total_runs"] == score
            assert stats["duration"]["avg_minutes"] == score * 10
            assert stats["umpire_leaderboard"][0]["hp_umpire"] == kind_code
            assert stats["team_standings"][0]["runs_scored"] == score
            assert stats["stadium_stats"][0]["field"] == kind_code
        assert client.get(f"/api/seasons?kind_code={kind_code}").json()["seasons"] == [2026]


@pytest.mark.parametrize("kind_code", ["G", "E", "C"])
def test_schedule_selects_game_type_and_requested_month(monkeypatch, kind_code):
    games = [
        {"GameId": f"2026-{kind}-1", "KindCode": kind, "PreExeDate": "2026-10-10T17:05:00"}
        for kind in ["A", "G", "E", "C", "D", "F"]
    ]
    games.append({"GameId": f"2026-{kind_code}-2", "KindCode": kind_code, "PreExeDate": "2026-10-11T17:05:00"})
    payload = {"Data": {"Games": games}}

    def fetch(url):
        assert f"kindCode={kind_code}" in url
        assert "year=2026" in url and "month=10" in url
        return json.dumps(payload)

    monkeypatch.setattr(collector, "fetch_cpbl_url", fetch)
    schedule = collector.fetch_schedule_by_date("2026-10-10", kind_code)
    assert [g["game_id"] for g in schedule] == [f"2026-{kind_code}-1"]


@pytest.mark.parametrize("kind_code", ["A", "G", "E", "C"])
def test_statistics_filter_mixed_types_including_legacy_summaries(kind_code):
    games = [
        {"game_id": f"2026-{kind}-1", "home_score": score, "visiting_score": 0}
        for kind, score in [("A", 3), ("G", 4), ("E", 5), ("C", 6)]
    ]
    result = calculate_season_stats(games, "全部", kind_code)
    assert result["kind_code"] == kind_code
    assert result["total_games"] == 1
    assert result["scores"]["total_runs"] == {"A": 3, "G": 4, "E": 5, "C": 6}[kind_code]


@pytest.mark.parametrize("endpoint", ["/api/seasons", "/api/games/cached", "/api/stats/season/all", "/api/game/sno/1"])
def test_type_filters_reject_unsupported_codes(client, endpoint):
    assert client.get(f"{endpoint}?kind_code=D").status_code == 422


@pytest.mark.parametrize("kind_code", ["G", "E", "C"])
def test_batch_collect_selected_type(client, monkeypatch, kind_code):
    def schedule(date, selected_kind):
        assert selected_kind == kind_code
        return [{"game_id": f"2026-{kind_code}-1", "kind_code": kind_code, "has_trackman": True, "status": "FINISHED"}]

    monkeypatch.setattr(app_module, "fetch_schedule_by_date", schedule)
    monkeypatch.setattr(
        app_module, "fetch_game_detail", lambda gid: {"game": {"gameId": gid, "kindCode": kind_code}, "players": {}}
    )
    monkeypatch.setattr(app_module, "analyze_game", lambda game, players: game_analysis(kind_code))
    response = client.post(f"/api/batch-collect?date=2026-10-10&kind_code={kind_code}")
    assert response.status_code == 200
    assert response.json()["processed"][0]["status"] == "success"
    assert db.list_cached_games() == []


def test_static_export_keeps_statistics_separate_with_same_date_and_sno(client, tmp_path):
    for kind_code, score in [("A", 3), ("G", 4), ("E", 5), ("C", 6)]:
        db.save_game(f"2026-{kind_code}-1", game_analysis(kind_code, score))
    output = tmp_path / "snapshot"
    result = export_all(str(output), db.DB_PATH)
    assert result["total_games"] == 4
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert {g["kind_code"] for g in manifest["games"]} == {"A", "G", "E", "C"}
    for kind_code, score in [("A", 3), ("G", 4), ("E", 5), ("C", 6)]:
        stats_dir = output / "stats" if kind_code == "A" else output / "stats" / kind_code
        for year in ["2026", "all"]:
            stats = json.loads((stats_dir / f"{year}.json").read_text(encoding="utf-8"))
            assert stats["kind_code"] == kind_code
            assert stats["total_games"] == 1
            assert stats["scores"]["total_runs"] == score
        assert (output / "games" / f"2026-{kind_code}-1.json").is_file()
