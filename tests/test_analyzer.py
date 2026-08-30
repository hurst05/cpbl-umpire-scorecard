from analyzer import calculate_strike_zone, evaluate_pitch_call

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
