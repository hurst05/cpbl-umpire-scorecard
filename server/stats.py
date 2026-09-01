def format_duration(minutes: float | None) -> str:
    """Format duration in minutes to 'X小時 Y分' string."""
    if minutes is None or minutes <= 0:
        return "無資料"
    total_mins = int(round(minutes))
    hrs = total_mins // 60
    mins = total_mins % 60
    if hrs > 0:
        return f"{hrs}小時 {mins}分"
    return f"{mins}分"


def calculate_season_stats(games: list[dict], year: int | str = None) -> dict:
    """
    Calculate comprehensive season statistics from a list of game dictionaries.
    Handles game duration, run differentials, winning/losing team scores,
    umpire metrics, team standings, and stadium breakdowns.
    """
    if not games:
        return {
            "year": str(year) if year else "全部",
            "total_games": 0,
            "duration": {
                "avg_minutes": 0,
                "formatted_avg": "無資料",
                "valid_games_count": 0,
                "shortest_game": None,
                "longest_game": None,
            },
            "scores": {
                "avg_margin": 0.0,
                "avg_winner_score": 0.0,
                "avg_loser_score": 0.0,
                "avg_total_runs": 0.0,
                "total_runs": 0,
                "one_run_games_count": 0,
                "one_run_games_pct": 0.0,
                "blowout_games_count": 0,
                "blowout_games_pct": 0.0,
                "tie_games_count": 0,
                "margin_distribution": {"1": 0, "2": 0, "3-4": 0, "5+": 0},
            },
            "home_away": {
                "home_wins": 0,
                "visiting_wins": 0,
                "ties": 0,
                "home_win_pct": 0.0,
                "visiting_win_pct": 0.0,
            },
            "umpire_summary": {
                "avg_overall_acc": 0.0,
                "avg_ball_acc": 0.0,
                "avg_strike_acc": 0.0,
                "avg_missed_calls": 0.0,
                "total_missed_calls": 0,
                "highest_acc_game": None,
                "lowest_acc_game": None,
            },
            "umpire_leaderboard": [],
            "team_standings": [],
            "stadium_stats": [],
        }

    total_games = len(games)

    # 1. Game Duration Stats
    durations = []
    dur_games = []
    for g in games:
        dur = g.get("game_duration_minutes")
        if dur is not None and dur > 0:
            durations.append(dur)
            dur_games.append(g)

    valid_dur_count = len(durations)
    avg_dur_mins = round(sum(durations) / valid_dur_count, 1) if valid_dur_count > 0 else 0
    formatted_avg_dur = format_duration(avg_dur_mins) if valid_dur_count > 0 else "無資料"

    shortest_game = None
    longest_game = None
    if dur_games:
        s_game = min(dur_games, key=lambda x: x["game_duration_minutes"])
        l_game = max(dur_games, key=lambda x: x["game_duration_minutes"])
        shortest_game = {
            "game_id": s_game.get("game_id"),
            "game_sno": s_game.get("game_sno"),
            "date": s_game.get("game_date"),
            "matchup": f"{s_game.get('visiting_team')} vs {s_game.get('home_team')}",
            "minutes": s_game.get("game_duration_minutes"),
            "formatted": format_duration(s_game.get("game_duration_minutes")),
        }
        longest_game = {
            "game_id": l_game.get("game_id"),
            "game_sno": l_game.get("game_sno"),
            "date": l_game.get("game_date"),
            "matchup": f"{l_game.get('visiting_team')} vs {l_game.get('home_team')}",
            "minutes": l_game.get("game_duration_minutes"),
            "formatted": format_duration(l_game.get("game_duration_minutes")),
        }

    # 2. Scores and Run Margin Stats
    margins = []
    winner_scores = []
    loser_scores = []
    total_runs_list = []
    one_run_count = 0
    blowout_count = 0
    tie_count = 0
    home_wins = 0
    visiting_wins = 0

    margin_dist = {"1": 0, "2": 0, "3-4": 0, "5+": 0}

    # Umpire aggregation
    umpire_map = {}
    total_overall_acc = 0.0
    total_ball_acc = 0.0
    total_strike_acc = 0.0
    total_missed = 0

    # Team aggregation
    team_map = {}

    # Stadium aggregation
    stadium_map = {}

    # Best / worst accuracy games
    highest_acc_game = None
    lowest_acc_game = None

    for g in games:
        h_score = int(g.get("home_score") or 0)
        v_score = int(g.get("visiting_score") or 0)
        h_team = str(g.get("home_team") or "主隊")
        v_team = str(g.get("visiting_team") or "客隊")
        stadium = str(g.get("field") or "未知球場")
        umpire = str(g.get("hp_umpire") or "未知主審")

        overall_acc = float(g.get("overall_acc") or 0.0)
        ball_acc = float(g.get("ball_acc") or 0.0)
        strike_acc = float(g.get("strike_acc") or 0.0)
        missed = int(g.get("missed_count") or 0)

        # Margins and scores
        margin = abs(h_score - v_score)
        margins.append(margin)
        w_score = max(h_score, v_score)
        l_score = min(h_score, v_score)
        winner_scores.append(w_score)
        loser_scores.append(l_score)
        total_game_runs = h_score + v_score
        total_runs_list.append(total_game_runs)

        if margin == 0:
            tie_count += 1
        elif margin == 1:
            one_run_count += 1
            margin_dist["1"] += 1
        elif margin == 2:
            margin_dist["2"] += 1
        elif margin in (3, 4):
            margin_dist["3-4"] += 1
        else:
            margin_dist["5+"] += 1

        if margin >= 5:
            blowout_count += 1

        if h_score > v_score:
            home_wins += 1
        elif v_score > h_score:
            visiting_wins += 1

        # Accuracy tracking
        total_overall_acc += overall_acc
        total_ball_acc += ball_acc
        total_strike_acc += strike_acc
        total_missed += missed

        game_acc_info = {
            "game_id": g.get("game_id"),
            "game_sno": g.get("game_sno"),
            "date": g.get("game_date"),
            "matchup": f"{v_team} vs {h_team}",
            "hp_umpire": umpire,
            "overall_acc": overall_acc,
            "missed_count": missed,
        }
        if highest_acc_game is None or overall_acc > highest_acc_game["overall_acc"]:
            highest_acc_game = game_acc_info
        if lowest_acc_game is None or overall_acc < lowest_acc_game["overall_acc"]:
            lowest_acc_game = game_acc_info

        # Umpire stats
        if umpire not in umpire_map:
            umpire_map[umpire] = {
                "name": umpire,
                "games": 0,
                "total_overall_acc": 0.0,
                "total_ball_acc": 0.0,
                "total_strike_acc": 0.0,
                "total_missed": 0,
            }
        u_entry = umpire_map[umpire]
        u_entry["games"] += 1
        u_entry["total_overall_acc"] += overall_acc
        u_entry["total_ball_acc"] += ball_acc
        u_entry["total_strike_acc"] += strike_acc
        u_entry["total_missed"] += missed

        # Team stats
        for team, is_home, scored, allowed in [
            (h_team, True, h_score, v_score),
            (v_team, False, v_score, h_score),
        ]:
            if team not in team_map:
                team_map[team] = {
                    "team": team,
                    "games": 0,
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "runs_scored": 0,
                    "runs_allowed": 0,
                    "one_run_wins": 0,
                    "one_run_losses": 0,
                    "home_games": 0,
                    "home_wins": 0,
                    "away_games": 0,
                    "away_wins": 0,
                }
            t_entry = team_map[team]
            t_entry["games"] += 1
            t_entry["runs_scored"] += scored
            t_entry["runs_allowed"] += allowed
            if is_home:
                t_entry["home_games"] += 1
            else:
                t_entry["away_games"] += 1

            if scored > allowed:
                t_entry["wins"] += 1
                if is_home:
                    t_entry["home_wins"] += 1
                else:
                    t_entry["away_wins"] += 1
                if margin == 1:
                    t_entry["one_run_wins"] += 1
            elif scored < allowed:
                t_entry["losses"] += 1
                if margin == 1:
                    t_entry["one_run_losses"] += 1
            else:
                t_entry["ties"] += 1

        # Stadium stats
        if stadium not in stadium_map:
            stadium_map[stadium] = {
                "field": stadium,
                "games": 0,
                "total_runs": 0,
                "durations": [],
                "total_acc": 0.0,
            }
        s_entry = stadium_map[stadium]
        s_entry["games"] += 1
        s_entry["total_runs"] += total_game_runs
        s_entry["total_acc"] += overall_acc
        g_dur = g.get("game_duration_minutes")
        if g_dur and g_dur > 0:
            s_entry["durations"].append(g_dur)

    # Calculate summaries
    avg_margin = round(sum(margins) / total_games, 2) if total_games > 0 else 0.0
    avg_winner_score = round(sum(winner_scores) / total_games, 2) if total_games > 0 else 0.0
    avg_loser_score = round(sum(loser_scores) / total_games, 2) if total_games > 0 else 0.0
    total_runs = sum(total_runs_list)
    avg_total_runs = round(total_runs / total_games, 2) if total_games > 0 else 0.0

    one_run_pct = round(one_run_count / total_games * 100, 1) if total_games > 0 else 0.0
    blowout_pct = round(blowout_count / total_games * 100, 1) if total_games > 0 else 0.0

    decided_games = home_wins + visiting_wins
    home_win_pct = round(home_wins / decided_games * 100, 1) if decided_games > 0 else 0.0
    visiting_win_pct = round(visiting_wins / decided_games * 100, 1) if decided_games > 0 else 0.0

    avg_overall_acc = round(total_overall_acc / total_games, 2) if total_games > 0 else 0.0
    avg_ball_acc = round(total_ball_acc / total_games, 2) if total_games > 0 else 0.0
    avg_strike_acc = round(total_strike_acc / total_games, 2) if total_games > 0 else 0.0
    avg_missed_calls = round(total_missed / total_games, 1) if total_games > 0 else 0.0

    # Build Umpire Leaderboard
    umpire_leaderboard = []
    for u in umpire_map.values():
        u_games = u["games"]
        u_overall = round(u["total_overall_acc"] / u_games, 2) if u_games > 0 else 0.0
        u_ball = round(u["total_ball_acc"] / u_games, 2) if u_games > 0 else 0.0
        u_strike = round(u["total_strike_acc"] / u_games, 2) if u_games > 0 else 0.0
        u_missed_avg = round(u["total_missed"] / u_games, 1) if u_games > 0 else 0.0
        umpire_leaderboard.append(
            {
                "hp_umpire": u["name"],
                "games": u_games,
                "overall_acc": u_overall,
                "ball_acc": u_ball,
                "strike_acc": u_strike,
                "total_missed": u["total_missed"],
                "missed_per_game": u_missed_avg,
            }
        )
    # Sort leaderboard by games DESC then overall_acc DESC
    umpire_leaderboard.sort(key=lambda x: (x["games"], x["overall_acc"]), reverse=True)

    # Build Team Standings
    team_standings = []
    for t in team_map.values():
        t_games = t["games"]
        decided = t["wins"] + t["losses"]
        win_rate = round(t["wins"] / decided, 3) if decided > 0 else 0.000
        run_diff = t["runs_scored"] - t["runs_allowed"]
        avg_rs = round(t["runs_scored"] / t_games, 2) if t_games > 0 else 0.0
        avg_ra = round(t["runs_allowed"] / t_games, 2) if t_games > 0 else 0.0
        one_run_total = t["one_run_wins"] + t["one_run_losses"]
        one_run_win_rate = round(t["one_run_wins"] / one_run_total, 3) if one_run_total > 0 else 0.000

        team_standings.append(
            {
                "team": t["team"],
                "games": t_games,
                "wins": t["wins"],
                "losses": t["losses"],
                "ties": t["ties"],
                "win_rate": win_rate,
                "win_rate_str": f"{win_rate:.3f}".lstrip("0") if win_rate < 1 else "1.000",
                "runs_scored": t["runs_scored"],
                "runs_allowed": t["runs_allowed"],
                "run_diff": run_diff,
                "avg_runs_scored": avg_rs,
                "avg_runs_allowed": avg_ra,
                "one_run_record": f"{t['one_run_wins']}勝-{t['one_run_losses']}敗",
                "one_run_win_rate": one_run_win_rate,
                "home_record": f"{t['home_wins']}勝-{t['home_games'] - t['home_wins']}敗",
                "away_record": f"{t['away_wins']}勝-{t['away_games'] - t['away_wins']}敗",
            }
        )
    # Sort teams by win_rate DESC, then run_diff DESC
    team_standings.sort(key=lambda x: (x["win_rate"], x["run_diff"]), reverse=True)

    # Build Stadium Stats
    stadium_stats = []
    for s in stadium_map.values():
        s_games = s["games"]
        s_durs = s["durations"]
        s_avg_dur = round(sum(s_durs) / len(s_durs), 1) if s_durs else 0.0
        s_avg_runs = round(s["total_runs"] / s_games, 2) if s_games > 0 else 0.0
        s_avg_acc = round(s["total_acc"] / s_games, 2) if s_games > 0 else 0.0
        stadium_stats.append(
            {
                "field": s["field"],
                "games": s_games,
                "avg_duration_minutes": s_avg_dur,
                "formatted_avg_duration": format_duration(s_avg_dur) if s_avg_dur > 0 else "無資料",
                "avg_total_runs": s_avg_runs,
                "avg_accuracy": s_avg_acc,
            }
        )
    stadium_stats.sort(key=lambda x: x["games"], reverse=True)

    return {
        "year": str(year) if year else "全部",
        "total_games": total_games,
        "duration": {
            "avg_minutes": avg_dur_mins,
            "formatted_avg": formatted_avg_dur,
            "valid_games_count": valid_dur_count,
            "shortest_game": shortest_game,
            "longest_game": longest_game,
        },
        "scores": {
            "avg_margin": avg_margin,
            "avg_winner_score": avg_winner_score,
            "avg_loser_score": avg_loser_score,
            "avg_total_runs": avg_total_runs,
            "total_runs": total_runs,
            "one_run_games_count": one_run_count,
            "one_run_games_pct": one_run_pct,
            "blowout_games_count": blowout_count,
            "blowout_games_pct": blowout_pct,
            "tie_games_count": tie_count,
            "margin_distribution": margin_dist,
        },
        "home_away": {
            "home_wins": home_wins,
            "visiting_wins": visiting_wins,
            "ties": tie_count,
            "home_win_pct": home_win_pct,
            "visiting_win_pct": visiting_win_pct,
        },
        "umpire_summary": {
            "avg_overall_acc": avg_overall_acc,
            "avg_ball_acc": avg_ball_acc,
            "avg_strike_acc": avg_strike_acc,
            "avg_missed_calls": avg_missed_calls,
            "total_missed_calls": total_missed,
            "highest_acc_game": highest_acc_game,
            "lowest_acc_game": lowest_acc_game,
        },
        "umpire_leaderboard": umpire_leaderboard,
        "team_standings": team_standings,
        "stadium_stats": stadium_stats,
    }
