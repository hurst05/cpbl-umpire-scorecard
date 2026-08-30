import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
import export_static  # noqa: E402
from export_static import export_all  # noqa: E402


@pytest.fixture
def mock_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY,
            game_sno INTEGER,
            kind_code TEXT,
            game_date TEXT,
            field TEXT,
            home_team TEXT,
            visiting_team TEXT,
            home_score INTEGER,
            visiting_score INTEGER,
            hp_umpire TEXT,
            overall_acc REAL,
            ball_acc REAL,
            strike_acc REAL,
            missed_count INTEGER,
            data_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    sample_game_data = {
        "game_info": {
            "game_id": "2026-A-295",
            "game_sno": 295,
            "kind_code": "A",
            "date": "2026-08-29",
            "field": "臺北大巨蛋",
            "home_team": "味全龍",
            "visiting_team": "中信兄弟",
            "home_score": 2,
            "visiting_score": 3,
            "hp_umpire": "張展榮",
        },
        "umpire_metrics": {
            "overall_accuracy": 92.5,
            "ball_accuracy": 94.1,
            "strike_accuracy": 89.8,
            "missed_count": 11,
        },
        "plate_appearances": [
            {"pa_index": 1, "inning": 1, "hitter_name": "岳政華", "pitcher_name": "鋼龍", "pitches": []}
        ],
        "all_called_pitches": [],
    }

    cursor.execute(
        """
        INSERT INTO games (
            game_id, game_sno, kind_code, game_date, field,
            home_team, visiting_team, home_score, visiting_score,
            hp_umpire, overall_acc, ball_acc, strike_acc, missed_count,
            data_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            "2026-A-295",
            295,
            "A",
            "2026-08-29",
            "臺北大巨蛋",
            "味全龍",
            "中信兄弟",
            2,
            3,
            "張展榮",
            92.5,
            94.1,
            89.8,
            11,
            json.dumps(sample_game_data, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


def test_export_all_creates_valid_manifest_and_game(mock_db):
    with tempfile.TemporaryDirectory() as out_dir:
        target_dir = os.path.join(out_dir, "data")
        result = export_all(output_dir=target_dir, custom_db_path=mock_db)

        assert result["total_games"] == 1
        assert result["default_game_id"] == "2026-A-295"

        manifest_path = os.path.join(target_dir, "manifest.json")
        assert os.path.exists(manifest_path)

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["schema_version"] == 1
        assert "generated_at" in manifest
        assert manifest["default_game_id"] == "2026-A-295"
        assert len(manifest["games"]) == 1

        game_summary = manifest["games"][0]
        assert game_summary["game_id"] == "2026-A-295"
        assert game_summary["game_sno"] == 295
        assert game_summary["hp_umpire"] == "張展榮"
        assert game_summary["overall_acc"] == 92.5
        assert game_summary["missed_count"] == 11

        game_file_path = os.path.join(target_dir, "games", "2026-A-295.json")
        assert os.path.exists(game_file_path)

        with open(game_file_path, "r", encoding="utf-8") as f:
            game_detail = json.load(f)

        assert "game_info" in game_detail
        assert "umpire_metrics" in game_detail
        assert "plate_appearances" in game_detail
        assert "all_called_pitches" in game_detail


def test_export_empty_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        empty_db = f.name

    conn = sqlite3.connect(empty_db)
    conn.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY,
            game_sno INTEGER,
            kind_code TEXT,
            game_date TEXT,
            field TEXT,
            home_team TEXT,
            visiting_team TEXT,
            home_score INTEGER,
            visiting_score INTEGER,
            hp_umpire TEXT,
            overall_acc REAL,
            ball_acc REAL,
            strike_acc REAL,
            missed_count INTEGER,
            data_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    try:
        with tempfile.TemporaryDirectory() as out_dir:
            target_dir = os.path.join(out_dir, "data")
            result = export_all(output_dir=target_dir, custom_db_path=empty_db)
            assert result["total_games"] == 0
            assert result["default_game_id"] is None

            manifest_path = os.path.join(target_dir, "manifest.json")
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            assert manifest["schema_version"] == 1
            assert manifest["games"] == []
    finally:
        if os.path.exists(empty_db):
            os.remove(empty_db)


def test_export_missing_custom_db_fails():
    with pytest.raises(FileNotFoundError, match="指定的 SQLite 資料庫不存在"):
        export_all(custom_db_path="non_existent_path_12345.db")


def test_export_invalid_game_ids_rejected():
    invalid_ids = ["../../outside", "2026-B-123", "2025-A-123", "2026-A-0", "invalid_id"]
    for bad_id in invalid_ids:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            bad_db = f.name
        conn = sqlite3.connect(bad_db)
        conn.execute("""
            CREATE TABLE games (
                game_id TEXT PRIMARY KEY, game_sno INTEGER, kind_code TEXT, game_date TEXT, field TEXT,
                home_team TEXT, visiting_team TEXT, home_score INTEGER, visiting_score INTEGER,
                hp_umpire TEXT, overall_acc REAL, ball_acc REAL, strike_acc REAL, missed_count INTEGER,
                data_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            """
            INSERT INTO games (game_id, game_sno, game_date, data_json)
            VALUES (?, 1, '2026-08-30', '{"game_info":{},"umpire_metrics":{},"plate_appearances":[],"all_called_pitches":[]}')
        """,
            (bad_id,),
        )
        conn.commit()
        conn.close()

        try:
            with tempfile.TemporaryDirectory() as out_dir:
                target_dir = os.path.join(out_dir, "data")
                with pytest.raises(ValueError, match="無效的賽事 ID 格式"):
                    export_all(output_dir=target_dir, custom_db_path=bad_db)
                # Ensure no outside files were written
                outside_file = Path(out_dir) / "outside.json"
                assert not outside_file.exists()
        finally:
            if os.path.exists(bad_db):
                os.remove(bad_db)


def test_export_valid_single_game():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        valid_db = f.name
    conn = sqlite3.connect(valid_db)
    conn.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY, game_sno INTEGER, kind_code TEXT, game_date TEXT, field TEXT,
            home_team TEXT, visiting_team TEXT, home_score INTEGER, visiting_score INTEGER,
            hp_umpire TEXT, overall_acc REAL, ball_acc REAL, strike_acc REAL, missed_count INTEGER,
            data_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO games (game_id, game_sno, game_date, data_json)
        VALUES ('2026-A-123', 123, '2026-08-30', '{"game_info":{},"umpire_metrics":{},"plate_appearances":[],"all_called_pitches":[]}')
    """)
    conn.commit()
    conn.close()

    try:
        with tempfile.TemporaryDirectory() as out_dir:
            target_dir = os.path.join(out_dir, "data")
            res = export_all(output_dir=target_dir, custom_db_path=valid_db)
            assert res["total_games"] == 1
            assert res["default_game_id"] == "2026-A-123"
            assert (Path(target_dir) / "games" / "2026-A-123.json").exists()
    finally:
        if os.path.exists(valid_db):
            os.remove(valid_db)


def test_export_missing_data_json_fails():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        bad_db = f.name

    conn = sqlite3.connect(bad_db)
    conn.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY, game_sno INTEGER, kind_code TEXT, game_date TEXT, field TEXT,
            home_team TEXT, visiting_team TEXT, home_score INTEGER, visiting_score INTEGER,
            hp_umpire TEXT, overall_acc REAL, ball_acc REAL, strike_acc REAL, missed_count INTEGER,
            data_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO games (game_id, game_sno, game_date, data_json)
        VALUES ('2026-A-100', 100, '2026-08-30', NULL)
    """)
    conn.commit()
    conn.close()

    try:
        with tempfile.TemporaryDirectory() as out_dir:
            with pytest.raises(ValueError, match="缺少 data_json"):
                export_all(output_dir=os.path.join(out_dir, "data"), custom_db_path=bad_db)
    finally:
        if os.path.exists(bad_db):
            os.remove(bad_db)


def test_export_corrupted_data_json_fails():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        bad_db = f.name

    conn = sqlite3.connect(bad_db)
    conn.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY, game_sno INTEGER, kind_code TEXT, game_date TEXT, field TEXT,
            home_team TEXT, visiting_team TEXT, home_score INTEGER, visiting_score INTEGER,
            hp_umpire TEXT, overall_acc REAL, ball_acc REAL, strike_acc REAL, missed_count INTEGER,
            data_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO games (game_id, game_sno, game_date, data_json)
        VALUES ('2026-A-100', 100, '2026-08-30', '{invalid_json')
    """)
    conn.commit()
    conn.close()

    try:
        with tempfile.TemporaryDirectory() as out_dir:
            with pytest.raises(ValueError, match="損壞或包含無效格式"):
                export_all(output_dir=os.path.join(out_dir, "data"), custom_db_path=bad_db)
    finally:
        if os.path.exists(bad_db):
            os.remove(bad_db)


def test_export_staging_atomic_behavior_on_failure(mock_db):
    with tempfile.TemporaryDirectory() as out_dir:
        target_dir = os.path.join(out_dir, "data")
        # Export valid initial version
        export_all(output_dir=target_dir, custom_db_path=mock_db)
        manifest_before = Path(target_dir, "manifest.json").read_text(encoding="utf-8")

        # Now corrupt the database
        conn = sqlite3.connect(mock_db)
        conn.execute("UPDATE games SET data_json = '{corrupted' WHERE game_id = '2026-A-295'")
        conn.commit()
        conn.close()

        # Second export must fail and leave existing target_dir intact
        with pytest.raises(ValueError, match="損壞或包含無效格式"):
            export_all(output_dir=target_dir, custom_db_path=mock_db)

        manifest_after = Path(target_dir, "manifest.json").read_text(encoding="utf-8")
        assert manifest_before == manifest_after


def test_export_rollback_on_final_verification_failure(mock_db, monkeypatch):
    with tempfile.TemporaryDirectory() as out_dir:
        target_dir = os.path.join(out_dir, "data")
        # Export initial valid version
        export_all(output_dir=target_dir, custom_db_path=mock_db)
        manifest_before = Path(target_dir, "manifest.json").read_text(encoding="utf-8")

        # Monkeypatch verify_static_snapshot to fail on the final output_path call
        original_verify = export_static.verify_static_snapshot
        call_count = 0

        def failing_verify(path):
            nonlocal call_count
            call_count += 1
            if call_count > 1:  # Fail on second call (output_path verification)
                raise export_static.verify_static.VerificationError("模擬最終快照驗證失敗")
            return original_verify(path)

        monkeypatch.setattr(export_static, "verify_static_snapshot", failing_verify)

        with pytest.raises(RuntimeError, match="快照替換失敗，已還原上一份有效版本"):
            export_all(output_dir=target_dir, custom_db_path=mock_db)

        manifest_after = Path(target_dir, "manifest.json").read_text(encoding="utf-8")
        assert manifest_before == manifest_after


def test_export_skips_zero_called_pitches_game():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY, game_sno INTEGER, kind_code TEXT, game_date TEXT, field TEXT,
            home_team TEXT, visiting_team TEXT, home_score INTEGER, visiting_score INTEGER,
            hp_umpire TEXT, overall_acc REAL, ball_acc REAL, strike_acc REAL, missed_count INTEGER,
            data_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 1. Valid game with calls > 0
    conn.execute(
        """
        INSERT INTO games (game_id, game_sno, kind_code, game_date, data_json)
        VALUES ('2026-A-101', 101, 'A', '2026-08-30',
                '{"game_info":{"game_id":"2026-A-101","game_sno":101},"umpire_metrics":{"total_called_pitches":120},"plate_appearances":[],"all_called_pitches":[]}')
    """
    )
    # 2. Game with total_called_pitches == 0 (should be skipped)
    conn.execute(
        """
        INSERT INTO games (game_id, game_sno, kind_code, game_date, data_json)
        VALUES ('2026-A-102', 102, 'A', '2026-08-30',
                '{"game_info":{"game_id":"2026-A-102","game_sno":102},"umpire_metrics":{"total_called_pitches":0},"plate_appearances":[],"all_called_pitches":[]}')
    """
    )
    conn.commit()
    conn.close()

    try:
        with tempfile.TemporaryDirectory() as out_dir:
            target_dir = os.path.join(out_dir, "data")
            res = export_all(output_dir=target_dir, custom_db_path=db_path)
            assert res["total_games"] == 1
            assert res["default_game_id"] == "2026-A-101"
            assert (Path(target_dir) / "games" / "2026-A-101.json").exists()
            assert not (Path(target_dir) / "games" / "2026-A-102.json").exists()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

