""" 
GovProcureChain - Minimal Permissioned Blockchain (Educational)
- Hash-linked blocks (tamper-evident)
- Each block contains a list of events (transactions)
- Simple chain validation

NOTE: This is NOT a cryptocurrency. It's a permissioned-style audit ledger model
for government procurement transparency and compliance logging.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_json(obj: Any) -> str:
    """
    Stable JSON encoding for hashing.
    Ensures consistent field ordering.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

@dataclass(frozen=True)
class Event:
    """
    A single procurement event (transaction).
    Keep PII off-chain in real systems. For the assignment we store readable values.
    Enterprise pattern: store documents off-chain; store doc hashes + metadata on-chain.
    """
    event_type: str
    actor_role: str  # e.g., "CONTRACTING_OFFICER", "VENDOR", "QA", "FINANCE"
    actor_id: str  # e.g., "CO_001", "VENDOR_ACME"
    payload: Dict[str, Any]  # event data
    timestamp_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not d["timestamp_utc"]:
            d["timestamp_utc"] = utc_now_iso()
        return d

@dataclass
class Block:
    index: int
    timestamp_utc: str
    previous_hash: str
    events: List[Dict[str, Any]]
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        # Hash the block contents EXCEPT the hash field itself
        block_obj = {
            "index": self.index,
            "timestamp_utc": self.timestamp_utc,
            "previous_hash": self.previous_hash,
            "events": self.events,
            "nonce": self.nonce,
        }
        return sha256_hex(canonical_json(block_obj).encode("utf-8"))

class Blockchain:
    """
    Minimal blockchain for audit logging procurement events.
    """
    def __init__(self) -> None:
        self.chain: List[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            timestamp_utc=utc_now_iso(),
            previous_hash="0" * 64,
            events=[{
                "event_type": "GENESIS",
                "actor_role": "SYSTEM",
                "actor_id": "GOVPROCURECHAIN",
                "payload": {"message": "Genesis block - chain initialized"},
                "timestamp_utc": utc_now_iso(),
            }],
            nonce=0,
        )
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)

    def add_block(self, events: List[Event]) -> Block:
        """
        Add a block containing one or more events.
        """
        prev = self.chain[-1]
        event_dicts = [e.to_dict() for e in events]
        block = Block(
            index=len(self.chain),
            timestamp_utc=utc_now_iso(),
            previous_hash=prev.hash,
            events=event_dicts,
            nonce=0,
        )
        block.hash = block.compute_hash()
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        """
        Validate chain integrity: hashes and previous_hash links.
        """
        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i - 1]
            # Check link
            if cur.previous_hash != prev.hash:
                return False
            # Recompute hash
            expected = cur.compute_hash()
            if cur.hash != expected:
                return False
        return True

    def display(self, max_blocks: Optional[int] = None) -> None:
        """
        Print the chain for screenshots.
        """
        blocks = self.chain if max_blocks is None else self.chain[:max_blocks]
        for b in blocks:
            print("=" * 72)
            print(f"BLOCK #{b.index}")
            print(f"Timestamp (UTC): {b.timestamp_utc}")
            print(f"Previous Hash : {b.previous_hash}")
            print(f"Hash : {b.hash}")
            print(f"Events count : {len(b.events)}")
            for j, ev in enumerate(b.events, start=1):
                print(f"  - Event {j}: {ev['event_type']} | actor={ev['actor_role']}:{ev['actor_id']}")
                print(f"    payload: {ev['payload']}")
            print("=" * 72)
