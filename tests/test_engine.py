from udshield.engine import evaluate
from udshield.models import UtilityRecord as R


def run(*records):
    return evaluate("x", list(records), "test")


def test_clean_accounts_have_no_friction():
    r = run(R("electric", "E", balance_due=0.0, meter_hold=False))
    assert r.friction == "none" and r.flags == []


def test_small_balance_is_low():
    assert run(R("electric", "E", balance_due=20.0, meter_hold=False)).friction == "low"


def test_mid_balance_is_medium():
    assert run(R("electric", "E", balance_due=120.0, meter_hold=False)).friction == "medium"


def test_large_balance_is_high():
    assert run(R("electric", "E", balance_due=300.0, meter_hold=False)).friction == "high"


def test_old_small_balance_escalates_to_high():
    r = run(R("electric", "E", balance_due=60.0, days_past_due=90, meter_hold=False))
    assert r.friction == "high"


def test_meter_hold_alone_is_high():
    assert run(R("gas", "G", balance_due=0.0, meter_hold=True)).friction == "high"


def test_deposit_is_medium():
    assert run(R("gas", "G", balance_due=0.0, meter_hold=False, deposit_required=100.0)).friction == "medium"


def test_worst_flag_wins_across_utilities():
    r = run(R("electric", "E", balance_due=20.0, meter_hold=False),
            R("gas", "G", balance_due=0.0, meter_hold=True))
    assert r.friction == "high"


def test_missing_data_is_unknown_not_none():
    r = run(R("electric", "E"), R("gas", "G"))
    assert r.friction == "unknown"
    assert {f.code for f in r.flags} == {"BALANCE_UNAVAILABLE"}


def test_no_records_is_unknown():
    assert run().friction == "unknown"


def test_partial_data_with_clean_balance_is_none():
    r = run(R("electric", "E", balance_due=0.0), R("gas", "G"))
    assert r.friction == "none"


def test_high_notice_does_not_claim_renter_owes_debt():
    r = run(R("electric", "E", balance_due=500.0, meter_hold=False))
    assert "does not by itself mean the renter owes" in r.notice
