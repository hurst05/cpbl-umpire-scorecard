import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
from app import app
from stats import calculate_season_stats, format_duration

client = TestClient(app)


def test_format_duration():
    assert format_duration(None) == "無資料"
    assert format_duration(0) == "無資料"
    assert format_duration(45) == "45分"
    assert format_duration(60) == "1小時 0分"
    assert format_duration(176.4) == "2小時 56分"


def test_calculate_season_stats_empty():
    res = calculate_season_stats([], "2026")
    assert res["total_games"] == 0
    assert res["duration"]["formatted_avg"] == "無資料"
    assert res["scores"]["avg_margin"] == 0.0
    assert res["scores"]["avg_winner_score"] == 0.0


def test_calculate_season_stats_metrics():
    dummy_games = [
        {
            "game_id": "2026-A-1",
            "game_sno": 1,
            "game_date": "2026-04-01",
            "field": "大巨蛋",
            "visiting_team": "中信兄弟",
            "home_team": "樂天桃猿",
            "visiting_score": 2,
            "home_score": 5,
            "hp_umpire": "張展榮",
            "overall_acc": 92.0,
            "ball_acc": 90.0,
            "strike_acc": 94.0,
            "overall_consistency": 86.0,
            "missed_count": 8,
            "game_duration_minutes": 180,
        },
        {
            "game_id": "2026-A-2",
            "game_sno": 2,
            "game_date": "2026-04-02",
            "field": "洲際",
            "visiting_team": "樂天桃猿",
            "home_team": "中信兄弟",
            "visiting_score": 4,
            "home_score": 3,
            "hp_umpire": "張展榮",
            "overall_acc": 90.0,
            "ball_acc": 88.0,
            "strike_acc": 92.0,
            "overall_consistency": 84.0,
            "missed_count": 12,
            "game_duration_minutes": 160,
        },
        {
            "game_id": "2026-A-3",
            "game_sno": 3,
            "game_date": "2026-04-03",
            "field": "大巨蛋",
            "visiting_team": "富邦悍將",
            "home_team": "統一7-ELEVEn獅",
            "visiting_score": 1,
            "home_score": 7,
            "hp_umpire": "楊崇煇",
            "overall_acc": 94.0,
            "ball_acc": 92.0,
            "strike_acc": 96.0,
            "overall_consistency": 90.0,
            "missed_count": 6,
            "game_duration_minutes": 200,
        },
    ]

    stats = calculate_season_stats(dummy_games, 2026)

    # 1. Basic counts & duration
    assert stats["total_games"] == 3
    assert stats["duration"]["valid_games_count"] == 3
    assert stats["duration"]["avg_minutes"] == 180.0
    assert stats["duration"]["formatted_avg"] == "3小時 0分"
    assert stats["duration"]["shortest_game"]["game_id"] == "2026-A-2"
    assert stats["duration"]["longest_game"]["game_id"] == "2026-A-3"

    # 2. Scores calculations
    # Game 1: 5-2 (margin 3, winner 5, loser 2, total 7)
    # Game 2: 4-3 (margin 1, winner 4, loser 3, total 7)
    # Game 3: 7-1 (margin 6, winner 7, loser 1, total 8)
    # Avg margin: (3 + 1 + 6) / 3 = 3.33
    assert stats["scores"]["avg_margin"] == 3.33
    # Avg winner: (5 + 4 + 7) / 3 = 5.33
    assert stats["scores"]["avg_winner_score"] == 5.33
    # Avg loser: (2 + 3 + 1) / 3 = 2.00
    assert stats["scores"]["avg_loser_score"] == 2.00
    # Avg total runs: (7 + 7 + 8) / 3 = 7.33
    assert stats["scores"]["avg_total_runs"] == 7.33
    assert stats["scores"]["total_runs"] == 22
    assert stats["scores"]["one_run_games_count"] == 1
    assert stats["scores"]["blowout_games_count"] == 1

    # 3. Home / Away
    # Home wins: Game 1 (home), Game 3 (home) -> 2 wins
    # Visiting wins: Game 2 (visiting) -> 1 win
    assert stats["home_away"]["home_wins"] == 2
    assert stats["home_away"]["visiting_wins"] == 1
    assert stats["home_away"]["home_win_pct"] == 66.7

    # 4. Umpire Leaderboard & Summary
    assert stats["umpire_summary"]["avg_consistency"] == 86.67
    assert len(stats["umpire_leaderboard"]) == 2
    top_ump = stats["umpire_leaderboard"][0]
    assert top_ump["hp_umpire"] == "張展榮"
    assert top_ump["games"] == 2
    assert top_ump["overall_acc"] == 91.0
    assert top_ump["total_missed"] == 20
    assert top_ump["missed_per_game"] == 10.0
    assert top_ump["consistency"] == 85.0

    # 5. Team Standings
    # 樂天桃猿: Game 1 won (5-2), Game 2 won (4-3) -> 2-0 (1.000)
    # 統一獅: Game 3 won (7-1) -> 1-0 (1.000)
    # 中信兄弟: Game 1 lost, Game 2 lost -> 0-2 (0.000)
    # 富邦悍將: Game 3 lost -> 0-1 (0.000)
    rakuten = next(t for t in stats["team_standings"] if t["team"] == "樂天桃猿")
    assert rakuten["wins"] == 2
    assert rakuten["losses"] == 0
    assert rakuten["win_rate"] == 1.000
    assert rakuten["run_diff"] == (5 + 4) - (2 + 3)  # +4

    # 6. Stadium stats
    dome = next(s for s in stats["stadium_stats"] if s["field"] == "大巨蛋")
    assert dome["games"] == 2
    assert dome["avg_duration_minutes"] == 190.0


def test_api_seasons_and_stats():
    # Test /api/seasons
    res_seasons = client.get("/api/seasons")
    assert res_seasons.status_code == 200
    data_seasons = res_seasons.json()
    assert "seasons" in data_seasons
    assert isinstance(data_seasons["seasons"], list)

    # Test /api/stats/season/2026
    res_stats = client.get("/api/stats/season/2026")
    assert res_stats.status_code == 200
    data_stats = res_stats.json()
    assert "total_games" in data_stats
    assert "duration" in data_stats
    assert "scores" in data_stats
    assert "umpire_leaderboard" in data_stats
    assert "team_standings" in data_stats
    assert "stadium_stats" in data_stats

    # Test /api/games/cached with year
    res_cached = client.get("/api/games/cached?year=2026")
    assert res_cached.status_code == 200
    games = res_cached.json()
    assert isinstance(games, list)
    for g in games:
        assert g["game_date"].startswith("2026")
