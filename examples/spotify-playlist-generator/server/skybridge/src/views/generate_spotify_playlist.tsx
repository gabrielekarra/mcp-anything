import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { useCallTool, mountView } from "skybridge/web";

type Track = {
  id: string;
  name: string;
  duration: string;
  singers: string[];
  album: string;
  cover_url: string;
  spotify_url: string;
};

type PlaylistResult = {
  playlist_name: string;
  mood_vibe: string;
  requested_duration_minutes: number;
  actual_duration: string;
  market: string;
  created_playlist?: {
    spotify_url?: string;
  } | null;
  tracks: Track[];
};

type GeneratePlaylistArgs = {
  mood_vibe: string;
  duration_minutes: number;
  market: string;
  playlist_name?: string;
  create_playlist?: boolean;
  public?: boolean;
};

function asPlaylistResult(data: unknown): PlaylistResult | null {
  if (!data) {
    return null;
  }
  if (typeof data === "object" && "result" in data && typeof (data as any).result === "string") {
    try {
      return JSON.parse((data as any).result) as PlaylistResult;
    } catch {
      return null;
    }
  }
  if (typeof data === "string") {
    try {
      return JSON.parse(data) as PlaylistResult;
    } catch {
      return null;
    }
  }
  if (
    typeof data === "object" &&
    "content" in data &&
    Array.isArray((data as any).content) &&
    typeof (data as any).content[0]?.text === "string"
  ) {
    try {
      return JSON.parse((data as any).content[0].text) as PlaylistResult;
    } catch {
      return null;
    }
  }
  return data as PlaylistResult;
}

function PlaylistGeneratorView() {
  const { status, data, error, callTool } = useCallTool<GeneratePlaylistArgs>("generate_spotify_playlist");
  const [moodVibe, setMoodVibe] = useState("late-night rainy indie");
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [market, setMarket] = useState("US");
  const [playlistName, setPlaylistName] = useState("");
  const [createPlaylist, setCreatePlaylist] = useState(false);
  const [isPublic, setIsPublic] = useState(false);
  const result = useMemo(() => asPlaylistResult(data), [data]);

  const run = () => {
    callTool({
      mood_vibe: moodVibe,
      duration_minutes: durationMinutes,
      market,
      playlist_name: playlistName || undefined,
      create_playlist: createPlaylist,
      public: isPublic,
    });
  };

  return (
    <main style={styles.shell}>
      <aside style={styles.sidebar}>
        <div style={styles.logoMark}>S</div>
        <div style={styles.navItemActive}>Generate</div>
        <div style={styles.navItem}>OAuth</div>
        <div style={styles.navItem}>Library</div>
      </aside>

      <section style={styles.content}>
        <div style={styles.topbar}>
          <div>
            <div style={styles.eyebrow}>Spotify playlist generator</div>
            <h1 style={styles.title}>{result?.playlist_name ?? "Build a playlist"}</h1>
          </div>
          <button style={styles.primaryButton} onClick={run} disabled={status === "pending"}>
            {status === "pending" ? "Generating..." : "Generate"}
          </button>
        </div>

        <section style={styles.controls}>
          <label style={styles.field}>
            <span style={styles.label}>Mood or vibe</span>
            <input
              style={styles.input}
              value={moodVibe}
              onChange={(event) => setMoodVibe(event.target.value)}
            />
          </label>
          <label style={styles.fieldSmall}>
            <span style={styles.label}>Minutes</span>
            <input
              style={styles.input}
              type="number"
              min={5}
              max={480}
              value={durationMinutes}
              onChange={(event) => setDurationMinutes(Number(event.target.value))}
            />
          </label>
          <label style={styles.fieldSmall}>
            <span style={styles.label}>Market</span>
            <input
              style={styles.input}
              maxLength={2}
              value={market}
              onChange={(event) => setMarket(event.target.value.toUpperCase())}
            />
          </label>
          <label style={styles.field}>
            <span style={styles.label}>Playlist name</span>
            <input
              style={styles.input}
              value={playlistName}
              placeholder="Auto-name"
              onChange={(event) => setPlaylistName(event.target.value)}
            />
          </label>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={createPlaylist}
              onChange={(event) => setCreatePlaylist(event.target.checked)}
            />
            Create in Spotify
          </label>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(event) => setIsPublic(event.target.checked)}
            />
            Public
          </label>
        </section>

        {status === "error" && <div style={styles.error}>Error: {String(error)}</div>}

        <section style={styles.summary}>
          <div>
            <div style={styles.metricValue}>{result?.tracks?.length ?? 0}</div>
            <div style={styles.metricLabel}>songs</div>
          </div>
          <div>
            <div style={styles.metricValue}>{result?.actual_duration ?? "0:00"}</div>
            <div style={styles.metricLabel}>duration</div>
          </div>
          <div>
            <div style={styles.metricValue}>{result?.market ?? market}</div>
            <div style={styles.metricLabel}>market</div>
          </div>
          {result?.created_playlist?.spotify_url && (
            <a style={styles.spotifyLink} href={result.created_playlist.spotify_url}>
              Open in Spotify
            </a>
          )}
        </section>

        <div style={styles.tableHeader}>
          <span>#</span>
          <span>Title</span>
          <span>Album</span>
          <span>Duration</span>
        </div>

        <div style={styles.trackList}>
          {(result?.tracks ?? []).map((track, index) => (
            <a key={track.id} style={styles.trackRow} href={track.spotify_url}>
              <span style={styles.index}>{index + 1}</span>
              <img style={styles.cover} src={track.cover_url} alt="" />
              <span style={styles.trackText}>
                <span style={styles.trackName}>{track.name}</span>
                <span style={styles.artistName}>{track.singers.join(", ")}</span>
              </span>
              <span style={styles.album}>{track.album}</span>
              <span style={styles.duration}>{track.duration}</span>
            </a>
          ))}
          {!result?.tracks?.length && status !== "pending" && (
            <div style={styles.emptyState}>Choose a vibe and duration, then generate.</div>
          )}
        </div>
      </section>
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  shell: {
    minHeight: "100vh",
    display: "grid",
    gridTemplateColumns: "220px minmax(0, 1fr)",
    background: "#121212",
    color: "#ffffff",
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
  },
  sidebar: {
    background: "#000000",
    padding: 24,
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  logoMark: {
    width: 42,
    height: 42,
    borderRadius: 21,
    background: "#1db954",
    color: "#000000",
    display: "grid",
    placeItems: "center",
    fontWeight: 800,
    marginBottom: 18,
  },
  navItemActive: {
    color: "#ffffff",
    fontWeight: 700,
    padding: "10px 0",
  },
  navItem: {
    color: "#b3b3b3",
    fontWeight: 600,
    padding: "10px 0",
  },
  content: {
    padding: 28,
    overflow: "hidden",
  },
  topbar: {
    minHeight: 164,
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: 24,
    padding: "28px 28px 22px",
    background: "linear-gradient(180deg, #1f3d2b 0%, #181818 100%)",
  },
  eyebrow: {
    color: "#b3b3b3",
    fontSize: 13,
    fontWeight: 700,
    textTransform: "uppercase",
  },
  title: {
    margin: "8px 0 0",
    fontSize: 48,
    lineHeight: 1,
    letterSpacing: 0,
  },
  primaryButton: {
    border: 0,
    background: "#1db954",
    color: "#000000",
    borderRadius: 24,
    padding: "13px 26px",
    fontWeight: 800,
    cursor: "pointer",
    minWidth: 128,
  },
  controls: {
    display: "grid",
    gridTemplateColumns: "minmax(220px, 2fr) 110px 96px minmax(180px, 1fr) auto auto",
    gap: 12,
    alignItems: "end",
    padding: "18px 0",
  },
  field: {
    display: "grid",
    gap: 6,
  },
  fieldSmall: {
    display: "grid",
    gap: 6,
  },
  label: {
    color: "#b3b3b3",
    fontSize: 12,
    fontWeight: 700,
  },
  input: {
    height: 40,
    border: "1px solid #333333",
    borderRadius: 4,
    background: "#242424",
    color: "#ffffff",
    padding: "0 12px",
    fontSize: 14,
  },
  toggle: {
    height: 40,
    display: "flex",
    alignItems: "center",
    gap: 8,
    color: "#d9d9d9",
    fontSize: 14,
    whiteSpace: "nowrap",
  },
  error: {
    background: "#3d1515",
    color: "#ffd6d6",
    padding: 12,
    borderRadius: 6,
    marginBottom: 12,
  },
  summary: {
    display: "flex",
    alignItems: "center",
    gap: 28,
    padding: "14px 0 22px",
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 800,
  },
  metricLabel: {
    color: "#b3b3b3",
    fontSize: 12,
  },
  spotifyLink: {
    color: "#1db954",
    fontWeight: 800,
    textDecoration: "none",
    marginLeft: "auto",
  },
  tableHeader: {
    display: "grid",
    gridTemplateColumns: "40px minmax(240px, 2fr) minmax(160px, 1fr) 84px",
    color: "#b3b3b3",
    borderBottom: "1px solid #2a2a2a",
    padding: "0 12px 10px",
    fontSize: 13,
  },
  trackList: {
    display: "grid",
    gap: 2,
    paddingTop: 8,
  },
  trackRow: {
    display: "grid",
    gridTemplateColumns: "40px 56px minmax(184px, 2fr) minmax(160px, 1fr) 84px",
    alignItems: "center",
    minHeight: 64,
    gap: 12,
    color: "#ffffff",
    textDecoration: "none",
    borderRadius: 4,
    padding: "4px 12px",
  },
  index: {
    color: "#b3b3b3",
    textAlign: "right",
  },
  cover: {
    width: 48,
    height: 48,
    objectFit: "cover",
  },
  trackText: {
    minWidth: 0,
    display: "grid",
    gap: 3,
  },
  trackName: {
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
    fontWeight: 700,
  },
  artistName: {
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
    color: "#b3b3b3",
    fontSize: 13,
  },
  album: {
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
    color: "#b3b3b3",
    fontSize: 13,
  },
  duration: {
    color: "#b3b3b3",
    fontSize: 13,
  },
  emptyState: {
    padding: 28,
    color: "#b3b3b3",
    textAlign: "center",
  },
};

export default PlaylistGeneratorView;
mountView(<PlaylistGeneratorView />);
