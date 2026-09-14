"use client";

import { useState } from "react";

export default function SimulatePanel({ eventId, residents }: { eventId: string; residents: { id: string; name: string; phone: string }[] }) {
  const [out, setOut] = useState("");
  const [text, setText] = useState("I feel dizzy");
  const [who, setWho] = useState(residents[1]?.phone ?? "");
  const [accessKey, setAccessKey] = useState("");
  const [menuToken, setMenuToken] = useState("");
  const [requestId, setRequestId] = useState("");

  async function act(op: string, body: Record<string, unknown>) {
    setOut("sending…");
    try {
      const res = await fetch(`/api/simulate/${op}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Console-Key": accessKey },
        body: JSON.stringify({ event_id: eventId, ...body }),
      });
      setOut(`${op}: ${res.status} ${(await res.text()).slice(0, 200)}`);
    } catch {
      setOut("Unable to reach the simulation service. Try again.");
    }
  }

  return (
    <section className="min-w-0 rounded-xl border border-amber-200 bg-white p-4">
      <h2 className="text-sm font-semibold">Synthetic drill (access key required)</h2>
      <label className="mt-2 block text-sm">
        Access key
        <input type="password" autoComplete="off" className="mt-1 block w-full min-w-0 rounded-lg border border-zinc-300 px-2 py-1.5" value={accessKey} onChange={(e) => setAccessKey(e.target.value)} />
      </label>
      <p className="mt-1 text-xs text-zinc-600">Use the privately provided key. It stays in this page until you close or reload it.</p>
      <fieldset disabled={!accessKey} className="disabled:opacity-50">
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        <button className="rounded-lg bg-amber-500 px-3 py-1.5 font-medium text-white hover:bg-amber-600" onClick={() => act("inject", { fixture: "heat.json" })}>Inject heat</button>
        <button className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50" onClick={() => act("inject", { fixture: "outage.json" })}>Inject outage</button>
      </div>
      <div className="mt-3 flex min-w-0 flex-wrap gap-2 text-sm">
        <select aria-label="Select Resident" className="max-w-full rounded-lg border border-zinc-300 px-2 py-1.5" value={who} onChange={(e) => setWho(e.target.value)}>
          {residents.map((r) => <option key={r.id} value={r.phone}>{r.name}</option>)}
        </select>
        <input aria-label="Resident reply message" className="min-w-0 basis-44 flex-1 rounded-lg border border-zinc-300 px-2 py-1.5" value={text} onChange={(e) => setText(e.target.value)} />
        <button className="rounded-lg bg-zinc-900 px-3 py-1.5 font-medium text-white hover:bg-zinc-700" onClick={() => act("resident", { from: who, text })}>Reply as resident</button>
      </div>
      <label className="mt-3 block text-sm">
        Coordinator menu code
        <input aria-label="Coordinator menu code" autoComplete="off" maxLength={8} className="mt-1 block w-full min-w-0 rounded-lg border border-zinc-300 px-2 py-1.5" value={menuToken} onChange={(e) => setMenuToken(e.target.value.trim())} />
      </label>
      <p className="mt-1 text-xs text-zinc-600">Copy the code from the coordinator message you reviewed, then choose its matching number. Older menus are rejected.</p>
      <label className="mt-3 block text-sm">
        Volunteer request ID
        <input aria-label="Volunteer request ID" autoComplete="off" className="mt-1 block w-full min-w-0 rounded-lg border border-zinc-300 px-2 py-1.5" value={requestId} onChange={(e) => setRequestId(e.target.value.trim())} />
      </label>
      <p className="mt-1 text-xs text-zinc-600">Copy the ID from the volunteer request you reviewed.</p>
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        <button disabled={!requestId} className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50 disabled:opacity-50" onClick={() => act("volunteer", { dispatch_id: requestId, text: "Y" })}>Volunteer Y</button>
        <button disabled={!requestId} className="rounded-lg border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50 disabled:opacity-50" onClick={() => act("volunteer", { dispatch_id: requestId, text: "N" })}>Volunteer N</button>
        {["1", "2", "3", "4"].map((d) => (
          <button key={d} disabled={!/^[a-f0-9]{8}$/.test(menuToken)} className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 hover:bg-amber-100 disabled:opacity-50" onClick={() => act("coordinator", { text: d, menu_token: menuToken })}>Coordinator {d}</button>
        ))}
      </div>
      </fieldset>
      <p role="status" className="mt-2 break-words font-mono text-xs text-zinc-600">{out}</p>
    </section>
  );
}
