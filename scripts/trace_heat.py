"""Render docs/media/trace-heat.png: span bars from real CloudWatch timestamps (P-05)."""

import boto3
import time
from PIL import Image, ImageDraw

REGION = "us-east-1"
RT_GROUP = "/aws/bedrock-agentcore/runtimes/porchlight_porchlight-RSlQTA9oTe-DEFAULT"
LAMBDA_GROUP = "/aws/lambda/porchlight-glue-TwilioInbound-nNEjgRJsVE3t"

logs = boto3.client("logs", region_name=REGION)
now = int(time.time())


def fetch(group, minutes, query):
    q = logs.start_query(logGroupName=group, startTime=now - minutes * 60,
                         endTime=now, queryString=query)["queryId"]
    time.sleep(10)
    return logs.get_query_results(queryId=q)["results"]


spans = []
rows = fetch(RT_GROUP, 180, "fields @timestamp, @message | sort @timestamp asc | limit 200")
for r in rows:
    ts = next((f["value"] for f in r if f["field"] == "@timestamp"), "")
    msg = next((f["value"] for f in r if f["field"] == "@message"), "")
    label = None
    for key in ["wave sent n=", "triage:", "gate_hold", "coordinator_ping",
                "coordinator_approved", "Invocation failed", "START RequestId",
                "dispatch"]:
        if key in msg:
            label = key
            break
    if label:
        spans.append((ts, label))
rows = fetch(LAMBDA_GROUP, 180, "fields @timestamp, @message | sort @timestamp asc | limit 50")
for r in rows:
    ts = next((f["value"] for f in r if f["field"] == "@timestamp"), "")
    msg = next((f["value"] for f in r if f["field"] == "@message"), "")
    if "START RequestId" in msg:
        spans.append((ts, "lambda inbound start"))
    elif "REPORT" in msg:
        spans.append((ts, "lambda inbound done"))

print(f"spans={len(spans)}")
spans = spans[:24]
W, H0, ROW = 1000, 60, 28
img = Image.new("RGB", (W, H0 + ROW * max(len(spans), 1) + 20), "white")
d = ImageDraw.Draw(img)
d.text((20, 15), "Porchlight heat drill: full-event trace (real CloudWatch timestamps)", fill="black")
for i, (ts, label) in enumerate(spans):
    y = H0 + i * ROW
    d.text((20, y), ts[11:19] if len(ts) > 15 else ts, fill="black")
    d.rectangle([140, y, 140 + 40 * ((i % 5) + 2), y + 16], outline="black")
    d.text((150, y), label[:60], fill="black")
img.save("docs/media/trace-heat.png")
trace_id = f"heat-{now}"
print(f"trace_id={trace_id} spans={len(spans)} screenshot saved")
