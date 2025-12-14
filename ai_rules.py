""" 
Rule-Based AI (Expert System) for procurement risk & compliance.

Why this counts as "AI":
- Rule-based systems are classic AI ("expert systems")
- Explainable scoring is especially appropriate for government compliance contexts

We produce:
- compliance_pass (bool)
- risk_score (0-100)
- reasons (list of strings)
"""

from __future__ import annotations
from dataclasses import dataclass
from statistics import median
from typing import Dict, List, Tuple

from models import Bid, Vendor, Solicitation

@dataclass
class RiskResult:
    compliance_pass: bool
    risk_score: int
    reasons: List[str]

def evaluate_bid_rules(
    solicitation: Solicitation,
    bid: Bid,
    vendor: Vendor,
    peer_prices: List[float],
) -> RiskResult:
    reasons: List[str] = []
    risk = 0
    compliance_pass = True

    # --- Hard compliance gates (fail = do not advance automatically) ---

    if bid.solicitation_id != solicitation.solicitation_id:
        compliance_pass = False
        reasons.append("Bid does not match solicitation_id.")
        risk += 60

    if not vendor.sam_registered:
        compliance_pass = False
        reasons.append("Vendor is NOT SAM-registered.")
        risk += 50

    if not vendor.insurance_valid:
        compliance_pass = False
        reasons.append("Vendor insurance is NOT valid.")
        risk += 40

    if solicitation.naics not in vendor.naics_codes:
        # Not always an absolute fail in real life, but it's a major risk signal.
        reasons.append("Vendor NAICS codes do not include solicitation NAICS.")
        risk += 20

    if not bid.technical_compliance:
        compliance_pass = False
        reasons.append("Bid marked technically non-compliant (fails requirements).")
        risk += 50

    # --- Soft risk signals (explainable) ---

    # Past performance
    if vendor.past_performance_score < 60:
        reasons.append("Low past performance score (<60).")
        risk += 25
    elif vendor.past_performance_score < 75:
        reasons.append("Moderate past performance score (60-74).")
        risk += 10

    # Delivery time risk
    if bid.delivery_days <= 3:
        reasons.append("Very aggressive delivery timeline (<=3 days).")
        risk += 15
    elif bid.delivery_days > 60:
        reasons.append("Very long delivery timeline (>60 days).")
        risk += 10

    # Price outlier analysis vs peers
    if peer_prices:
        m = median(peer_prices)
        if bid.price_total < 0.7 * m:
            reasons.append("Price is unusually low (<70% of median) \u2014 potential underbid risk.")
            risk += 20
        elif bid.price_total > 1.5 * m:
            reasons.append("Price is unusually high (>150% of median).")
            risk += 10

    # Clamp 0-100
    risk = max(0, min(100, risk))

    return RiskResult(compliance_pass=compliance_pass, risk_score=risk, reasons=reasons)

def choose_winner(
    solicitation: Solicitation,
    bids: List[Bid],
    vendors_by_id: Dict[str, Vendor],
) -> Tuple[Bid, RiskResult]:
    """
    Simple winner logic:
    - Only consider bids that pass compliance gates
    - Among compliant bids, choose lowest price
    - Return winner + its risk evaluation (for audit trace)

    In real procurement, evaluation is multi-factor (technical, price realism, past performance).
    """
    peer_prices = [b.price_total for b in bids]
    scored: List[Tuple[Bid, RiskResult]] = []

    for b in bids:
        v = vendors_by_id[b.vendor_id]
        res = evaluate_bid_rules(solicitation, b, v, peer_prices)
        scored.append((b, res))

    compliant = [(b, r) for (b, r) in scored if r.compliance_pass]

    if not compliant:
        # Fallback: choose lowest risk among all, but flag that none were compliant.
        # For assignment clarity, we'll raise.
        raise ValueError("No compliant bids available. Manual contracting officer review required.")

    # Choose lowest price among compliant bids (simple)
    compliant.sort(key=lambda x: x[0].price_total)
    return compliant[0]
