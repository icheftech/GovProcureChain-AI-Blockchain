""" 
GovProcureChain Demo App (CLI)

Scenario:
1) Contracting Officer publishes a solicitation
2) Multiple vendors submit bids (tracked)
3) System closes bidding
4) Rule-based AI evaluates bids (expert system)
5) Winner is selected (award recorded)
6) Deliverables are submitted + accepted
7) Closeout event recorded
8) Blockchain printed + validity check

Run: python app.py

Screenshot:
- Terminal output showing chain + validity True
"""

from __future__ import annotations

from blockchain import Blockchain, Event
from models import Solicitation, Vendor, Bid, Award, Deliverable, ContractLifecycle
from ai_rules import choose_winner, evaluate_bid_rules

def main() -> None:
    chain = Blockchain()

    # --- Sample data (replace with your own realistic examples) ---

    solicitation = Solicitation(
        solicitation_id="SOL-2025-001",
        agency_name="City of Houston Procurement",
        title="IT Helpdesk Support Services",
        naics="541519",
        closing_date="2025-11-12 17:00 CST",
        requirements=[
            "Provide Tier 1-2 helpdesk support",
            "Document tickets and resolution steps",
            "Meet SLA: 90% tickets resolved within 48 hours",
        ],
        status="POSTED",
    )

    vendors = [
        Vendor(
            vendor_id="VENDOR_ACME",
            legal_name="ACME Technology Solutions LLC",
            sam_registered=True,
            naics_codes=["541519", "541511"],
            insurance_valid=True,
            past_performance_score=82,
        ),
        Vendor(
            vendor_id="VENDOR_BUDGET",
            legal_name="Budget IT Pros Inc",
            sam_registered=False,  # non-compliant
            naics_codes=["541519"],
            insurance_valid=True,
            past_performance_score=70,
        ),
        Vendor(
            vendor_id="VENDOR_FAST",
            legal_name="FastTrack Systems Group",
            sam_registered=True,
            naics_codes=["541511"],  # NAICS mismatch risk
            insurance_valid=True,
            past_performance_score=55,  # low past performance
        ),
    ]

    vendors_by_id = {v.vendor_id: v for v in vendors}

    bids = [
        Bid(
            bid_id="BID-001",
            solicitation_id=solicitation.solicitation_id,
            vendor_id="VENDOR_ACME",
            price_total=120000.0,
            delivery_days=14,
            technical_compliance=True,
            notes="Meets SLA with staffed on-call rotation.",
        ),
        Bid(
            bid_id="BID-002",
            solicitation_id=solicitation.solicitation_id,
            vendor_id="VENDOR_BUDGET",
            price_total=80000.0,
            delivery_days=10,
            technical_compliance=True,
            notes="Lowest price but SAM registration missing.",
        ),
        Bid(
            bid_id="BID-003",
            solicitation_id=solicitation.solicitation_id,
            vendor_id="VENDOR_FAST",
            price_total=70000.0,
            delivery_days=3,
            technical_compliance=True,
            notes="Aggressive delivery timeline; NAICS mismatch.",
        ),
    ]

    lifecycle = ContractLifecycle(solicitation=solicitation, bids=bids)

    # --- 1) Publish solicitation (CO) ---

    chain.add_block([
        Event(
            event_type="SOLICITATION_PUBLISHED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "solicitation_id": solicitation.solicitation_id,
                "agency_name": solicitation.agency_name,
                "title": solicitation.title,
                "naics": solicitation.naics,
                "closing_date": solicitation.closing_date,
                "requirements": solicitation.requirements,
                "status": solicitation.status,
            },
        )
    ])

    # --- 2) Track bids submitted (plaintext for this version) ---

    bid_events = []
    for b in bids:
        bid_events.append(
            Event(
                event_type="BID_SUBMITTED",
                actor_role="VENDOR",
                actor_id=b.vendor_id,
                payload={
                    "bid_id": b.bid_id,
                    "solicitation_id": b.solicitation_id,
                    "vendor_id": b.vendor_id,
                    "price_total": b.price_total,
                    "delivery_days": b.delivery_days,
                    "technical_compliance": b.technical_compliance,
                    "notes": b.notes,
                },
            )
        )

    chain.add_block(bid_events)

    # --- 3) Close bidding ---

    lifecycle.state = "BIDDING_CLOSED"
    solicitation.status = "BIDDING_CLOSED"

    chain.add_block([
        Event(
            event_type="BIDDING_CLOSED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "solicitation_id": solicitation.solicitation_id,
                "status": solicitation.status,
            },
        )
    ])

    # --- 4) Evaluate bids with rule-based AI ---
    # Record each evaluation so the audit trail is transparent

    peer_prices = [b.price_total for b in bids]
    eval_events = []

    for b in bids:
        v = vendors_by_id[b.vendor_id]
        res = evaluate_bid_rules(solicitation, b, v, peer_prices)
        eval_events.append(
            Event(
                event_type="EVALUATION_RECORDED",
                actor_role="AI_RISK_ENGINE",
                actor_id="RULES_V1",
                payload={
                    "bid_id": b.bid_id,
                    "vendor_id": b.vendor_id,
                    "compliance_pass": res.compliance_pass,
                    "risk_score": res.risk_score,
                    "reasons": res.reasons,
                },
            )
        )

    chain.add_block(eval_events)

    # --- 5) Choose winner + record award ---

    winning_bid, winning_eval = choose_winner(solicitation, bids, vendors_by_id)

    award = Award(
        solicitation_id=solicitation.solicitation_id,
        winning_vendor_id=winning_bid.vendor_id,
        winning_bid_id=winning_bid.bid_id,
        award_amount=winning_bid.price_total,
        rationale="Lowest priced compliant bid. Risk reviewed and acceptable.",
    )

    lifecycle.award = award
    lifecycle.state = "AWARDED"
    solicitation.status = "AWARDED"

    chain.add_block([
        Event(
            event_type="AWARD_ISSUED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "solicitation_id": award.solicitation_id,
                "winning_vendor_id": award.winning_vendor_id,
                "winning_bid_id": award.winning_bid_id,
                "award_amount": award.award_amount,
                "rationale": award.rationale,
                "winner_risk_score": winning_eval.risk_score,
            },
        )
    ])

    # --- 6) Deliverables submitted + accepted ---

    lifecycle.state = "IN_PERFORMANCE"

    deliverables = [
        Deliverable(
            deliverable_id="DELIV-001",
            solicitation_id=solicitation.solicitation_id,
            description="Provide staffing plan + onboarding schedule",
        ),
        Deliverable(
            deliverable_id="DELIV-002",
            solicitation_id=solicitation.solicitation_id,
            description="Launch helpdesk service and meet SLA for 30 days",
        ),
    ]

    lifecycle.deliverables = deliverables

    # Submit deliverables
    chain.add_block([
        Event(
            event_type="DELIVERABLE_SUBMITTED",
            actor_role="VENDOR",
            actor_id=award.winning_vendor_id,
            payload={
                "deliverable_id": d.deliverable_id,
                "solicitation_id": d.solicitation_id,
                "description": d.description,
            },
        )
        for d in deliverables
    ])

    # Accept deliverables (agency QA/CO)
    for d in deliverables:
        d.accepted = True
        d.acceptance_notes = "Accepted - meets requirements."

    chain.add_block([
        Event(
            event_type="DELIVERABLE_ACCEPTED",
            actor_role="AGENCY_QA",
            actor_id="QA_001",
            payload={
                "deliverable_id": d.deliverable_id,
                "solicitation_id": d.solicitation_id,
                "accepted": d.accepted,
                "acceptance_notes": d.acceptance_notes,
            },
        )
        for d in deliverables
    ])

    # --- 7) Closeout (your "block closes" moment) ---

    lifecycle.state = "CLOSED"
    solicitation.status = "CLOSED"

    chain.add_block([
        Event(
            event_type="CLOSEOUT_CONFIRMED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "solicitation_id": solicitation.solicitation_id,
                "status": solicitation.status,
                "closeout_statement": "All deliverables accepted. Contract closed. Ledger remains immutable.",
                "access_model": "Government transparent oversight; vendors limited to their own bid/contract view in production (RBAC).",
            },
        )
    ])

    # --- Output for screenshots ---

    print("\nGOVPROCURECHAIN LEDGER OUTPUT (for screenshot)\n")
    chain.display()

    print(f"\nBlockchain valid: {chain.is_valid()}\n")

    print("Winner summary:")
    print(f"- Solicitation: {solicitation.solicitation_id} | {solicitation.title}")
    print(f"- Winner: {award.winning_vendor_id} | Bid: {award.winning_bid_id} | Amount: ${award.award_amount:,.2f}")

    print("\nDone.")

if __name__ == "__main__":
    main()
