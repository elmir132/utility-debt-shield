"""Deterministic activation-friction rules.

What this measures, and what it does not: a balance, shut-off or meter hold on the
account tied to an address can delay or block a new tenant from turning service on
(deposits, disputes, a technician visit). It does NOT mean the new tenant inherits
the debt: utility debt generally follows the account holder, not the address.
The output is worded accordingly.
"""
from typing import List

from .models import CheckResult, Flag, UtilityRecord

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}

# Balance thresholds in USD
LOW_BALANCE = 50.0
HIGH_BALANCE = 300.0
# Past this many days overdue, a balance is treated as a collections risk
SERIOUS_DAYS_PAST_DUE = 60


def _balance_flag(rec: UtilityRecord):
    if rec.balance_due is None:
        return Flag("BALANCE_UNAVAILABLE", "info", rec.utility,
                    f"{rec.provider_name} did not report a balance for this account.")
    if rec.balance_due <= 0:
        return None
    if rec.balance_due >= HIGH_BALANCE or (rec.days_past_due or 0) >= SERIOUS_DAYS_PAST_DUE:
        severity = "high"
    elif rec.balance_due >= LOW_BALANCE:
        severity = "medium"
    else:
        severity = "low"
    overdue = f", {rec.days_past_due} days past due" if rec.days_past_due else ""
    return Flag("BALANCE_ON_ACCOUNT", severity, rec.utility,
                f"Unpaid balance of ${rec.balance_due:,.2f} on the {rec.utility} account{overdue}.")


def evaluate(address: str, records: List[UtilityRecord], data_source: str) -> CheckResult:
    flags: List[Flag] = []
    for rec in records:
        bal = _balance_flag(rec)
        if bal:
            flags.append(bal)
        if rec.meter_hold:
            flags.append(Flag("METER_HOLD", "high", rec.utility,
                              f"{rec.provider_name} has a hold on the {rec.utility} meter; "
                              "activation may need a technician visit."))
        if rec.deposit_required:
            flags.append(Flag("DEPOSIT_REQUIRED", "medium", rec.utility,
                              f"A deposit of ${rec.deposit_required:,.2f} may be required to activate "
                              f"{rec.utility} service."))

    real = [f for f in flags if f.severity != "info"]
    if real:
        friction = max((f.severity for f in real), key=SEVERITY_ORDER.get)
    elif not records or all(r.balance_due is None and r.meter_hold is None for r in records):
        friction = "unknown"
    else:
        friction = "none"

    return CheckResult(address=address, data_source=data_source, friction=friction,
                       flags=flags, notice=_notice(friction))


def _notice(friction: str) -> str:
    return {
        "none": "No activation obstacles found in the data available.",
        "low": "Minor items found. Service activation is unlikely to be blocked.",
        "medium": "Activation may require a deposit or payment. Tell the renter before they sign.",
        "high": "Activation may be delayed or blocked. Tell the renter before they sign. "
                "This does not by itself mean the renter owes the balance.",
        "unknown": "The data source did not return enough information to assess this address.",
    }[friction]
