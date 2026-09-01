import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import db
from collector import CPBL_HEADERS, parse_duration_str


import http.cookiejar

# Create shared cookie jar and opener
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [
    ("User-Agent", CPBL_HEADERS["User-Agent"]),
    ("Accept-Language", "zh-TW,zh;q=0.9"),
    ("X-Requested-With", "XMLHttpRequest"),
]

# Initialize cookie by hitting home page
try:
    opener.open("https://www.cpbl.com.tw/", timeout=10)
    print("已成功建立 CPBL 連線 Session。")
except Exception as e:
    print(f"初始化 CPBL 連線失敗: {e}")


def fetch_duration_worker(item):
    game_id, year, kind_code, sno = item
    try:
        data = urllib.parse.urlencode({"year": str(year), "kindCode": str(kind_code), "gameSno": str(sno)}).encode(
            "utf-8"
        )
        req = urllib.request.Request(
            "https://www.cpbl.com.tw/box/getlive",
            data=data,
        )
        with opener.open(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("GameDetailJson"):
                gd = json.loads(res["GameDetailJson"])
                if gd:
                    dur_str = gd[0].get("GameDuringTime")
                    minutes = parse_duration_str(dur_str)
                    return game_id, minutes
    except Exception as e:
        print(f"Error fetching duration for {game_id}: {e}")
    return game_id, None


def backfill_all_durations():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT game_id, game_sno, kind_code, game_date, data_json, game_duration_minutes
        FROM games
        WHERE game_duration_minutes IS NULL OR game_duration_minutes = 0
    """)
    rows = cursor.fetchall()

    if not rows:
        print("所有賽事已有比賽時間資料，無需回填。")
        conn.close()
        return

    print(f"共發現 {len(rows)} 場賽事缺少比賽時間，開始並行回填...")

    items = []
    for r in rows:
        gid = r["game_id"]
        parts = gid.split("-")
        if len(parts) == 3:
            items.append((gid, parts[0], parts[1], parts[2]))

    results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_duration_worker, it): it[0] for it in items}
        for future in as_completed(futures):
            gid, dur = future.result()
            if dur is not None:
                results[gid] = dur

    print(f"成功抓取 {len(results)} / {len(rows)} 場賽事的比賽時間，正在寫入資料庫...")

    updated_count = 0
    for r in rows:
        gid = r["game_id"]
        if gid in results:
            dur = results[gid]
            raw_json = r["data_json"]
            new_json = raw_json
            if raw_json:
                try:
                    d = json.loads(raw_json)
                    if "game_info" in d:
                        d["game_info"]["game_duration_minutes"] = dur
                        new_json = json.dumps(d, ensure_ascii=False)
                except Exception:
                    pass

            cursor.execute(
                """
                UPDATE games
                SET game_duration_minutes = ?, data_json = ?
                WHERE game_id = ?
            """,
                (dur, new_json, gid),
            )
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"回填完成！已成功更新 {updated_count} 筆賽事資料。")


if __name__ == "__main__":
    backfill_all_durations()
