# -----------------imports----------------

from sources import kp_to_factor, calculate_score

#--------------------kp-----------------

def test_kp_to_factor():
    result = kp_to_factor(7)
    assert result == 1

#------------------score-----------------

def test_score_normal_night():
    result = calculate_score(80, 30, True, True)
    assert result == 39

def test_score_is_zero_when_fully_cloudy():
    result = calculate_score(80, 100, True, True)
    assert result == 0

def test_score_is_zero_when_not_dark():
    result = calculate_score(80, 30, False, True)
    assert result == 0