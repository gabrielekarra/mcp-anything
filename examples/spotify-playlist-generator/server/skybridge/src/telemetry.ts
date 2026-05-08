/**
 * Anonymized per-call telemetry (CONTRACT C-19, C-20)
 * Logs tool name, latency, and status only. Never logs parameter values.
 * Set MCP_TELEMETRY_ENDPOINT to enable remote reporting.
 */

const ENDPOINT = process.env["MCP_TELEMETRY_ENDPOINT"] ?? "";

export function recordCall(tool: string, latencyMs: number, status: string): void {
  console.error(JSON.stringify({ tool, latency_ms: latencyMs, status }));
  if (ENDPOINT) {
    sendRemote(tool, latencyMs, status).catch(() => {}); // must never break tool execution
  }
}

async function sendRemote(tool: string, latencyMs: number, status: string): Promise<void> {
  await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, latency_ms: latencyMs, status }),
    signal: AbortSignal.timeout(1000),
  });
}
