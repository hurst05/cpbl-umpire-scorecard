import json
from unittest.mock import MagicMock, patch

from collector import (
    calculate_duration_from_times,
    fetch_game_duration,
    parse_duration_str,
)


def test_parse_duration_str():
    assert parse_duration_str("025600") == 176
    assert parse_duration_str("032300") == 203
    assert parse_duration_str("014000") == 100
    assert parse_duration_str("") is None
    assert parse_duration_str("      ") is None
    assert parse_duration_str(None) is None
    assert parse_duration_str("invalid") is None


def test_calculate_duration_from_times():
    assert calculate_duration_from_times("2026-09-01T18:34:00", "2026-09-01T21:57:00") == 203
    assert calculate_duration_from_times("2026-09-01T18:34:00", "2026-09-01T18:34:00") is None
    assert calculate_duration_from_times("2026-09-01T18:34:00", None) is None
    assert calculate_duration_from_times("invalid", "invalid") is None


def test_fetch_game_duration_matches_exact_sno():
    mock_gd = [
        {"GameSno": 322, "GameDuringTime": "030400", "GameStatus": 3},
        {"GameSno": 323, "GameDuringTime": "025900", "GameStatus": 3},
        {"GameSno": 324, "GameDuringTime": "024000", "GameStatus": 3},
    ]
    mock_payload = {"Success": True, "GameDetailJson": json.dumps(mock_gd)}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("collector.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        dur_322 = fetch_game_duration("2026-A-322")
        assert dur_322 == 184  # 3h 04m

        dur_323 = fetch_game_duration("2026-A-323")
        assert dur_323 == 179  # 2h 59m

        dur_324 = fetch_game_duration("2026-A-324")
        assert dur_324 == 160  # 2h 40m


def test_fetch_game_duration_fallback_and_curt():
    mock_curt = {"GameSno": 301, "GameDuringTime": "032300", "GameStatus": 3}
    mock_payload = {"Success": True, "GameDetailJson": "[]", "CurtGameDetailJson": json.dumps(mock_curt)}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("collector.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        dur = fetch_game_duration("2026-A-301")
        assert dur == 203
