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


