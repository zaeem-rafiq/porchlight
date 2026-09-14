import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";

const WINDOW_MS = 10_000;
let lastAction = 0;

const HEAT = {
  id: "https://api.weather.gov/alerts/urn:oid:porchlight.demo.heat001",
  properties: {
    areaDesc: "Benton County",
    event: "Extreme Heat Warning",
    severity: "Extreme",
    headline: "Extreme Heat Warning issued September 7 at 2:15PM CDT",
    instruction: "Drink plenty of fluids, stay in an air-conditioned room.",
    onset: "2026-09-07T14:15:00-05:00",
    expires: "2026-09-08T20:00:00-05:00",
    senderName: "NWS Tulsa OK",
    sent: "2026-09-07T14:15:00-05:00",
    status: "Actual",
  },
  type: "Feature",
};

const OUTAGE = {
  id: "porchlight:synthetic:outage001",
  properties: {
    areaDesc: "Pea Ridge, AR",
    event: "Power Outage",
    severity: "Severe",
    headline: "Synthetic power-outage event for Porchlight drill",
    instruction: "Check on residents with powered medical devices.",
    onset: "2026-09-07T16:00:00-05:00",
    expires: "2026-09-07T22:00:00-05:00",
    senderName: "Porchlight coordinator drill",
    sent: "2026-09-07T16:00:00-05:00",
    status: "Test",
  },
  type: "Feature",
};

export async function POST(req: NextRequest, { params }: { params: Promise<{ op: string }> }) {
  const functionUrl = process.env.FUNCTION_URL || process.env.SIMULATE_FUNCTION_URL || "";
  const expectedKey = process.env.CONSOLE_KEY || "";
  const consoleKey = req.headers.get("x-console-key") || "";
  if (!functionUrl || !expectedKey) {
    return NextResponse.json({ error: "simulation access is not configured" }, { status: 503 });
  }
  const supplied = Buffer.from(consoleKey);
  const expected = Buffer.from(expectedKey);
  if (!consoleKey || supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) {
    return NextResponse.json({ error: "valid access key required" }, { status: 403 });
  }
  const { op } = await params;
  if (!["inject", "resident", "volunteer", "coordinator"].includes(op)) {
    return NextResponse.json({ error: "unknown op" }, { status: 400 });
  }
  const incoming = await req.json().catch(() => null);
  if (!incoming || typeof incoming !== "object" || Array.isArray(incoming)) {
    return NextResponse.json({ error: "JSON object required" }, { status: 400 });
  }
  if (op !== "inject" && (
    typeof incoming.event_id !== "string" || !incoming.event_id ||
    typeof incoming.text !== "string" || !incoming.text.trim() || incoming.text.length > 2000
  )) {
    return NextResponse.json({ error: "event and reply text required" }, { status: 400 });
  }
  if (op === "resident" && (typeof incoming.from !== "string" || !incoming.from)) {
    return NextResponse.json({ error: "resident required" }, { status: 400 });
  }
  if (op === "coordinator" && (typeof incoming.menu_token !== "string" || !/^[a-f0-9]{8}$/.test(incoming.menu_token))) {
    return NextResponse.json({ error: "code from the reviewed coordinator menu required" }, { status: 400 });
  }
  if (op === "volunteer" && (typeof incoming.dispatch_id !== "string" || !incoming.dispatch_id.trim())) {
    return NextResponse.json({ error: "ID from the reviewed volunteer request required" }, { status: 400 });
  }
  const now = Date.now();
  if (now - lastAction < WINDOW_MS) {
    return NextResponse.json({ error: "one action per 10s" }, { status: 429 });
  }
  lastAction = now;
  let payload: Record<string, unknown>;
  if (op === "inject") {
    const which = incoming.fixture === "outage.json" ? OUTAGE : HEAT;
    payload = { op: "inject", alert: which, fixture: incoming.fixture ?? "heat.json" };
  } else if (op === "volunteer") {
    payload = { op: "volunteer", dispatch_id: incoming.dispatch_id, text: incoming.text ?? "Y", event_id: incoming.event_id };
  } else if (op === "coordinator") {
    payload = { op: "coordinator", text: incoming.text ?? "1", menu_token: incoming.menu_token, event_id: incoming.event_id };
  } else {
    payload = { op: "inbound", to: "telegram", from: incoming.from, text: incoming.text, event_id: incoming.event_id };
  }
  try {
    const res = await fetch(functionUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Console-Key": consoleKey },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "simulation service unavailable" }, { status: 502 });
  }
}
