from backend.profile import build_profile


def trip(i, **kw):
    base = dict(id=f"t{i}", destination="Goa", origin="Delhi", pace="relaxed", travelers=2, interests=["food", "nature"])
    base.update(kw)
    return base


def test_no_history_means_no_profile():
    assert build_profile([]) is None
    assert build_profile([trip(1, destination=None)]) is None  # a trip that never got a plan tells us nothing


def test_profile_uses_most_common_habits_and_skips_the_current_trip():
    rows = [trip(1), trip(2, origin="Mumbai"), trip(3), trip(4, pace="packed", interests=["food"])]
    p = build_profile(rows, exclude_trip_id="t3")
    assert p["origin"] == "Delhi" and p["pace"] == "relaxed" and p["travelers"] == 2
    assert p["interests"][0] == "food" and p["trips"] == 3
