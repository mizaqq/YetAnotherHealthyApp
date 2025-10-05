"use client";
import { useEffect, useState } from "react";
import { createApiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/types.gen";

export default function HomePage() {
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const api = createApiClient();
    const today = new Date().toISOString().slice(0, 10);
    setStatus("loading");
    api.GET("/api/v1/summary", { params: { query: { date: today } } })
      .then((res) => {
        if (res.error) throw res.error;
        setStatus("ok");
      })
      .catch((e: any) => {
        setError(e?.message ?? "Unknown error");
        setStatus("error");
      });
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>Yet Another Healthy App</h1>
      <p>Status: {status}</p>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
    </main>
  );
}
