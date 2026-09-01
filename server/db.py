import json
import os
import sqlite3

from stats import calculate_season_stats

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cpbl_scorecard.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
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
            game_duration_minutes INTEGER,
            data_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check if game_duration_minutes column exists, add if missing
    cursor.execute("PRAGMA table_info(games)")
    columns = [col["name"] for col in cursor.fetchall()]
    if "game_duration_minutes" not in columns:
        cursor.execute("ALTER TABLE games ADD COLUMN game_duration_minutes INTEGER")

    conn.commit()
    conn.close()


def save_game(game_id: str, analyzed_data: dict):
    info = analyzed_data.get("game_info", {})
    metrics = analyzed_data.get("umpire_metrics", {})
    kind_code = info.get("kind_code")
    total_calls = metrics.get("total_called_pitches", 0)

    # 只取一軍比賽且判決數大於 0 時才儲存
    if (kind_code and kind_code != "A") or total_calls == 0:
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO games (
            game_id, game_sno, kind_code, game_date, field,
            home_team, visiting_team, home_score, visiting_score,
            hp_umpire, overall_acc, ball_acc, strike_acc, missed_count,
            game_duration_minutes, data_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            game_id,
            info.get("game_sno"),
            info.get("kind_code"),
            info.get("date"),
            info.get("field"),
            info.get("home_team"),
            info.get("visiting_team"),
            info.get("home_score"),
            info.get("visiting_score"),
            info.get("hp_umpire"),
            metrics.get("overall_accuracy"),
            metrics.get("ball_accuracy"),
            metrics.get("strike_accuracy"),
            metrics.get("missed_count"),
            info.get("game_duration_minutes"),
            json.dumps(analyzed_data, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def get_game(game_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM games WHERE game_id = ?", (game_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["data_json"])
    return None


def list_available_years() -> list[int]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT CAST(substr(game_date, 1, 4) AS INTEGER) as year
        FROM games
        WHERE kind_code = 'A' AND game_date IS NOT NULL AND game_date != ''
        ORDER BY year DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [r["year"] for r in rows if r["year"]]


def list_cached_games(year: int | str = None) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(games)")
    columns = [col["name"] for col in cursor.fetchall()]
    dur_col = "game_duration_minutes," if "game_duration_minutes" in columns else ""

    if year:
        cursor.execute(
            f"""
            SELECT game_id, game_sno, kind_code, game_date, field,
                   home_team, visiting_team, home_score, visiting_score,
                   hp_umpire, overall_acc, ball_acc, strike_acc, missed_count,
                   {dur_col} updated_at
            FROM games
            WHERE kind_code = 'A' AND substr(game_date, 1, 4) = ?
            ORDER BY game_date DESC, game_sno DESC
        """,
            (str(year),),
        )
    else:
        cursor.execute(f"""
            SELECT game_id, game_sno, kind_code, game_date, field,
                   home_team, visiting_team, home_score, visiting_score,
                   hp_umpire, overall_acc, ball_acc, strike_acc, missed_count,
                   {dur_col} updated_at
            FROM games
            WHERE kind_code = 'A'
            ORDER BY game_date DESC, game_sno DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_season_stats(year: int | str = None) -> dict:
    games = list_cached_games(year)
    return calculate_season_stats(games, year)


init_db()
