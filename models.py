""" 
Data models for GovProcureChain (simple, readable, assignment-friendly)

Real deployments would enforce stricter schemas, signatures, encryption, RBAC, etc.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Solicitation:
    solicitation_id: str
    agency_name: str
    title: str
    naics: str
    closing_date: str  # simple string for assignment
    requirements: List[str] = field(default_factory=list)
    status: str = "POSTED"  # POSTED -> BIDDING_CLOSED -> AWARDED -> CLOSED

@dataclass
class Vendor:
    vendor_id: str
    legal_name: str
    sam_registered: bool
    naics_codes: List[str]
    insurance_valid: bool
    past_performance_score: int  # 0-100

@dataclass
class Bid:
    bid_id: str
    solicitation_id: str
    vendor_id: str
    price_total: float
    delivery_days: int
    technical_compliance: bool
    notes: str = ""

@dataclass
class Award:
    solicitation_id: str
    winning_vendor_id: str
    winning_bid_id: str
    award_amount: float
    rationale: str

@dataclass
class Deliverable:
    deliverable_id: str
    solicitation_id: str
    description: str
    accepted: bool = False
    acceptance_notes: str = ""

@dataclass
class ContractLifecycle:
    """
    Tracks state for one solicitation/contract lifecycle.
    """
    solicitation: Solicitation
    bids: List[Bid] = field(default_factory=list)
    award: Optional[Award] = None
    deliverables: List[Deliverable] = field(default_factory=list)
    state: str = "BIDDING_OPEN"  # BIDDING_OPEN -> BIDDING_CLOSED -> AWARDED -> IN_PERFORMANCE -> CLOSED
