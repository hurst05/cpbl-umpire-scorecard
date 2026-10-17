import os
from datetime import date as Date
from typing import Annotated

import db
import uvicorn
from analyzer import analyze_game
from collector import fetch_game_detail, fetch_schedule_by_date, find_game_id_by_sno
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from game_types import SUPPORTED_KIND_CODES, GameKind, get_game_kind

app = FastAPI(title="CPBL Umpire Scorecard & Pitch Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "CPBL Scorecard Engine"}


@app.get("/api/schedule")
def get_schedule(date: Annotated[Date, Query(description="Date YYYY-MM-DD")], kind_code: GameKind = "A"):
    try:
        games = fetch_schedule_by_date(date.isoformat(), kind_code)
        return {"date": date.isoformat(), "kind_code": kind_code, "games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/game/{game_id}")
def get_game_analysis(game_id: str, force_refresh: bool = False):
    requested_kind = get_game_kind({"game_id": game_id})
    if requested_kind not in SUPPORTED_KIND_CODES:
        raise HTTPException(status_code=400, detail=f"賽事 {game_id} 非一軍支援賽事，略過載入分析")
    cached = None
    if not force_refresh:
        cached = db.get_game(game_id)
        if cached:
            total_calls = cached.get("umpire_metrics", {}).get("total_called_pitches", 0)
            kind_code = get_game_kind(cached.get("game_info", {}))
            cached_status = cached.get("game_info", {}).get("status")
            # shortcut: 舊快取缺少狀態；需辨識既有未完賽場次時，再回補狀態。
            if kind_code != requested_kind or total_calls == 0:
                cached = None
            elif cached_status in (None, "FINISHED"):
                return cached

    try:
        raw_data = fetch_game_detail(game_id)
        game_raw = raw_data.get("game", {})
        kind_code = game_raw.get("kindCode") or requested_kind
        if kind_code not in SUPPORTED_KIND_CODES:
            raise HTTPException(
                status_code=400,
                detail=f"賽事 {game_id} 非一軍比賽 (kindCode={kind_code})，略過載入分析",
            )
        if kind_code != requested_kind:
            raise HTTPException(status_code=400, detail=f"賽事 {game_id} 的類型與資料不符: {kind_code}")

        analyzed = analyze_game(game_raw, raw_data.get("players", {}))
        total_calls = analyzed.get("umpire_metrics", {}).get("total_called_pitches", 0)
        if total_calls == 0:
            if cached:
                return {
                    **cached,
                    "refresh_warning": "官網目前沒有可分析的 Trackman 球點。先顯示上次成功擷取的部分資料"
                    "（非完整完賽結果），請稍後再搜尋更新。",
                }
            raise HTTPException(
                status_code=400,
                detail=f"賽事 {game_id} 官網目前缺少可分析的 Trackman 球點（判決數為 0），請稍後重試",
            )

        db.save_game(game_id, analyzed)
        return analyzed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch and analyze {game_id}: {str(e)}") from e


@app.get("/api/game/sno/{sno}")
def get_game_by_sno(sno: int, year: int = 2026, kind_code: GameKind = "A", force_refresh: bool = False):
    game_id = find_game_id_by_sno(sno, year, kind_code)
    return get_game_analysis(game_id, force_refresh)


@app.get("/api/seasons")
def get_seasons(kind_code: GameKind = "A"):
    """Get list of available seasons/years."""
    years = db.list_available_years(kind_code)
    return {"seasons": years}


@app.get("/api/stats/season/{year}")
def get_season_statistics(year: str, kind_code: GameKind = "A"):
    """Get aggregated statistics for a specific year (or 'all')."""
    target_year = None if year.lower() in ("all", "全部") else year
    return db.get_season_stats(target_year, kind_code)


@app.get("/api/games/cached")
def get_cached_games(year: str = Query(None, description="Filter by year (e.g. 2026)"), kind_code: GameKind = "A"):
    target_year = None if (not year or year.lower() in ("all", "全部")) else year
    return db.list_cached_games(target_year, kind_code)


@app.post("/api/batch-collect")
def batch_collect_date(date: Date, kind_code: GameKind = "A"):
    games = fetch_schedule_by_date(date.isoformat(), kind_code)
    results = []
    for g in games:
        gid = g.get("game_id")
        if get_game_kind(g) != kind_code:
            results.append({"game_id": gid, "status": "skipped", "reason": "非一軍選定類型賽事"})
            continue
        if gid and g.get("has_trackman") and g.get("status") in ("START", "FINISHED"):
            try:
                raw_data = fetch_game_detail(gid)
                game_raw = raw_data.get("game", {})
                if game_raw.get("kindCode", get_game_kind({"game_id": gid})) != kind_code:
                    results.append({"game_id": gid, "status": "skipped", "reason": "非一軍選定類型賽事"})
                    continue
                analyzed = analyze_game(game_raw, raw_data.get("players", {}))
                total_calls = analyzed.get("umpire_metrics", {}).get("total_called_pitches", 0)
                if total_calls == 0:
                    results.append({"game_id": gid, "status": "skipped", "reason": "判決數為 0"})
                    continue
                db.save_game(gid, analyzed)
                results.append({"game_id": gid, "status": "success"})
            except Exception as e:
                results.append({"game_id": gid, "status": "error", "message": str(e)})
        else:
            if gid:
                results.append({"game_id": gid, "status": "skipped", "reason": "賽事狀態不符或無 Trackman 數據"})
    return {"date": date, "processed": results}


dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
