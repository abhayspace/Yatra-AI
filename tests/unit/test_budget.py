import pytest

from agent.errors import ToolError
from agent.tools.budget import BudgetInput, compute_budget, parse_amount


def base(**kw):
    d = dict(transport=10000, stay=15000, food=8000, activities=5000, local_transport=2000, travelers=2, budget=50000)
    d.update(kw)
    return d


def test_sums_components_and_per_person():
    r = compute_budget(base())
    assert r.total == 40000
    assert r.per_person == 20000
    assert r.remaining == 10000
    assert r.status == "within_budget"
    assert r.breakdown_pct["stay"] == 37.5


def test_tight_when_above_95_percent():
    r = compute_budget(base(budget=41000))
    assert r.status == "tight" and r.remaining == 1000


def test_over_budget_reports_overage_and_suggestion():
    r = compute_budget(base(budget=30000))
    assert r.status == "over_budget"
    assert r.overage == 10000
    assert r.suggestions and "Stay" in r.suggestions[0]


def test_no_budget_given():
    r = compute_budget(base(budget=None))
    assert r.status == "no_budget_given" and r.remaining is None


@pytest.mark.parametrize(
    "raw,expected",
    [("50000", 50000), ("₹50,000", 50000), ("50k", 50000), ("1.5 lakh", 150000), ("Rs. 2,500", 2500), (1200, 1200), (99.5, 99.5)],
)
def test_parse_amount_accepts_plain_numbers(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "__import__('os').system('echo hacked')",
        "50000; DROP TABLE trips",
        "1e999",
        "nan",
        "inf",
        "-5",
        "10**9",
        "2+2",
        "٣٠٠٠",  # non-ASCII digits
        "",
        None,
        [1],
        True,
        10**12,
    ],
)
def test_parse_amount_rejects_adversarial_input(raw):
    with pytest.raises(ToolError):
        parse_amount(raw)


def test_compute_budget_fails_safely_on_injection_string():
    with pytest.raises(ToolError) as exc:
        compute_budget(base(stay="__import__('os').getcwd()"))
    assert "stay" in str(exc.value)


def test_compute_budget_never_evaluates_code(monkeypatch):
    import builtins

    def boom(*a, **k):
        raise AssertionError("eval/exec must never be called")

    monkeypatch.setattr(builtins, "eval", boom)
    monkeypatch.setattr(builtins, "exec", boom)
    assert compute_budget(base(transport="5,000")).components.transport == 5000


def test_negative_and_huge_values_rejected():
    with pytest.raises(ToolError):
        compute_budget(base(food=-1))
    with pytest.raises(ToolError):
        compute_budget(base(travelers=0))
    with pytest.raises(ToolError):
        compute_budget(base(travelers="2; rm -rf /"))
    assert BudgetInput.model_validate(base(travelers="3")).travelers == 3
