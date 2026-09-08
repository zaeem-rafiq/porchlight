"""AgentCore Memory tools (P-05): per-resident preferences + org protocol.

Namespaces: /org/{orgId}/protocol and /resident/{residentId}/preferences.
Written from triage outcomes; read back by conversation agents and the board.
Memory resource id comes from MEMORY_ID (deployed once, proof in P-05).
"""

from __future__ import annotations

import os

ORG_ID = "porchlight"

NAMESPACE_PROTOCOL = f"/org/{ORG_ID}/protocol"
NAMESPACE_RESIDENT = "/resident/{resident_id}/preferences"


def _client(region: str):
    import boto3

    return boto3.client("bedrock-agentcore", region_name=region or None)


def memory_id() -> str:
    return os.environ.get("MEMORY_ID", "")


import time
import uuid


def _record(text: str, namespace: str) -> dict:
    return {"requestIdentifier": str(uuid.uuid4()), "namespaces": [namespace],
            "content": {"text": text},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def write_preference(resident_id: str, text: str, region: str = "") -> str:
    client = _client(region)
    res = client.batch_create_memory_records(
        memoryId=memory_id(),
        records=[_record(text, NAMESPACE_RESIDENT.format(resident_id=resident_id))])
    return str(res)


def write_protocol_note(text: str, region: str = "") -> str:
    client = _client(region)
    res = client.batch_create_memory_records(
        memoryId=memory_id(), records=[_record(text, NAMESPACE_PROTOCOL)])
    return str(res)


def retrieve(namespace: str, query: str, region: str = "", top_k: int = 5) -> list[dict]:
    client = _client(region)
    res = client.retrieve_memory_records(
        memoryId=memory_id(), namespace=namespace,
        searchCriteria={"searchQuery": query, "topK": top_k}, maxResults=top_k)
    return res.get("memoryRecordSummaries", res.get("records", []))


def preference_from_triage(resident: dict, triage) -> str:
    bits = [resident.get("name", "?"), f"lang={resident.get('language')}",
            f"channel={resident.get('preferred_channel')}"]
    if resident.get("powered_medical_device"):
        bits.append(f"device={resident['powered_medical_device']}")
    if resident.get("notes"):
        bits.append(resident["notes"][:100])
    bits.append(f"last_triage={triage.status}/{triage.need}")
    return "; ".join(bits)
