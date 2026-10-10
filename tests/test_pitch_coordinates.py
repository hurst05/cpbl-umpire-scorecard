from copy import deepcopy

import pytest
from analyzer import analyze_game, evaluate_pitch_call


@pytest.fixture
def playoff_pitch():
    # 2026-E-2, PA 38: official pitch 4 (event 6), Chen Chung-Yu vs. Felix.
    return {
        "location": {
            "zoneTime": 0.435337,
            "plateLocSide": -0.104177592,
            "plateLocHeight": 0.470349072,
        },
        "flight": {
            "polyFit": {
                "pitchTrajectory": {
                    "x": [16.734214944, -39.55574004, 4.853626056],
                    "y": [1.97803008, -2.673208776, -1.810640016],
                    "z": [-0.573179448, 2.342269128, -1.812252408],
                }
            }
        },
    }


def analyze_pitch(pitch):
    game = {
        "gameId": "2026-E-2",
        "visiting": {"team": {"name": "中信兄弟"}},
        "home": {"team": {"name": "統一7-ELEVEn獅"}},
        "liveLog": [
            {
                "inningSeq": 5,
                "visitingHomeType": "2",
                "hitterAcnt": "0000002298",
                "content": "好球沒揮棒。",
                "trackman": {"play": {"pitchTag": {"pitchCall": "StrikeCalled"}}, "pitch": pitch},
            }
        ],
    }
    return analyze_game(game, {"0000002298": {"height": 183}})


def test_playoff_pitch_matches_official_plate_middle_position(playoff_pitch):
    result = analyze_pitch(playoff_pitch)
    pitch = result["all_called_pitches"][0]
    assert pitch["x"] == pytest.approx(-0.10878)
    assert pitch["z"] == pytest.approx(0.44429)
    assert pitch["true_call"] == "BALL"
    assert pitch["is_correct"] is False
    assert pitch["dist_cm"] == 1.29
    assert pitch["favored_team"] == "中信兄弟"
    pa_pitch = result["plate_appearances"][0]["pitches"][0]
    assert (pa_pitch["x"], pa_pitch["z"]) == (-0.1088, 0.4443)
    assert pa_pitch["true_call"] == "BALL"


@pytest.mark.parametrize("side", [-0.254, 0.254])
def test_call_uses_official_43_16_cm_zone_width(side):
    assert evaluate_pitch_call(side, 0.7, 0.97905, 0.4941, "STRIKE")["true_call"] == "BALL"


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("location", "zoneTime", None),
        ("location", "plateLocSide", float("nan")),
        ("location", "plateLocHeight", "0.47"),
        ("pitchTrajectory", "x", [16.7, -39.5]),
        ("pitchTrajectory", "y", [1.9, float("inf"), -1.8]),
        ("pitchTrajectory", "z", [0.0, False, 0.0]),
        ("pitchTrajectory", "x", [0.4, -40.0, 0.0]),
        ("pitchTrajectory", "x", [16.7, 0.0, 0.0]),
        ("pitchTrajectory", "x", [16.7, 1.0, 1.0]),
    ],
)
def test_invalid_trajectory_has_no_position_or_evaluation(playoff_pitch, section, key, value):
    pitch = deepcopy(playoff_pitch)
    target = pitch["location"] if section == "location" else pitch["flight"]["polyFit"]["pitchTrajectory"]
    target[key] = value
    result = analyze_pitch(pitch)
    assert result["all_called_pitches"] == []
    pa_pitch = result["plate_appearances"][0]["pitches"][0]
    assert pa_pitch["x"] is None and pa_pitch["z"] is None
    assert pa_pitch["true_call"] is None


def test_missing_trajectory_does_not_use_front_coordinates(playoff_pitch):
    del playoff_pitch["flight"]
    result = analyze_pitch(playoff_pitch)
    assert result["all_called_pitches"] == []
    assert result["plate_appearances"][0]["pitches"][0]["x"] is None


def test_linear_trajectory_preserves_calibration():
    pitch = {
        "location": {"zoneTime": 0.4, "plateLocSide": 0.15, "plateLocHeight": 0.7},
        "flight": {
            "polyFit": {"pitchTrajectory": {"x": [16.0, -40.0, 0.0], "y": [3.0, -2.0, 0.0], "z": [2.0, 1.0, 0.0]}}
        },
    }
    result = analyze_pitch(pitch)["all_called_pitches"][0]
    assert result["x"] == pytest.approx(0.1446)
    assert result["z"] == pytest.approx(0.68921)
