export {};

declare module "skybridge/server" {
  interface ViewNameRegistry {
    "exchange_spotify_code": true;
    "generate_spotify_playlist": true;
    "setup_spotify_oauth": true;
  }
}
