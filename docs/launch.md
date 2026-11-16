# Launch post (draft)

Fill in the numbers from `docs/leaderboard.md` after running `python scripts/leaderboard.py`. Do not publish before the leaderboard is real.

---

**Title:** Show HN: We graded N popular MCP servers on how usable they are for agents

Most MCP servers are judged by whether they work. Agents care about something else: whether they can pick the right tool out of the list and call it correctly. A server with 90 tools, vague descriptions and undocumented parameters works fine and is still hard for an agent to use, and it costs thousands of tokens on every request before the agent has done anything.

We built `mcp-anything grade`, which scores any MCP server from 0 to 100 on fifteen deterministic rules: tool count, the context cost of the tool list, missing or vague descriptions, undocumented or untyped parameters, missing destructive-action annotations, near-duplicate tools, and so on. No model is involved, so the same server always gets the same score, and every finding comes with a fix.

Then we ran it on N servers: the MCP reference servers and the official servers of [list]. Results: [link to docs/leaderboard.md]

- Best: [server] ([grade])
- Most common problem: [rule], in [n] of N servers
- Largest tool list: [server], about [tokens] tokens on every request

It works on any server, over stdio or HTTP:

    pip install mcp-anything
    mcp-anything grade "npx -y @modelcontextprotocol/server-memory"

There is a badge and a GitHub Action to keep a score from slipping in CI.

mcp-anything also generates servers, from an OpenAPI spec, a GraphQL schema, a proto file or a codebase, in one command, with any model including local ones. A server it generates from the Petstore spec, without a model, scores 95.

Code: https://github.com/gabrielekarra/mcp-anything

---

Checklist before posting:

- [ ] Leaderboard run on real servers and committed, with the date.
- [ ] Every number in the post copied from the leaderboard.
- [ ] Each graded server's authors would agree the finding is fair: open an issue on any that looks wrong before posting.
- [ ] The demo GIF recorded and in the README.
- [ ] v0.3.0 on PyPI, so `pip install mcp-anything` gets the grader.
