from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class UtilityRecord:
    """What a data source reports about one utility account at an address.

    Any field except `utility` may be None: aggregators do not expose every field
    (for example, some bill APIs return no balance or past-due amount at all).
    """
    utility: str                              # "electric" | "gas" | "water"
    provider_name: str
    balance_due: Optional[float] = None       # USD
    days_past_due: Optional[int] = None
    meter_hold: Optional[bool] = None
    deposit_required: Optional[float] = None  # USD


@dataclass
class Flag:
    code: str
    severity: str      # "info" | "low" | "medium" | "high"
    utility: str
    message: str


@dataclass
class CheckResult:
    address: str
    data_source: str
    friction: str      # "none" | "low" | "medium" | "high" | "unknown"
    flags: List[Flag] = field(default_factory=list)
    notice: str = ""

    def to_dict(self):
        return asdict(self)
