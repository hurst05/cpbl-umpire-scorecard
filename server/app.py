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
            return cached

    try:
        raw_data = fetch_game_detail(game_id)
        analyzed = analyze_game(raw_data["game"], raw_data.get("players", {}))
        db.save_game(game_id, analyzed)
        return analyzed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch and analyze {game_id}: {str(e)}") from e


@app.get("/api/game/sno/{sno}")
def get_game_by_sno(sno: int, year: int = 2026, kind_code: str = "A", force_refresh: bool = False):
    game_id = find_game_id_by_sno(sno, year, kind_code)
    return get_game_analysis(game_id, force_refresh)


@app.get("/api/games/cached")
def get_cached_games():
    return db.list_cached_games()


@app.post("/api/batch-collect")
def batch_collect_date(date: str):
    games = fetch_schedule_by_date(date)
    results = []
    for g in games:
        gid = g.get("game_id")
        if gid and g.get("has_trackman") and g.get("status") == "FINISHED":
            try:
                raw_data = fetch_game_detail(gid)
                analyzed = analyze_game(raw_data["game"], raw_data.get("players", {}))
                db.save_game(gid, analyzed)
                results.append({"game_id": gid, "status": "success"})
            except Exception as e:
                results.append({"game_id": gid, "status": "error", "message": str(e)})
    return {"date": date, "processed": results}


dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
