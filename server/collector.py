import json
import re
import urllib.request

CPBL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_cpbl_url(url: str, timeout: int = 15) -> str:
    """Fetch raw HTML string from CPBL stats website."""
    req = urllib.request.Request(url, headers=CPBL_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_rsc_payload(html_text: str) -> str:
    """Extract and reconstruct full Next.js RSC payload stream from HTML."""
    pattern = re.compile(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', re.DOTALL)
    matches = pattern.findall(html_text)
    full_rsc = ""
    for m in matches:
        try:
            full_rsc += json.loads(f'"{m}"')
        except Exception:
            full_rsc += m
    return full_rsc


def extract_query_data(full_rsc: str, query_key_pattern: str):
    """Find and decode React Query dehydrated state object from RSC payload."""
    idx = full_rsc.find(query_key_pattern)
    if idx == -1:
        return None
    start_pos = full_rsc.rfind('{"dehydratedAt"', 0, idx)
    if start_pos == -1:
        start_pos = full_rsc.rfind('{"state"', 0, idx)
    if start_pos == -1:
        return None

    decoder = json.JSONDecoder()
    try:
        obj, _ = decoder.raw_decode(full_rsc[start_pos:])
        return obj.get("state", {}).get("data", {}).get("data")
    except Exception as e:
        print(f"Error decoding query {query_key_pattern}: {e}")
        return None


def fetch_players_dict(html_text: str = None) -> dict:
    """Extract player mapping by acnt or chName with heights and photos."""
    if not html_text:
        try:
            html_text = fetch_cpbl_url("https://stats.cpbl.com.tw/schedule")
        except Exception as e:
            print(f"Error fetching players: {e}")
            return {}
    rsc = extract_rsc_payload(html_text)
    data = extract_query_data(rsc, '["players"]')
    if not data or "players" not in data:
        return {}

    players_by_acnt = {}
    for p in data["players"]:
        acnt = p.get("acnt")
        if acnt:
            players_by_acnt[acnt] = {
                "acnt": acnt,
                "name": p.get("chName", "").replace("#", "").strip(),
                "height": p.get("height") or 180,
                "uniform_no": p.get("uniformNo"),
                "img_path": p.get("acntImgPath"),
                "team": p.get("team", {}).get("name"),
            }
    return players_by_acnt


def fetch_schedule_by_date(date_str: str) -> list:
    """Fetch schedule of games on a given date (YYYY-MM-DD)."""
    url = f"https://stats.cpbl.com.tw/schedule?date={date_str}"
    html = fetch_cpbl_url(url)
    rsc = extract_rsc_payload(html)

    data = extract_query_data(rsc, f'["game","list","{date_str}"]')
    if not data:
        data = extract_query_data(rsc, '"game"')

    if not data or "games" not in data:
        return []

    games_list = []
    for g in data.get("games", []):
        g_date = g.get("preExeDate", "")[:10]
        if date_str and g_date != date_str:
            continue
        if g.get("kindCode") != "A":
            continue
        visiting = g.get("visiting", {})
        home = g.get("home", {})
        games_list.append(
            {
                "game_id": g.get("gameId"),
                "game_sno": g.get("gameSno"),
                "kind_code": g.get("kindCode"),
                "date": g_date,
                "time": g.get("preExeDate", "")[11:16] if g.get("preExeDate") else "",
                "status": g.get("gameStatus"),
                "field": g.get("field", {}).get("abbe", ""),
                "visiting_team": visiting.get("team", {}).get("name", ""),
                "visiting_score": visiting.get("score"),
                "visiting_logo": visiting.get("team", {}).get("smallLogoUrl", ""),
                "home_team": home.get("team", {}).get("name", ""),
                "home_score": home.get("score"),
                "home_logo": home.get("team", {}).get("smallLogoUrl", ""),
                "has_trackman": not g.get("skipTrackman", False),
            }
        )
    return games_list


def parse_duration_str(dur_str: str | None) -> int | None:
    """Parse CPBL duration string (e.g. '025600' -> 176 mins)."""
    if not dur_str or not isinstance(dur_str, str):
        return None
    cleaned = dur_str.strip()
    if len(cleaned) >= 4 and cleaned.isdigit():
        hrs = int(cleaned[:2])
        mins = int(cleaned[2:4])
        return hrs * 60 + mins
    return None


def fetch_game_duration(game_id: str) -> int | None:
    """Fetch duration in minutes from CPBL live box if available."""
    try:
        parts = game_id.split("-")
        if len(parts) != 3:
            return None
        year, kind_code, sno = parts[0], parts[1], parts[2]
        data = urllib.parse.urlencode({"year": year, "kindCode": kind_code, "gameSno": sno}).encode("utf-8")
        req = urllib.request.Request(
            "https://www.cpbl.com.tw/box/getlive",
            data=data,
            headers={
                "User-Agent": CPBL_HEADERS["User-Agent"],
                "Accept-Language": "zh-TW,zh;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("GameDetailJson"):
                gd = json.loads(res["GameDetailJson"])
                if gd:
                    return parse_duration_str(gd[0].get("GameDuringTime"))
    except Exception:
        pass
    return None


def fetch_game_detail(game_id: str) -> dict:
    """Fetch raw game detail JSON directly from CPBL website."""
    url = f"https://stats.cpbl.com.tw/schedule/{game_id}"
    html = fetch_cpbl_url(url)
    rsc = extract_rsc_payload(html)

    players_dict = fetch_players_dict(html)

    data = extract_query_data(rsc, f'["game-detail","{game_id}"]')
    if not data or "game" not in data:
        raise ValueError(f"Could not find game data for {game_id}")

    duration_mins = fetch_game_duration(game_id)
    game_obj = data["game"]
    if duration_mins:
        game_obj["game_duration_minutes"] = duration_mins

    return {"game": game_obj, "players": players_dict, "game_duration_minutes": duration_mins}


def find_game_id_by_sno(sno: int, year: int = 2026, kind_code: str = "A") -> str:
    """Format or resolve game ID from season sno."""
    return f"{year}-{kind_code}-{sno}"
