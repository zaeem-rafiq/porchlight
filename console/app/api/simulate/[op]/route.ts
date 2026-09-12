import { NextRequest, NextResponse } from "next/server";

const WINDOW_MS = 10_000;
let lastAction = 0;

const FUNCTION_URL =
  process.env.FUNCTION_URL ||
  process.env.SIMULATE_FUNCTION_URL ||
  "https://qrqpu64krttrdqmumjl7dpv2du0dxrkk.lambda-url.us-east-1.on.aws/";

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
  const { op } = await params;
  if (!["inject", "resident", "volunteer", "coordinator"].includes(op)) {
    return NextResponse.json({ error: "unknown op" }, { status: 400 });
  }
  const now = Date.now();
  if (now - lastAction < WINDOW_MS) {
    return NextResponse.json({ error: "one action per 10s" }, { status: 429 });
  }
  lastAction = now;
  const incoming = await req.json().catch(() => ({}));
  let payload: Record<string, unknown>;
  if (op === "inject") {
    const which = incoming.fixture === "outage.json" ? OUTAGE : HEAT;
    payload = { op: "inject", alert: which, fixture: incoming.fixture ?? "heat.json" };
  } else if (op === "volunteer") {
    payload = { op: "volunteer", dispatch_id: incoming.dispatch_id, text: incoming.text ?? "Y", event_id: incoming.event_id };
  } else if (op === "coordinator") {
    payload = { op: "coordinator", text: incoming.text ?? "1", event_id: incoming.event_id };
  } else {
    payload = { op: "inbound", to: incoming.to || "telegram", ...incoming };
    if (!incoming.to) {
      payload.to = "telegram";
    }
  }
  const consoleKey = req.headers.get("x-console-key") || process.env.CONSOLE_KEY || "";
  const res = await fetch(FUNCTION_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Console-Key": consoleKey },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
