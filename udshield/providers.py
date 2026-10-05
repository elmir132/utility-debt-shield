"""Data sources.

Only `MockProvider` exists. It returns fictional, deterministic data so the API and
the rules can be demonstrated and tested. A real provider would implement `fetch`
against a utility-data aggregator; that needs the account holder's consent and the
available fields differ by aggregator (some expose no balance or past-due data).
No real aggregator is integrated in this repository.
"""
import hashlib
from typing import List

from .models import UtilityRecord


class Provider:
    name = "base"

    def fetch(self, address: str) -> List[UtilityRecord]:
        raise NotImplementedError


# Fictional scenarios. Every name and figure here is invented.
SCENARIOS = {
    "clean": [
        UtilityRecord("electric", "Example Power Co", balance_due=0.0, meter_hold=False),
        UtilityRecord("gas", "Example Gas Co", balance_due=0.0, meter_hold=False),
    ],
    "small_balance": [
        UtilityRecord("electric", "Example Power Co", balance_due=34.18, days_past_due=12, meter_hold=False),
        UtilityRecord("gas", "Example Gas Co", balance_due=0.0, meter_hold=False),
    ],
    "arrears_and_hold": [
        UtilityRecord("electric", "Example Power Co", balance_due=340.18, days_past_due=75, meter_hold=True),
        UtilityRecord("gas", "Example Gas Co", balance_due=0.0, meter_hold=False, deposit_required=150.0),
    ],
    "no_balance_data": [
        UtilityRecord("electric", "Example Power Co"),
        UtilityRecord("gas", "Example Gas Co"),
    ],
}

# Fixed demo addresses so docs and tests are reproducible
DEMO_ADDRESSES = {
    "1 demo street, example city": "clean",
    "2 demo street, example city": "small_balance",
    "3 demo street, example city": "arrears_and_hold",
    "4 demo street, example city": "no_balance_data",
}


class MockProvider(Provider):
    name = "mock"

    def fetch(self, address: str) -> List[UtilityRecord]:
        key = address.strip().lower()
        scenario = DEMO_ADDRESSES.get(key)
        if scenario is None:  # stable pseudo-random pick for any other address
            names = sorted(SCENARIOS)
            scenario = names[int(hashlib.sha256(key.encode()).hexdigest(), 16) % len(names)]
        return [UtilityRecord(**r.__dict__) for r in SCENARIOS[scenario]]
