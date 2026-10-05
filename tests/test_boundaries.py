"""Boundary tests. The rows mirror the decision table in the README."""
import pytest

from app import create_app
from udshield.engine import evaluate
from udshield.models import UtilityRecord as R


def friction(**fields):
    return evaluate("x", [R("electric", "E", **fields)], "test").friction


# (balance, days_past_due, expected friction)
BALANCE_TABLE = [
    (-25.0, None, "none"),     # credit on account
    (0.0, None, "none"),
    (0.0, 400, "none"),        # nothing owed, so age is irrelevant
    (0.01, None, "low"),
    (49.99, None, "low"),
    (50.0, None, "medium"),    # lower bound is inclusive
    (299.99, None, "medium"),
    (299.99, 59, "medium"),    # one day short of the age escalation
    (300.0, None, "high"),     # upper bound is inclusive
    (1.0, 60, "high"),         # age escalation applies to any positive balance
    (49.99, 60, "high"),
]


@pytest.mark.parametrize("balance,days,expected", BALANCE_TABLE)
def test_balance_decision_table(balance, days, expected):
    assert friction(balance_due=balance, days_past_due=days, meter_hold=False) == expected


def test_zero_deposit_is_not_a_flag():
    assert friction(balance_due=0.0, meter_hold=False, deposit_required=0.0) == "none"


def test_meter_hold_false_vs_none():
    assert friction(balance_due=0.0, meter_hold=False) == "none"
    assert friction(balance_due=0.0, meter_hold=None) == "none"  # balance known, hold unreported


def test_balance_and_hold_unknown_is_unknown():
    assert friction() == "unknown"


def test_info_flag_never_raises_friction():
    r = evaluate("x", [R("electric", "E"), R("gas", "G", balance_due=0.0)], "test")
    assert r.friction == "none"
    assert any(f.code == "BALANCE_UNAVAILABLE" for f in r.flags)


@pytest.fixture
def client():
    return create_app().test_client()


@pytest.mark.parametrize("payload", [
    {"consent": True},
    {"address": "", "consent": True},
    {"address": "   ", "consent": True},
    {"address": 123, "consent": True},
    {"address": ["a"], "consent": True},
    {"address": None, "consent": True},
])
def test_bad_address_is_400(client, payload):
    assert client.post("/v1/checks", json=payload).status_code == 400


def test_non_json_and_non_object_bodies(client):
    assert client.post("/v1/checks", data="not json", content_type="text/plain").status_code == 400
    assert client.post("/v1/checks", json=["a", "b"]).status_code == 400
