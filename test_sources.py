# -----------------imports----------------

import sources
from sources import kp_to_factor, calculate_score, get_tips, find_best_hour


#---------------MonkeyPatch-------------

class FakeResponse:
    def __init__(self, answer):
        self.answer = answer

    def raise_for_status(self):
        pass                        # pretend: no error

    def json(self):
        return self.answer

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

#----------------- hour---------------------

def test_best_hour_picks_highest_score():
    hour1 = {"time": "23:00", "score": 10}
    hour3 = {"time": "2:00", "score": 70}
    hour2 = {"time": "00:00", "score": 40}

    assert find_best_hour([hour1, hour2, hour3]) == hour3


def test_best_hour_of_empty_night_is_none():
    # in summer, it never gets dark, so get_tonight returns []
    assert find_best_hour([]) is None

#------------------tips---------------------

def test_storm_gusts_give_a_storm_tip():
    hour = {"time": "23:00", "score": 10, "gusts": 20, "snow": 0, "rain": 0}
    tips = get_tips(hour, False)
    assert "Storm" in tips[1]


def test_windy_gusts_give_a_car_door_tip():
    hour = {"time": "23:00", "score": 10, "gusts": 15, "snow": 0, "rain": 0}
    tips = get_tips(hour, False)
    assert "car" in tips[1]

#------------------place (fake internet)-----------------

def test_find_place_returns_coordinates(monkeypatch):
    vik = FakeResponse({"results": [{"latitude": 63.4, "longitude": -19.0}]})

    def fake_get(url, params,timeout):
        return vik

    monkeypatch.setattr(sources.httpx, "get", fake_get)
    assert sources.find_place("vik") == (63.4, -19.0)

def test_find_place_unknown_returns_none(monkeypatch):
    wrong_place = FakeResponse({"results": []})
    def fake_wrong(url,params,timeout):
        return wrong_place

    monkeypatch.setattr(sources.httpx, "get", fake_wrong)
    assert sources.find_place("Narnia") is None
