import Link from "next/link";
import { boardClient, STAMPS } from "@/lib/board";
import SimulatePanel from "./simulate-panel";
import Refresh from "./refresh";

export const dynamic = "force-dynamic";

export default async function Home() {
  const sb = boardClient();
  const { data: events } = await sb.from("hazard_events").select("*").eq("status", "open").limit(1);
  const event = (events ?? [])[0] ?? null;
  const { data: residents } = await sb.from("residents").select("*").order("name");
  const { data: contacts } = event
    ? await sb.from("contacts").select("*").eq("event_id", event.id)
    : { data: [] };
  const { data: audit } = event
    ? await sb.from("audit_log").select("*").eq("event_id", event.id).order("created_at", { ascending: false }).limit(20)
    : { data: [] };
  const byResident = new Map((contacts ?? []).map((c) => [c.resident_id, c]));
  const tiers = [1, 2, 3].map((t) => (contacts ?? []).filter((c) => c.tier === t).length);

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="rounded-xl border border-amber-200 bg-amber-400/10 p-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-800">Porchlight · live event</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">
          {event ? event.headline : "No open event"}
        </h1>
        <div className="mt-3 flex gap-2">
          {tiers.map((n, i) => (
            <span key={i} className="rounded-full border border-amber-300 bg-white px-3 py-1 text-sm font-medium">
              Tier {i + 1}: {n}
            </span>
          ))}
        </div>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white">
        <h2 className="border-b border-zinc-100 px-4 py-3 text-sm font-semibold">Roster board · {(residents ?? []).length} residents</h2>
        <ul className="divide-y divide-zinc-100">
          {(residents ?? []).map((r) => {
            const c = byResident.get(r.id);
            const stamp = c?.status ?? "pending";
            return (
              <li key={r.id} className="flex items-center gap-3 px-4 py-2">
                <span className="w-48 truncate text-sm font-medium">{r.name}</span>
                <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${STAMPS[stamp] ?? STAMPS.pending}`}>
                  {stamp.replace("_", " ")}
                </span>
                <span className="ml-auto text-xs text-zinc-500">tier {c?.tier ?? "–"}</span>
                {event && (
                  <Link aria-label={`View conversation for ${r.name}`} className="text-xs font-medium text-amber-800 underline" href={`/event/${event.id}/resident/${r.id}`}>
                    conversation
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-xl border border-zinc-200 bg-white p-4">
          <h2 className="text-sm font-semibold">Timeline</h2>
          <ul className="mt-2 space-y-1 text-xs text-zinc-600">
            {(audit ?? []).map((a) => (
              <li key={a.id}>· {a.action} — {String(a.detail ?? "").slice(0, 90)}</li>
            ))}
          </ul>
        </section>
        <SimulatePanel eventId={event?.id ?? ""} residents={residents ?? []} />
      </div>
      <Refresh />
    </main>
  );
}
