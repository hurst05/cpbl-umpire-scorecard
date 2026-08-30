from analyzer import calculate_pitch_distance_cm, calculate_strike_zone, evaluate_pitch_call, find_similar_pitches

def test_calculate_strike_zone():
    top, bot = calculate_strike_zone(178)
    assert round(top, 3) == 0.952
    assert round(bot, 3) == 0.481

def test_evaluate_pitch_correct_strike():
    res = evaluate_pitch_call(0.0, 0.7, 0.952, 0.481, 'STRIKE')
    assert res['true_call'] == 'STRIKE'
    assert res['is_correct'] is True

def test_evaluate_pitch_missed_ball():
    res = evaluate_pitch_call(-0.06456, 0.45789, 0.9523, 0.4806, 'BALL')
    assert res['true_call'] == 'STRIKE'
    assert res['is_correct'] is False
    assert res['dist_cm'] > 0

def test_pitch_distance_and_similar_pitches():
    # Target: Batter A (165cm, sz_top=0.883, sz_bottom=0.446)
    target = {"pa_index": 1, "pitch_index": 1, "x": 0.18, "z": 1.02, "sz_top": 0.883, "sz_bottom": 0.446, "called": "STRIKE", "true_call": "BALL"}
    # Close relative pitch: Batter B (180cm, sz_top=0.963, sz_bottom=0.486) pitched at same relative height above zone top
    # Relative height of target = (1.02 - 0.446) / (0.883 - 0.446) = 0.574 / 0.437 = 1.3135
    # For Batter B: z = 0.486 + 1.3135 * (0.963 - 0.486) = 0.486 + 1.3135 * 0.477 = 1.112
    p_close_relative = {"pa_index": 2, "pitch_index": 1, "x": 0.19, "z": 1.112, "sz_top": 0.963, "sz_bottom": 0.486, "called": "BALL", "true_call": "BALL"}
    # Different physical and relative location
    p_far = {"pa_index": 3, "pitch_index": 2, "x": -0.15, "z": 0.50, "sz_top": 0.963, "sz_bottom": 0.486, "called": "BALL", "true_call": "BALL"}

    dist = calculate_pitch_distance_cm(target, p_close_relative)
    # dx = 1cm, dz ~ 0cm -> dist ~ 1.0cm
    assert 0.8 <= dist <= 1.5

    all_pitches = [target, p_close_relative, p_far]
    sim = find_similar_pitches(target, all_pitches, radius_cm=5.0)
    assert len(sim) == 1
    assert sim[0]["pa_index"] == 2
    assert sim[0]["distance_to_target_cm"] == dist


def test_analyze_game_advantage():
    from analyzer import analyze_game

    mock_raw_game = {
        "game": {
            "gameId": "2026-A-001",
            "gameSno": 1,
            "kindCode": "A",
            "preExeDate": "2026-08-30",
            "referee": [{"job": "主審", "name": "林金達"}],
            "visiting": {"team": {"name": "統一獅"}, "score": 2},
            "home": {"team": {"name": "中信兄弟"}, "score": 3},
            "liveLog": [
                # Pitch 1: 1局上, Strike called ball -> Batter favors (統一獅 / Visiting)
                {
                    "inningSeq": 1,
                    "visitingHomeType": 1,
                    "hitterAcnt": "H1",
                    "hitterName": "邱智呈",
                    "pitcherAcnt": "P1",
                    "pitcherName": "德保拉",
                    "pitchCnt": 1,
                    "ballCnt": 1,
                    "strikeCnt": 0,
                    "outCnt": 0,
                    "content": "壞球",
                    "trackman": {
                        "play": {"pitchTag": {"pitchCall": "BallCalled", "taggedPitchType": "Fastball"}},
                        "pitch": {"location": {"plateLocSide": 0.0, "plateLocHeight": 0.70}},
                    },
                },
                # Pitch 2: 1局下, Ball called strike -> Pitcher favors (統一獅 / Visiting defense)
                {
                    "inningSeq": 1,
                    "visitingHomeType": 2,
                    "hitterAcnt": "H2",
                    "hitterName": "岳政華",
                    "pitcherAcnt": "P2",
                    "pitcherName": "古林睿煬",
                    "pitchCnt": 1,
                    "ballCnt": 0,
                    "strikeCnt": 1,
                    "outCnt": 0,
                    "content": "好球沒揮棒",
                    "trackman": {
                        "play": {"pitchTag": {"pitchCall": "StrikeCalled", "taggedPitchType": "Slider"}},
                        "pitch": {"location": {"plateLocSide": 0.35, "plateLocHeight": 0.70}},
                    },
                },
            ],
        },
        "players": {},
    }

    result = analyze_game(mock_raw_game)
    metrics = result["umpire_metrics"]

    assert metrics["total_called_pitches"] == 2
    assert metrics["missed_count"] == 2
    assert metrics["visiting_favored_count"] == 2  # 1 as batter, 1 as pitcher
    assert metrics["visiting_favored_dist_cm"] > 0
    assert metrics["visiting_favored_avg_cm"] > 0
    assert metrics["home_favored_count"] == 0
    assert metrics["home_favored_dist_cm"] == 0.0
    assert "overall_consistency" in metrics
    assert "consistency_ratio_str" in metrics


def test_calculate_game_consistency():
    from analyzer import calculate_game_consistency

    # 1. Empty or single pitch
    assert calculate_game_consistency([])["consistency_rate"] == 100.0
    assert calculate_game_consistency([{"x": 0.1, "z": 0.6, "called": "STRIKE"}])["consistency_rate"] == 100.0

    # 2. Perfect consistency: 2 nearby pitches both called STRIKE
    pitches_consistent = [
        {"pa_index": 1, "pitch_index": 1, "x": 0.10, "z": 0.70, "called": "STRIKE", "sz_top": 0.95, "sz_bottom": 0.48},
        {"pa_index": 2, "pitch_index": 1, "x": 0.12, "z": 0.71, "called": "STRIKE", "sz_top": 0.95, "sz_bottom": 0.48},
        {"pa_index": 3, "pitch_index": 1, "x": -0.30, "z": 0.20, "called": "BALL", "sz_top": 0.95, "sz_bottom": 0.48},
    ]
    res = calculate_game_consistency(pitches_consistent, radius_cm=8.0)
    assert res["total_pairs"] == 1
    assert res["consistent_pairs"] == 1
    assert res["consistency_rate"] == 100.0
    assert res["ratio_str"] == "1/1"
    assert res["conflicting_pitches_count"] == 0
    assert res["isolated_count"] == 1

    # 3. Conflict: 2 nearby pitches, one STRIKE and one BALL
    pitches_conflict = [
        {"pa_index": 1, "pitch_index": 1, "x": 0.10, "z": 0.70, "called": "STRIKE", "sz_top": 0.95, "sz_bottom": 0.48},
        {"pa_index": 2, "pitch_index": 1, "x": 0.12, "z": 0.71, "called": "BALL", "sz_top": 0.95, "sz_bottom": 0.48},
    ]
    res_conflict = calculate_game_consistency(pitches_conflict, radius_cm=8.0)
    assert res_conflict["total_pairs"] == 1
    assert res_conflict["consistent_pairs"] == 0
    assert res_conflict["consistency_rate"] == 0.0
    assert res_conflict["conflicting_pitches_count"] == 2




