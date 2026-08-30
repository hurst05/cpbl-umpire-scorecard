from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))
from verify_static import VerificationError, verify_static_snapshot  # noqa: E402


def _create_minimal_valid_snapshot(target_dir: Path, num_games: int = 1) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    games_dir = target_dir / "games"
    games_dir.mkdir(exist_ok=True)

    games_list = []
    for i in range(num_games, 0, -1):
        gid = f"2026-A-{200 + i}"
        summary = {
            "game_id": gid,
            "game_sno": 200 + i,
            "game_date": "2026-08-29",
            "field": "臺北大巨蛋",
            "visiting_team": "中信兄弟",
            "home_team": "味全龍",
            "visiting_score": 3,
            "home_score": 2,
            "hp_umpire": "張展榮",
            "overall_acc": 92.5,
            "ball_acc": 94.1,
            "strike_acc": 89.8,
            "missed_count": 11,
        }
        games_list.append(summary)

        detail = {
            "game_info": {"game_id": gid, "game_sno": 200 + i},
            "umpire_metrics": {"overall_accuracy": 92.5},
            "plate_appearances": [],
            "all_called_pitches": [],
        }
        (games_dir / f"{gid}.json").write_text(json.dumps(detail, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).astimezone().isoformat(),
        "default_game_id": games_list[0]["game_id"] if games_list else None,
        "games": games_list,
    }
    (target_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return target_dir


def test_verify_valid_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=2)
        res = verify_static_snapshot(snap_path)
        assert res["status"] == "valid"
        assert res["total_games"] == 2
        assert res["default_game_id"] == "2026-A-202"


def test_verify_missing_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = Path(tmp) / "data"
        snap_path.mkdir()
        with pytest.raises(VerificationError, match="缺少必要索引檔案"):
            verify_static_snapshot(snap_path)


def test_verify_invalid_schema_version():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data")
        manifest_path = snap_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = 2
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with pytest.raises(VerificationError, match="schema_version 必須為整數 1"):
            verify_static_snapshot(snap_path)


def test_verify_missing_timezone_in_generated_at():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data")
        manifest_path = snap_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["generated_at"] = "2026-08-30T12:00:00"  # No TZ
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with pytest.raises(VerificationError, match="必須包含時區資訊"):
            verify_static_snapshot(snap_path)


def test_verify_games_sorting_error():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=2)
        manifest_path = snap_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Reverse order so it violates DESC
        manifest["games"].reverse()
        manifest["default_game_id"] = manifest["games"][0]["game_id"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with pytest.raises(VerificationError, match="未按.*排序"):
            verify_static_snapshot(snap_path)


def test_verify_missing_game_file():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=1)
        (snap_path / "games" / "2026-A-201.json").unlink()

        with pytest.raises(VerificationError, match="缺少 manifest 所對應的賽事詳細檔案"):
            verify_static_snapshot(snap_path)


def test_verify_orphan_game_file():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=1)
        orphan = snap_path / "games" / "2026-A-999.json"
        orphan.write_text("{}", encoding="utf-8")

        with pytest.raises(VerificationError, match="孤兒檔案"):
            verify_static_snapshot(snap_path)


def test_verify_missing_top_keys_in_detail():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=1)
        detail_path = snap_path / "games" / "2026-A-201.json"
        detail = {"game_info": {}}  # Missing other 3 keys
        detail_path.write_text(json.dumps(detail), encoding="utf-8")

        with pytest.raises(VerificationError, match="缺少必要頂層欄位"):
            verify_static_snapshot(snap_path)


def test_verify_forbidden_files_wal_shm_env():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=1)
        (snap_path / "database.db-wal").write_text("dummy", encoding="utf-8")
        with pytest.raises(VerificationError, match="包含不允許的敏感或暫存檔案"):
            verify_static_snapshot(snap_path)
        (snap_path / "database.db-wal").unlink()

        (snap_path / "DATABASE.DB-SHM").write_text("dummy", encoding="utf-8")
        with pytest.raises(VerificationError, match="包含不允許的敏感或暫存檔案"):
            verify_static_snapshot(snap_path)
        (snap_path / "DATABASE.DB-SHM").unlink()

        (snap_path / ".env.local").write_text("dummy", encoding="utf-8")
        with pytest.raises(VerificationError, match="包含不允許的敏感或暫存檔案"):
            verify_static_snapshot(snap_path)


def test_verify_invalid_game_id_format():
    invalid_ids = ["2026-B-100", "2025-A-100", "2026-A-0", "invalid_id", "2026-A-01"]
    for bad_id in invalid_ids:
        with tempfile.TemporaryDirectory() as tmp:
            snap_path = Path(tmp) / "data"
            snap_path.mkdir(parents=True, exist_ok=True)
            (snap_path / "games").mkdir()
            detail = {
                "game_info": {},
                "umpire_metrics": {},
                "plate_appearances": [],
                "all_called_pitches": [],
            }
            (snap_path / "games" / f"{bad_id}.json").write_text(json.dumps(detail), encoding="utf-8")

            manifest = {
                "schema_version": 1,
                "generated_at": datetime.now(UTC).astimezone().isoformat(),
                "default_game_id": bad_id,
                "games": [
                    {
                        "game_id": bad_id,
                        "game_sno": 100,
                        "game_date": "2026-08-29",
                        "field": "臺北大巨蛋",
                        "visiting_team": "中信兄弟",
                        "home_team": "味全龍",
                        "visiting_score": 3,
                        "home_score": 2,
                        "hp_umpire": "張展榮",
                        "overall_acc": 92.5,
                        "ball_acc": 94.1,
                        "strike_acc": 89.8,
                        "missed_count": 11,
                    }
                ],
            }
            (snap_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            with pytest.raises(VerificationError, match="game_id 格式無效"):
                verify_static_snapshot(snap_path)


def test_verify_empty_games_valid():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = Path(tmp) / "data"
        snap_path.mkdir()
        manifest = {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).astimezone().isoformat(),
            "default_game_id": None,
            "games": [],
        }
        (snap_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        res = verify_static_snapshot(snap_path)
        assert res["status"] == "valid"
        assert res["total_games"] == 0
        assert res["default_game_id"] is None


def test_verify_cli_exit_code():
    with tempfile.TemporaryDirectory() as tmp:
        snap_path = _create_minimal_valid_snapshot(Path(tmp) / "data", num_games=1)
        cmd = [sys.executable, "-m", "server.verify_static", "--input", str(snap_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0
        assert "[Verify OK]" in proc.stdout

        # Break it
        (snap_path / "manifest.json").unlink()
        proc_fail = subprocess.run(cmd, capture_output=True, text=True)
        assert proc_fail.returncode != 0
        assert "[Verify ERROR]" in proc_fail.stderr
