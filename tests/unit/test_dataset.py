from agent.data import find_origin, load_dataset, match_destinations
from agent.models import INTERESTS


def test_dataset_loads_and_is_consistent():
    ds = load_dataset()
    assert len(ds.destinations) >= 10
    ids = [d.id for d in ds.destinations]
    assert len(ids) == len(set(ids))
    for d in ds.destinations:
        assert len(d.attractions) >= 8 and len(d.restaurants) >= 7
        att_ids = [a.id for a in d.attractions] + [r.id for r in d.restaurants]
        assert len(att_ids) == len(set(att_ids)), d.id
        assert all(t in INTERESTS for a in d.attractions for t in a.themes), d.id
        assert set(d.stay) == {"budget", "mid", "premium"}
        assert set(ds.origins) == set(d.transport_from), d.id
        assert all(opts for opts in d.transport_from.values())
        assert any("lunch" in r.meals for r in d.restaurants)
        assert any("dinner" in r.meals for r in d.restaurants)


def test_origin_aliases_resolve():
    assert find_origin("Bangalore").name == "Bengaluru"
    assert find_origin("  new delhi ").name == "Delhi"
    assert find_origin("Atlantis") is None
    assert find_origin(None) is None


def test_destination_matching_by_name_alias_and_region():
    assert [d.id for d in match_destinations("Munnar")] == ["kerala"]
    assert {d.id for d in match_destinations("Rajasthan")} == {"jaipur", "udaipur"}
    assert match_destinations("Paris") == []
    assert match_destinations("") == []
    assert match_destinations("../../etc/passwd") == []
