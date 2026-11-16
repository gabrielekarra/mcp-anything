# MCP server leaderboard

Graded on 2026-11-16 with mcp-anything 0.3.0 (`python scripts/leaderboard.py`). The grade is a static review of each server's tool list: how easy it is for an agent to choose a tool and call it correctly. It does not test whether the tools work. See `mcp-anything grade --help` for the rules.

| Rank | Server | Grade | Score | Tools | Tool list (tokens) | Biggest finding |
|---|---|---|---|---|---|---|
| 1 | [Everything (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) | A | 100 | 16 | 1,942 | none |
| 2 | [Fetch (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | A | 100 | 1 | 353 | none |
| 3 | [Memory (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | A | 100 | 9 | 2,089 | none |
| 4 | [Time (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/time) | A | 100 | 3 | 550 | none |
| 5 | [Brave Search (official)](https://github.com/brave/brave-search-mcp-server) | A | 98 | 8 | 8,666 | Overlong descriptions (-1.5) |
| 6 | [Sequential thinking (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | A | 97 | 1 | 577 | Overlong descriptions (-3.0) |
| 7 | [Filesystem (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | A | 96 | 16 | 3,548 | CRUD operations not grouped (-4.5) |
| 8 | [Playwright (Microsoft)](https://github.com/microsoft/playwright-mcp) | A | 93 | 25 | 4,829 | Vague descriptions (-6.0) |
| 9 | [Notion (official)](https://github.com/makenotion/notion-mcp-server) | C | 74 | 24 | 20,067 | Undocumented parameters (-17.7) |
| 10 | [Git (reference)](https://github.com/modelcontextprotocol/servers/tree/main/src/git) | C | 70 | 14 | 1,643 | Undocumented parameters (-23.1) |

Not graded:

- GitHub (official): needs GITHUB_PERSONAL_ACCESS_TOKEN
