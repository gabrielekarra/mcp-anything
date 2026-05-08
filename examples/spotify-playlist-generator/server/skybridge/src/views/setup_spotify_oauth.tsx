import { useState } from "react";
import { useCallTool, mountView } from "skybridge/web";

type SetupOAuthArgs = {
  redirect_uri?: string;
};

function safeParse(raw: string): any {
  try { return JSON.parse(raw); } catch { return raw; }
}

function getContent(data: unknown): any {
  if (!data) return null;
  if (typeof data === "object" && "result" in data && typeof (data as any).result === "string") {
    return safeParse((data as any).result);
  }
  if (typeof data === "object" && "content" in data && typeof (data as any).content === "string") {
    return safeParse((data as any).content);
  }
  if (
    typeof data === "object" &&
    "content" in data &&
    Array.isArray((data as any).content) &&
    typeof (data as any).content[0]?.text === "string"
  ) {
    return safeParse((data as any).content[0].text);
  }
  if (typeof data === "string") {
    return safeParse(data);
  }
  return data;
}

function SpotifyOAuthView() {
  const { status, data, error, callTool } = useCallTool<SetupOAuthArgs>("setup_spotify_oauth");
  const [redirectUri, setRedirectUri] = useState("http://127.0.0.1:8888/callback");
  const payload = getContent(data);

  return (
    <main style={{ minHeight: "100vh", background: "#121212", color: "#fff", padding: 28, fontFamily: "Inter, system-ui, sans-serif" }}>
      <h1 style={{ margin: 0, fontSize: 32, letterSpacing: 0 }}>Spotify OAuth</h1>
      <div style={{ display: "grid", gap: 10, maxWidth: 760, marginTop: 24 }}>
        <label style={{ color: "#b3b3b3", fontSize: 13, fontWeight: 700 }}>Redirect URI</label>
        <input
          value={redirectUri}
          onChange={(event) => setRedirectUri(event.target.value)}
          style={{ height: 42, background: "#242424", color: "#fff", border: "1px solid #333", borderRadius: 4, padding: "0 12px" }}
        />
        <button
          onClick={() => callTool({ redirect_uri: redirectUri })}
          style={{ width: 180, height: 44, border: 0, borderRadius: 22, background: "#1db954", color: "#000", fontWeight: 800 }}
        >
          Create Auth URL
        </button>
      </div>
      {status === "error" && <p style={{ color: "#ffb4b4" }}>{String(error)}</p>}
      {payload?.authorization_url && (
        <a style={{ display: "block", marginTop: 24, color: "#1db954", wordBreak: "break-all" }} href={payload.authorization_url}>
          {payload.authorization_url}
        </a>
      )}
    </main>
  );
}

export default SpotifyOAuthView;
mountView(<SpotifyOAuthView />);
