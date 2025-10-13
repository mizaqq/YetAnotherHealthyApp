export type HealthResponse = { status: string };

const DEFAULT_API_BASE = "/api/v1";
type ImportMetaEnv = {
  readonly VITE_API_BASE?: string;
};

const { env } = import.meta as unknown as { env: ImportMetaEnv };
const API_BASE = env?.VITE_API_BASE ?? DEFAULT_API_BASE;

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`, {
    method: "GET",
    headers: { Accept: "application/json" }
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Health check failed (${response.status}): ${text}`);
  }

  return (await response.json()) as HealthResponse;
}


