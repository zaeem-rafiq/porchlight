import Link from "next/link";
import { boardClient, STAMPS } from "@/lib/board";

export const dynamic = "force-dynamic";

export default async function ResidentPage({ params }: { params: Promise<{ id: string; rid: string }> }) {
  const { id, rid } = await params;
  const sb = boardClient();
  const resident = (await sb.from("residents").select("*").eq("id", rid).limit(1)).data?.[0];
  const contact = (await sb.from("contacts").select("*").eq("event_id", id).eq("resident_id", rid).limit(1)).data?.[0];
  let query = sb.from("audit_log").select("*").eq("event_id", id);
  if (resident?.name) {
    query = query.ilike("detail", `%${resident.name}%`);
  }
  const trail = (await query.order("created_at")).data ?? [];
  const mine = trail.filter((a) => String(a.detail ?? "").includes(resident?.name ?? "§none§"));
  const quote = mine
    .slice()
    .reverse()
    .map((a) => /quote=([^]*)/.exec(String(a.detail ?? ""))?.[1]?.trim())
    .find(Boolean) ?? "—";

  if (!resident) return <main className="p-6">Resident not found. <Link href="/">Back</Link></main>;
  return (
    <main className="mx-auto max-w-3xl space-y-4 p-6">
      <Link href="/" aria-label="Back to dispatch board" className="text-sm font-medium text-amber-800 underline">← board</Link>
      <header className="rounded-xl border border-zinc-200 bg-white p-5">
        <h1 className="text-xl font-bold">{resident.name}</h1>
        <p className="text-sm text-zinc-600">{resident.language === "es" ? "Español" : "English"} · {resident.notes}</p>
        <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-xs font-semibold ${STAMPS[contact?.status ?? "pending"] ?? ""}`}>
          {(contact?.status ?? "pending").replace("_", " ")}
        </span>
      </header>
      <section className="rounded-xl border border-zinc-200 bg-white p-4">
        <h2 className="text-sm font-semibold">Triage quote</h2>
        <blockquote className="mt-1 border-l-4 border-amber-400 pl-3 text-sm italic">“{quote}”</blockquote>
      </section>
      <section className="rounded-xl border border-zinc-200 bg-white p-4">
        <h2 className="text-sm font-semibold">Conversation trail</h2>
        <ul className="mt-2 space-y-1 text-xs text-zinc-600">
          {mine.map((a) => <li key={a.id}>· {a.action} — {String(a.detail ?? "").slice(0, 120)}</li>)}
        </ul>
      </section>
    </main>
  );
}
