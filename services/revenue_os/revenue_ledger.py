from __future__ import annotations
from dataclasses import dataclass, field
from .models import MoneyState


@dataclass
class RevenueRecord:
    opportunity_id: str
    advertised_amount: float
    currency: str = "USD"
    state: MoneyState = MoneyState.ADVERTISED
    awarded_amount: float = 0.0
    paid_amount: float = 0.0
    receipts: list[str] = field(default_factory=list)

    def mark_submitted(self, receipt: str) -> None:
        if not receipt:
            raise ValueError("submission receipt required")
        self.receipts.append(receipt)
        self.state = MoneyState.SUBMITTED

    def mark_awarded(self, amount: float, receipt: str) -> None:
        if not receipt:
            raise ValueError("award receipt required")
        self.awarded_amount = amount
        self.receipts.append(receipt)
        self.state = MoneyState.AWARDED

    def mark_paid(self, amount: float, receipt: str) -> None:
        if not receipt:
            raise ValueError("payment receipt required")
        self.paid_amount = amount
        self.receipts.append(receipt)
        self.state = MoneyState.PAID
