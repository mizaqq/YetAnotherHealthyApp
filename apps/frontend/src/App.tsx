import { useState } from "react";
import { getHealth } from "@/lib/api";

export default function App() {
  const [status, setStatus] = useState<string>("unknown");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchHealth() {
    setLoading(true);
    setError(null);
    try {
      const data = await getHealth();
      setStatus(data.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh bg-gray-50 text-gray-900">
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold">YetAnotherHealthyApp</h1>
        <p className="mt-2 text-sm text-gray-600">React + FastAPI starter</p>

        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={() => {
              void fetchHealth();
            }}
            disabled={loading}
            className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
          >
            {loading ? "Checking..." : "Check Health"}
          </button>
          <span className="text-sm">
            Status: <span className="font-mono">{status}</span>
          </span>
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-600">Error: {error}</p>
        )}
      </div>
    </div>
  );
}


