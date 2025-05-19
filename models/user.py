from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class UserSettings:
    payout_method: str = ""
    requisites: str = ""
    country: str = ""
    bank: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        return cls(
            payout_method=data.get('payout_method', ''),
            requisites=data.get('requisites', ''),
            country=data.get('country', ''),
            bank=data.get('bank', '')
        )

    def to_dict(self) -> Dict:
        return {
            'payout_method': self.payout_method,
            'requisites': self.requisites,
            'country': self.country,
            'bank': self.bank
        }


@dataclass
class UserStats:
    hours: float = 0.0
    amount: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserStats':
        return cls(
            hours=float(data.get('hours', 0.0)),
            amount=float(data.get('amount', 0.0))
        )

    def to_dict(self) -> Dict:
        return {
            'hours': self.hours,
            'amount': self.amount
        }


@dataclass
class User:
    id: str
    settings: UserSettings = None
    stats: UserStats = None
    is_admin: bool = False
    is_global_admin: bool = False

    def __post_init__(self):
        if self.settings is None:
            self.settings = UserSettings()
        if self.stats is None:
            self.stats = UserStats()