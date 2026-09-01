import os

import db
import uvicorn
from analyzer import analyze_game
from collector import fetch_game_detail, fetch_schedule_by_date, find_game_id_by_sno
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
def get_schedule(date: str = Query(..., description="Date YYYY-MM-DD")):
    try:
        games = fetch_schedule_by_date(date)
        return {"date": date, "games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/game/{game_id}")
def get_game_analysis(game_id: str, force_refresh: bool = False):
    if not force_refresh:
        cached = db.get_game(game_id)
        if cached:
            total_calls = cached.get("umpire_metrics", {}).get("total_called_pitches", 0)
            kind_code = cached.get("game_info", {}).get("kind_code")
            if (kind_code and kind_code != "A") or total_calls == 0:
                pass  # 快取為無效資料，繼續向下重新抓取
            else:
                return cached

    try:
        raw_data = fetch_game_detail(game_id)
        game_raw = raw_data.get("game", {})
        kind_code = game_raw.get("kindCode")
        if kind_code and kind_code != "A":
            raise HTTPException(
                status_code=400,
                detail=f"賽事 {game_id} 非一軍比賽 (kindCode={kind_code})，略過載入分析",
            )

        analyzed = analyze_game(game_raw, raw_data.get("players", {}))
        total_calls = analyzed.get("umpire_metrics", {}).get("total_called_pitches", 0)
        if total_calls == 0:
            raise HTTPException(status_code=400, detail=f"賽事 {game_id} 判決數為 0，略過載入與儲存")

        db.save_game(game_id, analyzed)
        return analyzed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch and analyze {game_id}: {str(e)}") from e


@app.get("/api/game/sno/{sno}")
def get_game_by_sno(sno: int, year: int = 2026, kind_code: str = "A", force_refresh: bool = False):
    if kind_code != "A":
        raise HTTPException(status_code=400, detail=f"僅支援一軍比賽 (kind_code={kind_code})")
    game_id = find_game_id_by_sno(sno, year, kind_code)
    return get_game_analysis(game_id, force_refresh)


@app.get("/api/seasons")
def get_seasons():
    """Get list of available seasons/years."""
    years = db.list_available_years()
    return {"seasons": years}


@app.get("/api/stats/season/{year}")
def get_season_statistics(year: str):
    """Get aggregated statistics for a specific year (or 'all')."""
    target_year = None if year.lower() in ("all", "全部") else year
    return db.get_season_stats(target_year)


@app.get("/api/games/cached")
def get_cached_games(year: str = Query(None, description="Filter by year (e.g. 2026)")):
    target_year = None if (not year or year.lower() in ("all", "全部")) else year
    return db.list_cached_games(target_year)


@app.post("/api/batch-collect")
def batch_collect_date(date: str):
    games = fetch_schedule_by_date(date)
    results = []
    for g in games:
        gid = g.get("game_id")
        kind_code = g.get("kind_code")
        if kind_code and kind_code != "A":
            results.append({"game_id": gid, "status": "skipped", "reason": "非一軍賽事"})
            continue
        if gid and g.get("has_trackman") and g.get("status") == "FINISHED":
            try:
                raw_data = fetch_game_detail(gid)
                game_raw = raw_data.get("game", {})
                if game_raw.get("kindCode") and game_raw.get("kindCode") != "A":
                    results.append({"game_id": gid, "status": "skipped", "reason": "非一軍賽事"})
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
                results.append({"game_id": gid, "status": "skipped", "reason": "未完賽或無 Trackman 數據"})
    return {"date": date, "processed": results}


dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
