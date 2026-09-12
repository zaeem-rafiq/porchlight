"use client";

import { useState } from "react";

export default function SimulatePanel({ eventId, residents }: { eventId: string; residents: { id: string; name: string; phone: string }[] }) {
  const [out, setOut] = useState("");
  const [text, setText] = useState("I feel dizzy");
  const [who, setWho] = useState(residents[1]?.phone ?? "");

  async function act(op: string, body: Record<string, unknown>) {
    setOut("sending…");
    const res = await fetch(`/api/simulate/${op}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: eventId, ...body }),
    });
    setOut(`${op}: ${res.status} ${(await res.text()).slice(0, 200)}`);
  }

  return (
    <section className="rounded-xl border border-amber-200 bg-white p-4">
      <h2 className="text-sm font-semibold">Simulate (judges, no phone needed)</h2>
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        <button className="rounded-lg bg-amber-500 px-3 py-1.5 font-medium text-white hover:bg-amber-600" onClick={() => act("inject", { fixture: "heat.json" })}>Inject heat</button>
        <button className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50" onClick={() => act("inject", { fixture: "outage.json" })}>Inject outage</button>
      </div>
      <div className="mt-3 flex gap-2 text-sm">
        <select aria-label="Select Resident" className="rounded-lg border border-zinc-300 px-2 py-1.5" value={who} onChange={(e) => setWho(e.target.value)}>
          {residents.map((r) => <option key={r.id} value={r.phone}>{r.name}</option>)}
        </select>
        <input aria-label="Resident reply message" className="w-full rounded-lg border border-zinc-300 px-2 py-1.5" value={text} onChange={(e) => setText(e.target.value)} />
        <button className="rounded-lg bg-zinc-900 px-3 py-1.5 font-medium text-white hover:bg-zinc-700" onClick={() => act("resident", { from: who, text })}>Reply as resident</button>
      </div>
      <div className="mt-2 flex gap-2 text-sm">
        <button className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50" onClick={() => act("volunteer", { dispatch_id: "", text: "Y" })}>Volunteer Y</button>
        <button className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50" onClick={() => act("volunteer", { dispatch_id: "", text: "N" })}>Volunteer N</button>
        {["1", "2", "3"].map((d) => (
          <button key={d} className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 hover:bg-amber-100" onClick={() => act("coordinator", { text: d })}>Coordinator {d}</button>
        ))}
      </div>
      <p className="mt-2 break-words font-mono text-xs text-zinc-600">{out}</p>
    </section>
  );
}
