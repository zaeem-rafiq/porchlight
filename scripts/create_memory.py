"""Create the Porchlight AgentCore Memory resource (P-05, one-shot). Prints ids only."""

import boto3

REGION = "us-east-1"

strategies = [
    {"userPreferenceMemoryStrategy": {
        "name": "resident_preferences",
        "description": "Per-resident contact preferences learned from triage"}},
    {"semanticMemoryStrategy": {
        "name": "org_protocol",
        "description": "Org-level protocol notes"}},
]

client = boto3.client("bedrock-agentcore-control", region_name=REGION)
mem = client.create_memory(
    name="porchlight",
    description="Porchlight resident preferences + org protocol",
    memoryExecutionRoleArn="arn:aws:iam::292341338711:role/porchlight-memory-role",
    eventExpiryDuration=90,
    memoryStrategies=strategies,
    tags={"project": "porchlight"},
)["memory"]
print("memory=" + mem["id"] + " status=" + mem["status"])
for s in mem.get("memoryStrategies", []):
    print("strategy=" + str(s.get("memoryStrategyId")) + " name=" + str(
        (s.get("customMemoryStrategy") or {}).get("name")))
