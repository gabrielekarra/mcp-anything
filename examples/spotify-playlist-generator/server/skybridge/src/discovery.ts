/**
 * Discovery endpoint data (CONTRACT C-01..C-03)
 */

const TOOLS = [
  {
    name: "generate_spotify_playlist",
    description: "Generate a Spotify playlist from mood/vibe and target duration.",
  },
  {
    name: "setup_spotify_oauth",
    description: "Create a Spotify authorization URL for playlist write scopes.",
  },
  {
    name: "exchange_spotify_code",
    description: "Exchange a Spotify OAuth callback code for access and refresh tokens.",
  },
];

const GROUPS = [
  {
    name: "spotify_playlist_generation",
    disclosure_level: "default",
  },
  {
    name: "spotify_oauth",
    disclosure_level: "verbose",
  },
];

export function getDiscoveryInfo() {
  return {
    server_name: "spotify-playlist-generator",
    version: "1.0.0",
    tool_count: TOOLS.length,
    tool_groups: GROUPS,
    tools: TOOLS,
  };
}
