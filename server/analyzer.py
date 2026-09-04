import math

# Standard baseball and strike zone geometry constants
PLATE_WIDTH_M = 0.44  # 44 cm (Home plate width 17 in)
W_HALF = 0.22  # 22 cm half width (x in [-0.22, 0.22] m)
BALL_RADIUS_M = 0.0369  # 3.69 cm baseball radius

# Height proportions for top/bottom of strike zone
SZ_TOP_RATIO = 0.00535  # 0.535 of batter height in cm -> m
SZ_BOTTOM_RATIO = 0.00270  # 0.270 of batter height in cm -> m
DEFAULT_BATTER_HEIGHT = 180  # cm

PITCH_TYPE_NAMES = {
    "fastball": "快速球",
    "breakingball": "變化球",
    "curveball": "曲球",
    "slider": "滑球",
    "changeup": "變速球",
    "cutter": "卡特球",
    "forkball": "指叉球",
    "sinker": "伸卡球",
    "splitter": "指叉球",
    "knuckleball": "蝴蝶球",
}


def calculate_strike_zone(batter_height_cm: int | None) -> tuple[float, float]:
    """Calculate sz_top and sz_bottom in meters from batter height."""
    h = batter_height_cm if (batter_height_cm and batter_height_cm > 100) else DEFAULT_BATTER_HEIGHT
    sz_top = round(h * SZ_TOP_RATIO, 5)
    sz_bottom = round(h * SZ_BOTTOM_RATIO, 5)
    return sz_top, sz_bottom


def evaluate_pitch_call(x: float, z: float, sz_top: float, sz_bottom: float, called_str: str) -> dict:
    abs_x = abs(x)
    dx = max(0.0, abs_x - W_HALF)
    if z > sz_top:
        dz = z - sz_top
    elif z < sz_bottom:
        dz = sz_bottom - z
    else:
        dz = 0.0

    d_center = math.sqrt(dx * dx + dz * dz)

    if dx == 0.0 and dz == 0.0:
        dist_to_inner = min(W_HALF - abs_x, z - sz_bottom, sz_top - z)
        dist_edge = dist_to_inner + BALL_RADIUS_M
        is_true_strike = True
    else:
        if d_center <= BALL_RADIUS_M:
            dist_edge = BALL_RADIUS_M - d_center
            is_true_strike = True
        else:
            dist_edge = d_center - BALL_RADIUS_M
            is_true_strike = False

    dist_cm = round(dist_edge * 100, 2)
    true_call = "STRIKE" if is_true_strike else "BALL"
    is_correct = called_str == true_call

    return {"true_call": true_call, "is_correct": is_correct, "dist_cm": dist_cm, "dist_m": dist_edge}


def analyze_game(raw_game_data: dict, players_dict: dict = None) -> dict:
    game = raw_game_data.get("game", raw_game_data)
    live_log = game.get("liveLog", [])
    players = players_dict or raw_game_data.get("players", {})

    referees = {r.get("job", ""): r.get("name", "") for r in game.get("referee", [])}
    hp_umpire = referees.get("主審", referees.get("HP", "林金達"))

    visiting_team_name = game.get("visiting", {}).get("team", {}).get("name", "客隊")
    home_team_name = game.get("home", {}).get("team", {}).get("name", "主隊")

    pas_raw = []
    current_pa = []
    current_key = None

    for item in live_log:
        pa_key = (
            item.get("inningSeq"),
            item.get("visitingHomeType"),
            item.get("hitterAcnt"),
            item.get("hitterName"),
            item.get("battingOrder"),
        )
        if current_key is None or pa_key != current_key:
            if current_pa:
                pas_raw.append(current_pa)
            current_pa = [item]
            current_key = pa_key
        else:
            if item.get("pitchCnt") == 1 and len(current_pa) > 0 and current_pa[-1].get("pitchCnt") != 0:
                pas_raw.append(current_pa)
                current_pa = [item]
            else:
                current_pa.append(item)
    if current_pa:
        pas_raw.append(current_pa)

    all_called_pitches = []
    plate_appearances = []

    for pa_idx, pa_events in enumerate(pas_raw, start=1):
        first_evt = pa_events[0]
        last_evt = pa_events[-1]

        inning_seq = first_evt.get("inningSeq")
        v_h_type = str(first_evt.get("visitingHomeType"))
        half_str = "上" if v_h_type == "1" else "下"

        hitter_name = first_evt.get("hitterName", "")
        hitter_no = first_evt.get("hitterUniformNo", "")
        hitter_acnt = first_evt.get("hitterAcnt", "")
        pitcher_name = first_evt.get("pitcherName", "")
        pitcher_no = first_evt.get("pitcherUniformNo", "")
        pitcher_acnt = first_evt.get("pitcherAcnt", "")

        batter_info = players.get(hitter_acnt, {})
        batter_height = batter_info.get("height") or DEFAULT_BATTER_HEIGHT
        sz_top, sz_bottom = calculate_strike_zone(batter_height)

        outs_start = first_evt.get("outCnt", 0)
        bases_start = {
            "1B": bool(first_evt.get("firstBase")),
            "2B": bool(first_evt.get("secondBase")),
            "3B": bool(first_evt.get("thirdBase")),
        }
        score_v_start = first_evt.get("visitingScore", 0)
        score_h_start = first_evt.get("homeScore", 0)

        pa_pitches = []

        for p_idx, pitch_evt in enumerate(pa_events, start=1):
            content = pitch_evt.get("content", "")
            tm = pitch_evt.get("trackman") or {}
            play = tm.get("play") or {}
            pitch_tag = play.get("pitchTag") or {}
            pitch_loc = tm.get("pitch", {}).get("location") or {}
            pitch_rel = tm.get("pitch", {}).get("release") or {}

            pitch_call_tag = pitch_tag.get("pitchCall", "")
            raw_pitch_type = pitch_tag.get("taggedPitchType") or pitch_tag.get("autoPitchType") or ""
            pitch_type_zh = PITCH_TYPE_NAMES.get(raw_pitch_type.lower(), raw_pitch_type) or "快速球"

            rel_speed = pitch_rel.get("relSpeed")
            speed_kmh = (
                round(rel_speed, 1)
                if rel_speed
                else (round(pitch_loc.get("zoneSpeed", 0), 1) if pitch_loc.get("zoneSpeed") else None)
            )

            x = pitch_loc.get("plateLocSide")
            z = pitch_loc.get("plateLocHeight")

            is_called_strike = (pitch_call_tag == "StrikeCalled") or ("好球沒揮棒" in content)
            is_called_ball = (pitch_call_tag == "BallCalled") or (
                content.startswith("壞球") and "揮棒" not in content and "揮空" not in content
            )
            is_called_pitch = (is_called_strike or is_called_ball) and (x is not None and z is not None)

            evaluation = None
            called_str = None
            advantage = None
            favored_team = None
            if is_called_pitch:
                called_str = "STRIKE" if is_called_strike else "BALL"
                evaluation = evaluate_pitch_call(x, z, sz_top, sz_bottom, called_str)

                if not evaluation["is_correct"]:
                    if evaluation["true_call"] == "STRIKE" and called_str == "BALL":
                        advantage = "BATTER"
                        favored_team = visiting_team_name if v_h_type == "1" else home_team_name
                    elif evaluation["true_call"] == "BALL" and called_str == "STRIKE":
                        advantage = "PITCHER"
                        favored_team = home_team_name if v_h_type == "1" else visiting_team_name

                call_record = {
                    "pa_index": pa_idx,
                    "pitch_index": p_idx,
                    "inning_half": half_str,
                    "inning_num": inning_seq,
                    "pitcher": pitcher_name,
                    "batter": hitter_name,
                    "content": content,
                    "count_b": pitch_evt.get("ballCnt", 0),
                    "count_s": pitch_evt.get("strikeCnt", 0),
                    "outs": pitch_evt.get("outCnt", 0),
                    "bases": [
                        1 if bases_start["1B"] else 0,
                        1 if bases_start["2B"] else 0,
                        1 if bases_start["3B"] else 0,
                    ],
                    "x": round(x, 5),
                    "z": round(z, 5),
                    "sz_top": sz_top,
                    "sz_bottom": sz_bottom,
                    "called": called_str,
                    "true_call": evaluation["true_call"],
                    "is_correct": evaluation["is_correct"],
                    "dist_cm": evaluation["dist_cm"],
                    "advantage": advantage,
                    "favored_team": favored_team,
                    "pitch_type": pitch_type_zh,
                    "speed_kmh": speed_kmh,
                }
                all_called_pitches.append(call_record)

            pa_pitches.append(
                {
                    "pitch_num": p_idx,
                    "content": content,
                    "count_b": pitch_evt.get("ballCnt", 0),
                    "count_s": pitch_evt.get("strikeCnt", 0),
                    "out_cnt": pitch_evt.get("outCnt", 0),
                    "pitch_type": pitch_type_zh,
                    "speed_kmh": speed_kmh,
                    "x": round(x, 4) if x is not None else None,
                    "z": round(z, 4) if z is not None else None,
                    "sz_top": sz_top,
                    "sz_bottom": sz_bottom,
                    "is_called_pitch": is_called_pitch,
                    "called": called_str if is_called_pitch else None,
                    "true_call": evaluation["true_call"] if evaluation else None,
                    "is_correct": evaluation["is_correct"] if evaluation else None,
                    "dist_cm": evaluation["dist_cm"] if evaluation else None,
                    "advantage": advantage,
                    "favored_team": favored_team,
                }
            )

        plate_appearances.append(
            {
                "pa_num": pa_idx,
                "inning": f"{inning_seq}局{half_str}",
                "batting_team": visiting_team_name if v_h_type == "1" else home_team_name,
                "fielding_team": home_team_name if v_h_type == "1" else visiting_team_name,
                "pitcher": {
                    "name": pitcher_name,
                    "uniform_no": pitcher_no,
                    "img": first_evt.get("pitcherImgPath") or players.get(pitcher_acnt, {}).get("img_path"),
                },
                "batter": {
                    "name": hitter_name,
                    "uniform_no": hitter_no,
                    "img": first_evt.get("hitterImgPath") or players.get(hitter_acnt, {}).get("img_path"),
                    "height": batter_height,
                },
                "batting_order": first_evt.get("battingOrder"),
                "game_state": {
                    "outs": outs_start,
                    "bases": bases_start,
                    "score_visiting": score_v_start,
                    "score_home": score_h_start,
                },
                "pitches": pa_pitches,
                "outcome": last_evt.get("content"),
            }
        )

    total_calls = len(all_called_pitches)
    correct_calls = [p for p in all_called_pitches if p["is_correct"]]
    missed_calls = [p for p in all_called_pitches if not p["is_correct"]]

    true_balls = [p for p in all_called_pitches if p["true_call"] == "BALL"]
    true_balls_correct = [p for p in true_balls if p["called"] == "BALL"]

    true_strikes = [p for p in all_called_pitches if p["true_call"] == "STRIKE"]
    true_strikes_correct = [p for p in true_strikes if p["called"] == "STRIKE"]

    overall_acc = round((len(correct_calls) / total_calls * 100), 1) if total_calls > 0 else 100.0
    ball_acc = round((len(true_balls_correct) / len(true_balls) * 100), 1) if len(true_balls) > 0 else 100.0
    strike_acc = round((len(true_strikes_correct) / len(true_strikes) * 100), 1) if len(true_strikes) > 0 else 100.0

    avg_miss_dist = round(sum(p["dist_cm"] for p in missed_calls) / len(missed_calls), 1) if missed_calls else 0.0
    missed_calls_sorted = sorted(missed_calls, key=lambda x: x["dist_cm"], reverse=True)

    pitcher_favored_calls = [p for p in missed_calls if p.get("advantage") == "PITCHER"]
    batter_favored_calls = [p for p in missed_calls if p.get("advantage") == "BATTER"]

    pitcher_favored_dist = round(sum(p["dist_cm"] for p in pitcher_favored_calls), 1)
    batter_favored_dist = round(sum(p["dist_cm"] for p in batter_favored_calls), 1)

    pitcher_favored_avg = round(pitcher_favored_dist / len(pitcher_favored_calls), 1) if pitcher_favored_calls else 0.0
    batter_favored_avg = round(batter_favored_dist / len(batter_favored_calls), 1) if batter_favored_calls else 0.0

    home_favored_calls = [p for p in missed_calls if p.get("favored_team") == home_team_name]
    visiting_favored_calls = [p for p in missed_calls if p.get("favored_team") == visiting_team_name]
    home_favored_dist = round(sum(p["dist_cm"] for p in home_favored_calls), 1)
    visiting_favored_dist = round(sum(p["dist_cm"] for p in visiting_favored_calls), 1)
    home_favored_avg = round(home_favored_dist / len(home_favored_calls), 1) if home_favored_calls else 0.0
    visiting_favored_avg = (
        round(visiting_favored_dist / len(visiting_favored_calls), 1) if visiting_favored_calls else 0.0
    )

    game_consistency = calculate_game_consistency(all_called_pitches, radius_cm=7.5)

    return {
        "game_info": {
            "game_id": game.get("gameId"),
            "game_sno": game.get("gameSno"),
            "kind_code": game.get("kindCode"),
            "date": game.get("preExeDate", "")[:10],
            "field": game.get("field", {}).get("abbe", ""),
            "home_team": home_team_name,
            "visiting_team": visiting_team_name,
            "home_score": game.get("home", {}).get("score", 0),
            "visiting_score": game.get("visiting", {}).get("score", 0),
            "hp_umpire": hp_umpire,
            "total_pitches": len(live_log),
            "game_duration_minutes": game.get("game_duration_minutes") or raw_game_data.get("game_duration_minutes"),
        },
        "umpire_metrics": {
            "hp_umpire": hp_umpire,
            "total_called_pitches": total_calls,
            "correct_count": len(correct_calls),
            "missed_count": len(missed_calls),
            "overall_accuracy": overall_acc,
            "ball_accuracy": ball_acc,
            "strike_accuracy": strike_acc,
            "overall_consistency": game_consistency["consistency_rate"],
            "consistency_ratio_str": game_consistency["ratio_str"],
            "consistent_pairs": game_consistency["consistent_pairs"],
            "total_pairs": game_consistency["total_pairs"],
            "conflicting_pitches_count": game_consistency["conflicting_pitches_count"],
            "ball_ratio_str": f"{len(true_balls_correct)}/{len(true_balls)}",
            "strike_ratio_str": f"{len(true_strikes_correct)}/{len(true_strikes)}",
            "overall_ratio_str": f"{len(correct_calls)}/{total_calls}",
            "avg_miss_distance_cm": avg_miss_dist,
            "home_favored_count": len(home_favored_calls),
            "home_favored_dist_cm": home_favored_dist,
            "home_favored_avg_cm": home_favored_avg,
            "visiting_favored_count": len(visiting_favored_calls),
            "visiting_favored_dist_cm": visiting_favored_dist,
            "visiting_favored_avg_cm": visiting_favored_avg,
            "pitcher_favored_count": len(pitcher_favored_calls),
            "pitcher_favored_dist_cm": pitcher_favored_dist,
            "pitcher_favored_avg_cm": pitcher_favored_avg,
            "batter_favored_count": len(batter_favored_calls),
            "batter_favored_dist_cm": batter_favored_dist,
            "batter_favored_avg_cm": batter_favored_avg,
            "missed_calls": missed_calls_sorted,
        },
        "all_called_pitches": all_called_pitches,
        "plate_appearances": plate_appearances,
    }


def calculate_pitch_distance_cm(p1: dict, p2: dict, target_zone_height_m: float | None = None) -> float:
    """Calculate hybrid distance: absolute X (plate width) + normalized Z (batter strike zone)."""
    x1, z1 = p1.get("x"), p1.get("z")
    x2, z2 = p2.get("x"), p2.get("z")
    if x1 is None or z1 is None or x2 is None or z2 is None:
        return float("inf")

    dx_cm = (x1 - x2) * 100

    top1 = p1.get("sz_top") or 0.963
    bot1 = p1.get("sz_bottom") or 0.486
    h1 = (top1 - bot1) if (top1 - bot1) > 0 else 0.477
    norm_z1 = (z1 - bot1) / h1

    top2 = p2.get("sz_top") or 0.963
    bot2 = p2.get("sz_bottom") or 0.486
    h2 = (top2 - bot2) if (top2 - bot2) > 0 else 0.477
    norm_z2 = (z2 - bot2) / h2

    base_h = target_zone_height_m if target_zone_height_m else h1
    dz_cm = (norm_z1 - norm_z2) * base_h * 100

    return round(math.sqrt(dx_cm * dx_cm + dz_cm * dz_cm), 1)


def is_same_pitch(p1: dict, p2: dict) -> bool:
    """Check if two pitch dicts represent the exact same pitch."""
    if p1 is p2:
        return True
    pa1 = p1.get("pa_index") or p1.get("pa_num")
    pa2 = p2.get("pa_index") or p2.get("pa_num")
    p_idx1 = p1.get("pitch_index") or p1.get("pitch_num")
    p_idx2 = p2.get("pitch_index") or p2.get("pitch_num")
    if pa1 is not None and pa2 is not None and pa1 == pa2 and p_idx1 is not None and p_idx2 is not None:
        return p_idx1 == p_idx2

    return (
        abs(p1.get("x", 0) - p2.get("x", 0)) < 0.0005
        and abs(p1.get("z", 0) - p2.get("z", 0)) < 0.0005
        and p1.get("inning_num") == p2.get("inning_num")
        and p1.get("inning_half") == p2.get("inning_half")
        and p1.get("called") == p2.get("called")
    )


def find_similar_pitches(target_pitch: dict, all_pitches: list[dict], radius_cm: float = 8.0) -> list[dict]:
    """Find all called pitches within radius_cm distance from target_pitch using hybrid distance."""
    results = []
    target_top = target_pitch.get("sz_top")
    target_bot = target_pitch.get("sz_bottom")
    target_zone_h = (target_top - target_bot) if (target_top and target_bot and target_top > target_bot) else None

    for p in all_pitches:
        if is_same_pitch(target_pitch, p):
            continue

        dist = calculate_pitch_distance_cm(target_pitch, p, target_zone_h)
        if dist <= radius_cm:
            item = dict(p)
            item["distance_to_target_cm"] = dist
            results.append(item)

    return sorted(results, key=lambda x: x["distance_to_target_cm"])


def calculate_game_consistency(all_called_pitches: list[dict], radius_cm: float = 7.5) -> dict:
    """Calculate overall game consistency using Method A (Pairwise Neighborhood Consistency)."""
    valid_pitches = [
        p for p in all_called_pitches if p.get("x") is not None and p.get("z") is not None and p.get("called")
    ]
    n = len(valid_pitches)

    if n <= 1:
        return {
            "consistency_rate": 100.0,
            "consistent_pairs": 0,
            "total_pairs": 0,
            "conflicting_pitches_count": 0,
            "isolated_count": n,
            "total_pitches": n,
            "ratio_str": "0/0",
        }

    total_pairs = 0
    consistent_pairs = 0
    conflicting_set = set()
    has_neighbor_set = set()

    for i in range(n):
        p1 = valid_pitches[i]
        top1 = p1.get("sz_top")
        bot1 = p1.get("sz_bottom")
        target_zone_h = (top1 - bot1) if (top1 and bot1 and top1 > bot1) else None

        for j in range(i + 1, n):
            p2 = valid_pitches[j]
            if is_same_pitch(p1, p2):
                continue

            dist = calculate_pitch_distance_cm(p1, p2, target_zone_h)
            if dist <= radius_cm:
                total_pairs += 1
                has_neighbor_set.add(i)
                has_neighbor_set.add(j)

                if p1.get("called") == p2.get("called"):
                    consistent_pairs += 1
                else:
                    conflicting_set.add(i)
                    conflicting_set.add(j)

    isolated_count = n - len(has_neighbor_set)
    consistency_rate = round((consistent_pairs / total_pairs * 100), 1) if total_pairs > 0 else 100.0

    return {
        "consistency_rate": consistency_rate,
        "consistent_pairs": consistent_pairs,
        "total_pairs": total_pairs,
        "conflicting_pitches_count": len(conflicting_set),
        "isolated_count": isolated_count,
        "total_pitches": n,
        "ratio_str": f"{consistent_pairs}/{total_pairs}",
    }
