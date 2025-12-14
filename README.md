# GovProcureChain (Assignment Project)
AI + Blockchain for Government Procurement Transparency

## What it does
GovProcureChain is a simple, permissioned-style blockchain ledger that tracks the full lifecycle of a government solicitation:

1) Contracting Officer publishes a solicitation  
2) Vendors submit bids (tracked)  
3) Bidding closes  
4) "AI" Risk Engine (Rule-Based Expert System) evaluates bids for compliance/risk  
5) Contract award is recorded  
6) Deliverables are submitted and accepted  
7) Contract closeout is recorded (immutable audit trail)

The ledger is tamper-evident (hash-linked blocks) and can support transparency for public agencies while enforcing private access controls for vendors in a real deployment.

## Why the AI is valid
This project uses a **Rule-Based AI Risk Engine (Expert System)**:
- Rule-based systems are a classic form of AI.
- Explainable scoring is appropriate for government compliance/auditing.
- The system produces an auditable risk score + reasons for each bid.

## Compliance & Security Notes (Enterprise-minded)
- Real systems keep PII and large documents off-chain; store hashes + metadata on-chain.
- Real systems enforce RBAC (role-based access control) and encryption at rest/in transit.
- This demo models the audit ledger layer that supports FAR/DFARS style lifecycle events.

## Files
- `blockchain.py` : minimal blockchain + validation
- `models.py` : solicitation/vendor/bid/award/deliverable models
- `ai_rules.py` : rule-based AI risk engine + winner selection
- `app.py` : end-to-end CLI demo (run for screenshots)

## How to run
Requires Python 3.9+ (no external dependencies).

```bash
python app.py

