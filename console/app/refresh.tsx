"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Refresh() {
  const router = useRouter();
  useEffect(() => {
    const t = setInterval(() => router.refresh(), 5000);
    return () => clearInterval(t);
  }, [router]);
  return null;
}
