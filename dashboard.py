from flask import Flask, render_template, jsonify
from blockchain import Blockchain, Event
from models import Solicitation, Vendor, Bid, Award, Deliverable
from ai_rules import choose_winner, evaluate_bid_rules
import json
from datetime import datetime

app = Flask(__name__)

# Global blockchain instance
chain = Blockchain()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/blockchain')
def get_blockchain():
    """Return the entire blockchain as JSON"""
    blocks_data = []
    for block in chain.chain:
        blocks_data.append({
            'index': block.index,
            'timestamp': block.timestamp_utc,
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'events': block.events,
            'event_count': len(block.events)
        })
    
    return jsonify({
        'blocks': blocks_data,
        'total_blocks': len(chain.chain),
        'is_valid': chain.is_valid()
    })

@app.route('/api/stats')
def get_stats():
    """Return blockchain statistics"""
    total_events = sum(len(block.events) for block in chain.chain)
    
    event_types = {}
    for block in chain.chain:
        for event in block.events:
            evt_type = event.get('event_type', 'UNKNOWN')
            event_types[evt_type] = event_types.get(evt_type, 0) + 1
    
    return jsonify({
        'total_blocks': len(chain.chain),
        'total_events': total_events,
        'event_types': event_types,
        'is_valid': chain.is_valid()
    })

@app.route('/api/simulate', methods=['POST'])
def simulate_procurement():
    """Simulate a full procurement cycle"""
    
    # Create sample data
    solicitation = Solicitation(
        solicitation_id="SOL-DEMO-001",
        agency_name="City of Houston IT Department",
        title="Cloud Infrastructure Services",
        naics="541519",
        closing_date="2025-12-31 17:00 CST",
        requirements=["24/7 support", "99.9% uptime SLA", "Federal compliance"],
        status="POSTED"
    )
    
    vendors = [
        Vendor(
            vendor_id="VENDOR_ALPHA",
            legal_name="Alpha Tech Solutions LLC",
            sam_registered=True,
            naics_codes=["541519", "541511"],
            insurance_valid=True,
            past_performance_score=85
        ),
        Vendor(
            vendor_id="VENDOR_BETA",
            legal_name="Beta Cloud Services Inc",
            sam_registered=True,
            naics_codes=["541519"],
            insurance_valid=True,
            past_performance_score=72
        )
    ]
    
    vendors_by_id = {v.vendor_id: v for v in vendors}
    
    bids = [
        Bid(
            bid_id="BID-ALPHA-001",
            solicitation_id=solicitation.solicitation_id,
            vendor_id="VENDOR_ALPHA",
            price_total=150000.0,
            delivery_days=30,
            technical_compliance=True,
            notes="Full cloud migration with support"
        ),
        Bid(
            bid_id="BID-BETA-001",
            solicitation_id=solicitation.solicitation_id,
            vendor_id="VENDOR_BETA",
            price_total=130000.0,
            delivery_days=45,
            technical_compliance=True,
            notes="Phased deployment approach"
        )
    ]
    
    # 1. Publish solicitation
    chain.add_block([
        Event(
            event_type="SOLICITATION_PUBLISHED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "solicitation_id": solicitation.solicitation_id,
                "agency_name": solicitation.agency_name,
                "title": solicitation.title,
                "naics": solicitation.naics
            }
        )
    ])
    
    # 2. Submit bids
    bid_events = []
    for bid in bids:
        bid_events.append(
            Event(
                event_type="BID_SUBMITTED",
                actor_role="VENDOR",
                actor_id=bid.vendor_id,
                payload={
                    "bid_id": bid.bid_id,
                    "price_total": bid.price_total,
                    "delivery_days": bid.delivery_days
                }
            )
        )
    chain.add_block(bid_events)
    
    # 3. Close bidding
    chain.add_block([
        Event(
            event_type="BIDDING_CLOSED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={"solicitation_id": solicitation.solicitation_id}
        )
    ])
    
    # 4. AI Evaluation
    peer_prices = [b.price_total for b in bids]
    eval_events = []
    for bid in bids:
        v = vendors_by_id[bid.vendor_id]
        res = evaluate_bid_rules(solicitation, bid, v, peer_prices)
        eval_events.append(
            Event(
                event_type="EVALUATION_RECORDED",
                actor_role="AI_RISK_ENGINE",
                actor_id="RULES_V1",
                payload={
                    "bid_id": bid.bid_id,
                    "compliance_pass": res.compliance_pass,
                    "risk_score": res.risk_score
                }
            )
        )
    chain.add_block(eval_events)
    
    # 5. Award
    winning_bid, winning_eval = choose_winner(solicitation, bids, vendors_by_id)
    chain.add_block([
        Event(
            event_type="AWARD_ISSUED",
            actor_role="CONTRACTING_OFFICER",
            actor_id="CO_001",
            payload={
                "winning_vendor_id": winning_bid.vendor_id,
                "award_amount": winning_bid.price_total,
                "risk_score": winning_eval.risk_score
            }
        )
    ])
    
    return jsonify({"status": "success", "blocks_created": 5})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
