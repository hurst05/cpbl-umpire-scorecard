import argparse
import contextlib
import json
import os
import shutil
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ensure server directory is in sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))
import db  # noqa: E402
from stats import calculate_season_stats  # noqa: E402
from verify_static import GAME_ID_PATTERN, verify_static_snapshot  # noqa: E402

DEFAULT_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".static-export", "data"))


def export_all(output_dir: str = DEFAULT_OUTPUT_DIR, custom_db_path: str = None) -> dict:
    """
    Export manifest.json, stats/*.json, and games/{game_id}.json from SQLite into output_dir.
    1. Validates game ID format and data_json integrity BEFORE writing files or building paths.
    2. Writes to an isolated UUID staging directory.
    3. Runs verify_static_snapshot on the staging directory.
    4. Two-stage atomic directory replacement with safe rollback on error.
    5. Runs final verify_static_snapshot on the destination directory.
    """
    output_path = Path(output_dir).resolve()

    if custom_db_path:
        db_path = Path(custom_db_path).resolve()
        if not db_path.is_file():
            raise FileNotFoundError(f"指定的 SQLite 資料庫不存在: {db_path}")
    else:
        db_path = Path(db.DB_PATH).resolve()
        if not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db.init_db()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(games)")
    columns = [col["name"] for col in cursor.fetchall()]
    has_duration_col = "game_duration_minutes" in columns
    has_consistency_col = "overall_consistency" in columns

    dur_col_clause = "game_duration_minutes," if has_duration_col else ""
    consistency_col_clause = "overall_consistency," if has_consistency_col else ""
    cursor.execute(f"""
        SELECT game_id, game_sno, kind_code, game_date, field,
               home_team, visiting_team, home_score, visiting_score,
               hp_umpire, overall_acc, ball_acc, strike_acc, {consistency_col_clause} missed_count,
               {dur_col_clause} data_json
        FROM games
        ORDER BY game_date DESC, game_sno DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    games_summary = []
    games_detail = {}

    for row in rows:
        gid = row["game_id"]
        if not gid or not isinstance(gid, str) or not GAME_ID_PATTERN.match(gid):
            raise ValueError(f"無效的賽事 ID 格式: {gid}")

        raw_json = row["data_json"]
        if not raw_json:
            raise ValueError(f"賽事 {gid} 缺少 data_json 資料，匯出終止。")

        try:
            # Reject NaN/Infinity
            def reject_constant(c, current_gid=gid):
                raise ValueError(f"賽事 {current_gid} 包含非法數值常數: {c}")

            detail = json.loads(raw_json, parse_constant=reject_constant)
        except Exception as e:
            raise ValueError(f"賽事 {gid} 的 data_json 損壞或包含無效格式: {e}") from e

        # 判決數明確為 0 時略過
        total_calls = detail.get("umpire_metrics", {}).get("total_called_pitches")
        if total_calls is not None and total_calls == 0:
            continue

        games_detail[gid] = detail

        dur_val = None
        if has_duration_col and row["game_duration_minutes"] is not None:
            dur_val = int(row["game_duration_minutes"])
        elif "game_duration_minutes" in detail.get("game_info", {}):
            dur_val = detail["game_info"]["game_duration_minutes"]

        consistency_val = None
        if has_consistency_col and row["overall_consistency"] is not None:
            consistency_val = float(row["overall_consistency"])
        elif "overall_consistency" in detail.get("umpire_metrics", {}):
            consistency_val = detail["umpire_metrics"]["overall_consistency"]
        elif detail.get("all_called_pitches"):
            from analyzer import calculate_game_consistency
            consistency_val = calculate_game_consistency(detail["all_called_pitches"])["consistency_rate"]

        summary_item = {
            "game_id": gid,
            "game_sno": int(row["game_sno"]) if row["game_sno"] is not None else 0,
            "game_date": str(row["game_date"]),
            "field": str(row["field"] or ""),
            "visiting_team": str(row["visiting_team"] or ""),
            "home_team": str(row["home_team"] or ""),
            "visiting_score": int(row["visiting_score"]) if row["visiting_score"] is not None else 0,
            "home_score": int(row["home_score"]) if row["home_score"] is not None else 0,
            "hp_umpire": str(row["hp_umpire"] or ""),
            "overall_acc": float(row["overall_acc"]) if row["overall_acc"] is not None else 0.0,
            "ball_acc": float(row["ball_acc"]) if row["ball_acc"] is not None else 0.0,
            "strike_acc": float(row["strike_acc"]) if row["strike_acc"] is not None else 0.0,
            "overall_consistency": consistency_val,
            "missed_count": int(row["missed_count"]) if row["missed_count"] is not None else 0,
            "game_duration_minutes": dur_val,
        }
        games_summary.append(summary_item)

    default_game_id = games_summary[0]["game_id"] if games_summary else None
    available_years = sorted(
        list({int(g["game_date"][:4]) for g in games_summary if g.get("game_date") and len(g["game_date"]) >= 4}),
        reverse=True,
    )

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).astimezone().isoformat(),
        "default_game_id": default_game_id,
        "available_years": available_years,
        "games": games_summary,
    }

    # Staging paths
    parent_dir = output_path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    staging_id = uuid.uuid4().hex
    temp_dir = parent_dir / f"data_staging_{staging_id}"
    backup_dir = parent_dir / f"data_backup_{staging_id}"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    staging_games_dir = temp_dir / "games"
    staging_games_dir.mkdir(parents=True, exist_ok=True)
    staging_stats_dir = temp_dir / "stats"
    staging_stats_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Write manifest to staging
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

        # Write yearly stats to staging
        all_stats = calculate_season_stats(games_summary, "全部")
        (staging_stats_dir / "all.json").write_text(
            json.dumps(all_stats, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
        )
        for yr in available_years:
            yr_games = [g for g in games_summary if g["game_date"].startswith(str(yr))]
            yr_stats = calculate_season_stats(yr_games, yr)
            (staging_stats_dir / f"{yr}.json").write_text(
                json.dumps(yr_stats, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
            )

        # Write game details to staging
        resolved_staging_games = staging_games_dir.resolve()
        for game_id, detail in games_detail.items():
            game_file = staging_games_dir / f"{game_id}.json"
            resolved_game_file = game_file.resolve()
            if not resolved_game_file.is_relative_to(resolved_staging_games):
                raise ValueError(f"路徑越界嘗試: {game_id}")

            game_file.write_text(json.dumps(detail, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

        # Verify staging directory
        verify_static_snapshot(temp_dir)

    except Exception as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"靜態匯出或暫存驗證失敗: {e}") from e

    # Safe directory sync & replacement with rollback support
    if output_path.exists():
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
        try:
            shutil.copytree(output_path, backup_dir)
        except Exception as e:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"無法備份現有快照目錄: {e}") from e

        try:
            # Clean old output_path contents
            for child in output_path.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()

            # Copy all contents from temp_dir into output_path
            for child in temp_dir.iterdir():
                if child.is_dir():
                    shutil.copytree(child, output_path / child.name)
                else:
                    shutil.copy2(child, output_path / child.name)

            verify_static_snapshot(output_path)
            # Success! Delete backup and staging
            shutil.rmtree(backup_dir, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as swap_err:
            # Rollback from backup_dir
            for child in output_path.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    with contextlib.suppress(Exception):
                        child.unlink()
            if backup_dir.exists():
                for child in backup_dir.iterdir():
                    if child.is_dir():
                        shutil.copytree(child, output_path / child.name)
                    else:
                        shutil.copy2(child, output_path / child.name)
                shutil.rmtree(backup_dir, ignore_errors=True)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"快照替換失敗，已還原上一份有效版本: {swap_err}") from swap_err
    else:
        output_path.mkdir(parents=True, exist_ok=True)
        try:
            for child in temp_dir.iterdir():
                if child.is_dir():
                    shutil.copytree(child, output_path / child.name)
                else:
                    shutil.copy2(child, output_path / child.name)
            verify_static_snapshot(output_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as direct_err:
            if output_path.exists():
                shutil.rmtree(output_path, ignore_errors=True)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"快照寫入失敗: {direct_err}") from direct_err

    return {
        "status": "success",
        "snapshot_dir": str(output_path),
        "total_games": len(games_summary),
        "default_game_id": default_game_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Export CPBL scorecard database to static JSON files.")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="Destination directory for static JSON")
    parser.add_argument("--db", help="Path to SQLite database file")
    args = parser.parse_args()

    try:
        result = export_all(output_dir=os.path.abspath(args.output), custom_db_path=args.db)
        print(
            f"[Export OK] Successfully exported {result['total_games']} games to {result['snapshot_dir']} "
            f"(default: {result['default_game_id']})"
        )
        sys.exit(0)
    except Exception as e:
        print(f"[Export ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
