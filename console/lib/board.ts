import { createClient } from "@supabase/supabase-js";

export function boardClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "";
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY || "";
  return createClient(
    url,
    anonKey,
    { db: { schema: "porchlight" } }
  );
}

export type Status = "sent" | "ok" | "needs_help" | "medical" | "unclear" | "unreachable" | "opted_out" | "pending" | "resent" | "observed_only" | "open" | "closed";

export const STAMPS: Record<string, string> = {
  ok: "bg-green-100 text-green-900 border-green-300",
  needs_help: "bg-amber-100 text-amber-900 border-amber-300",
  medical: "bg-red-100 text-red-900 border-red-400",
  unclear: "bg-yellow-50 text-yellow-900 border-yellow-300",
  unreachable: "bg-zinc-200 text-zinc-800 border-zinc-400",
  opted_out: "bg-slate-200 text-slate-800 border-slate-300",
  sent: "bg-sky-100 text-sky-900 border-sky-300",
  pending: "bg-zinc-100 text-zinc-700 border-zinc-300",
  resent: "bg-sky-50 text-sky-800 border-sky-200",
};
