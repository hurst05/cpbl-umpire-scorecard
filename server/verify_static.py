import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

GAME_ID_PATTERN = re.compile(r"^2026-A-[1-9]\d*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

FORBIDDEN_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".wal", ".shm", ".py", ".env", ".key", ".pem"}


class VerificationError(Exception):
    pass


def _parse_json_strict(file_path: Path) -> dict:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise VerificationError(f"檔案非有效 UTF-8 編碼: {file_path} ({e})") from e

    try:
        # standard loads parses null, but parses NaN/Infinity unless we pass parse_constant
        def reject_constant(c):
            raise ValueError(f"不允許的數值常數: {c}")

        data = json.loads(raw_text, parse_constant=reject_constant)
        return data
    except Exception as e:
        raise VerificationError(f"JSON 解析失敗: {file_path} - {e}") from e


def verify_static_snapshot(snapshot_dir: str | Path) -> dict:
    snapshot_path = Path(snapshot_dir).resolve()
    if not snapshot_path.exists() or not snapshot_path.is_dir():
        raise VerificationError(f"快照目錄不存在或非目錄: {snapshot_path}")

    # Check for forbidden files in snapshot tree (case-insensitive)
    for root, _, files in os.walk(snapshot_path):
        for f in files:
            f_lower = f.lower()
            ext = os.path.splitext(f_lower)[1]
            if (
                ext in FORBIDDEN_EXTENSIONS
                or f_lower.endswith("-wal")
                or f_lower.endswith("-shm")
                or f_lower.startswith(".env")
            ):
                raise VerificationError(f"快照目錄包含不允許的敏感或暫存檔案: {os.path.join(root, f)}")

    manifest_path = snapshot_path / "manifest.json"
    if not manifest_path.exists():
        raise VerificationError(f"缺少必要索引檔案: {manifest_path}")

    manifest = _parse_json_strict(manifest_path)
    if not isinstance(manifest, dict):
        raise VerificationError("manifest.json 根節點必須是 JSON 物件")

    schema_version = manifest.get("schema_version")
    if schema_version != 1 or not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise VerificationError(f"manifest.json schema_version 必須為整數 1，實際為: {schema_version}")

    generated_at = manifest.get("generated_at")
    if not isinstance(generated_at, str):
        raise VerificationError("manifest.json generated_at 必須為字串")
    try:
        dt = datetime.fromisoformat(generated_at)
        if dt.tzinfo is None:
            raise VerificationError("manifest.json generated_at 必須包含時區資訊")
    except Exception as e:
        raise VerificationError(f"manifest.json generated_at 非有效 ISO 8601 時間格式: {generated_at} ({e})") from e

    games = manifest.get("games")
    if not isinstance(games, list):
        raise VerificationError("manifest.json games 必須為陣列")

    default_game_id = manifest.get("default_game_id")

    if not games:
        if default_game_id is not None:
            raise VerificationError(f"當 games 為空時，default_game_id 必須為 null，實際為: {default_game_id}")
    else:
        if default_game_id != games[0].get("game_id"):
            raise VerificationError(
                f"default_game_id ({default_game_id}) 必須與首筆賽事 ID ({games[0].get('game_id')}) 一致"
            )

    seen_ids = set()
    prev_sort_key = None
    games_dir = snapshot_path / "games"

    expected_summary_keys = {
        "game_id",
        "game_sno",
        "game_date",
        "field",
        "visiting_team",
        "home_team",
        "visiting_score",
        "home_score",
        "hp_umpire",
        "overall_acc",
        "ball_acc",
        "strike_acc",
        "missed_count",
    }

    for idx, g in enumerate(games):
        if not isinstance(g, dict):
            raise VerificationError(f"manifest.json games[{idx}] 必須為物件")

        missing_keys = expected_summary_keys - set(g.keys())
        if missing_keys:
            raise VerificationError(f"manifest.json games[{idx}] 缺少必要欄位: {missing_keys}")

        gid = g["game_id"]
        if not isinstance(gid, str) or not GAME_ID_PATTERN.match(gid):
            raise VerificationError(f"games[{idx}].game_id 格式無效: {gid} (預期如 2026-A-295)")

        if gid in seen_ids:
            raise VerificationError(f"manifest.json 存在重複的 game_id: {gid}")
        seen_ids.add(gid)

        sno = g["game_sno"]
        if not isinstance(sno, int) or isinstance(sno, bool) or sno <= 0:
            raise VerificationError(f"games[{idx}].game_sno 必須為正整數: {sno}")

        gdate = g["game_date"]
        if not isinstance(gdate, str) or not DATE_PATTERN.match(gdate):
            raise VerificationError(f"games[{idx}].game_date 格式無效: {gdate} (預期 YYYY-MM-DD)")

        for score_key in ("visiting_score", "home_score", "missed_count"):
            val = g[score_key]
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                raise VerificationError(f"games[{idx}].{score_key} 必須為非負整數: {val}")

        for acc_key in ("overall_acc", "ball_acc", "strike_acc"):
            val = g[acc_key]
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0 or val > 100:
                raise VerificationError(f"games[{idx}].{acc_key} 必須在 0 到 100 之間: {val}")

        # Check sorting: game_date DESC, game_sno DESC
        current_sort_key = (gdate, sno)
        if prev_sort_key is not None and current_sort_key >= prev_sort_key:
            raise VerificationError(
                f"games 清單未按 (game_date DESC, game_sno DESC) 排序: "
                f"前項 {prev_sort_key} <= 當前項 {current_sort_key}"
            )
        prev_sort_key = current_sort_key

        # Verify corresponding game detail JSON exists
        game_file = games_dir / f"{gid}.json"
        if not game_file.exists():
            raise VerificationError(f"缺少 manifest 所對應的賽事詳細檔案: {game_file}")

    # Check for orphan files in games/
    if games_dir.exists():
        for item in games_dir.iterdir():
            if item.is_file() and item.suffix == ".json":
                gid_from_file = item.stem
                if gid_from_file not in seen_ids:
                    raise VerificationError(f"games/ 目錄存在未在 manifest 中引用的孤兒檔案: {item.name}")

    # Verify each game detail JSON content
    required_top_keys = {"game_info", "umpire_metrics", "plate_appearances", "all_called_pitches"}
    for gid in seen_ids:
        game_file = games_dir / f"{gid}.json"
        detail = _parse_json_strict(game_file)
        if not isinstance(detail, dict):
            raise VerificationError(f"{game_file.name} 根節點必須為 JSON 物件")

        missing_top = required_top_keys - set(detail.keys())
        if missing_top:
            raise VerificationError(f"{game_file.name} 缺少必要頂層欄位: {missing_top}")

        if not isinstance(detail["game_info"], dict):
            raise VerificationError(f"{game_file.name} game_info 必須為物件")
        if not isinstance(detail["umpire_metrics"], dict):
            raise VerificationError(f"{game_file.name} umpire_metrics 必須為物件")
        if not isinstance(detail["plate_appearances"], list):
            raise VerificationError(f"{game_file.name} plate_appearances 必須為陣列")
        if not isinstance(detail["all_called_pitches"], list):
            raise VerificationError(f"{game_file.name} all_called_pitches 必須為陣列")

    return {
        "status": "valid",
        "snapshot_dir": str(snapshot_path),
        "total_games": len(games),
        "default_game_id": default_game_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify static CPBL scorecard snapshot against data contract.")
    parser.add_argument("--input", "-i", required=True, help="Path to static snapshot data directory")
    args = parser.parse_args()

    try:
        res = verify_static_snapshot(args.input)
        print(
            f"[Verify OK] Snapshot at {res['snapshot_dir']} is valid. "
            f"Total games: {res['total_games']}, default: {res['default_game_id']}"
        )
        sys.exit(0)
    except VerificationError as e:
        print(f"[Verify ERROR] 靜態資料驗證失敗: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Verify UNEXPECTED ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
