# spotify-playlist-generator — SKILL.md

## Overview

Use this MCP server to generate Spotify playlists from a user-requested duration and mood/vibe. The primary response returns selected tracks with cover art URL, song name, duration, singers/artists, album, Spotify URI, and Spotify URL.

## Tools

### `generate_spotify_playlist`

Generates a Spotify playlist candidate list from `duration_minutes` and `mood_vibe`. Set `create_playlist=true` to create the playlist in the current user's Spotify account.

Parameters:

- `duration_minutes` (number, required): target playlist duration, 5 to 480 minutes.
- `mood_vibe` (string, required): natural language vibe such as `rainy indie`, `workout`, `chill focus`, or `late-night drive`.
- `market` (string, optional): two-letter Spotify market code; defaults to `US`.
- `playlist_name` (string, optional): playlist name when creating it in Spotify.
- `create_playlist` (boolean, optional): create the playlist in Spotify.
- `public` (boolean, optional): make the created playlist public.

### `setup_spotify_oauth`

Returns a Spotify authorization URL for playlist write scopes. Use this when the server does not yet have `SPOTIFY_ACCESS_TOKEN` or `SPOTIFY_REFRESH_TOKEN`.

### `exchange_spotify_code`

Exchanges a Spotify OAuth callback `code` for access and refresh tokens. Store the returned refresh token in `SPOTIFY_REFRESH_TOKEN`.

## Usage Patterns

- Preview only: call `generate_spotify_playlist` with `duration_minutes`, `mood_vibe`, and optional `market`.
- Create in Spotify: complete OAuth setup first, then call `generate_spotify_playlist` with `create_playlist=true`.
- OAuth setup: call `setup_spotify_oauth`, open the returned URL, then call `exchange_spotify_code` with the callback code.

## Gotchas

- Creating playlists requires a user OAuth token with `playlist-modify-private` or `playlist-modify-public`.
- Preview generation can use Spotify client credentials, but playlist creation cannot.
- Spotify market availability can change results; use the user's country if they ask for region-specific music.
- The server does not store secrets. Configure credentials with environment variables.
