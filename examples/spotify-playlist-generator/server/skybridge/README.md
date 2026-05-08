# spotify-playlist-generator

Skybridge MCP + ChatGPT App server generated with `mcp-anything --target skybridge`, then implemented against the real Spotify Web API.

It generates playlists from:

- target duration, in minutes
- mood or vibe, such as `rainy indie`, `workout`, `chill focus`, or `late-night drive`
- optional market code

Results include each chosen song's cover image, name, duration, and singer/artist names. If `create_playlist` is true, the server creates a Spotify playlist for the current user and adds the selected tracks.

## Requirements

- Node.js 22.12+
- pnpm 10+
- A Spotify developer app

## Spotify auth

For preview-only generation, set either a user token or client credentials:

```bash
export SPOTIFY_CLIENT_ID=...
export SPOTIFY_CLIENT_SECRET=...
```

For creating playlists, use a user OAuth token with playlist scopes:

```bash
export SPOTIFY_CLIENT_ID=...
export SPOTIFY_CLIENT_SECRET=...
export SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Then call:

1. `setup_spotify_oauth`
2. Open the returned URL and approve access.
3. Call `exchange_spotify_code` with the callback `code`.
4. Export the returned `SPOTIFY_REFRESH_TOKEN`.

You can also set `SPOTIFY_ACCESS_TOKEN` directly for short-lived testing.

## Quick start

```bash
cd examples/spotify-playlist-generator/server/skybridge
pnpm install
pnpm dev
```

## Tools

- `generate_spotify_playlist` - generates a track list from `duration_minutes` and `mood_vibe`, optionally creating the playlist in Spotify.
- `setup_spotify_oauth` - returns a Spotify authorization URL for playlist scopes.
- `exchange_spotify_code` - exchanges a Spotify callback code for access and refresh tokens.

## Environment variables

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify developer app client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify developer app client secret |
| `SPOTIFY_REDIRECT_URI` | Redirect URI registered in Spotify dashboard |
| `SPOTIFY_REFRESH_TOKEN` | User refresh token for creating playlists |
| `SPOTIFY_ACCESS_TOKEN` | Optional short-lived access token |
| `MCP_TRANSPORT` | `stdio` or `http` |
| `MCP_TELEMETRY_ENDPOINT` | Optional URL for anonymized call metrics |
