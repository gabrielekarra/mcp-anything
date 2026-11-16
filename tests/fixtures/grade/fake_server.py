"""A tiny MCP server on stdio that lists the tools of a JSON file, two per page."""

import json
import sys

tools = json.load(open(sys.argv[1]))["tools"]
for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    if message["method"] == "initialize":
        result = {"protocolVersion": message["params"]["protocolVersion"], "capabilities": {"tools": {}},
                  "serverInfo": {"name": "fake", "version": "1"}}
    elif message["method"] == "tools/list":
        start = int((message.get("params") or {}).get("cursor") or 0)
        result = {"tools": tools[start:start + 2]}
        if start + 2 < len(tools):
            result["nextCursor"] = str(start + 2)
    else:
        result = {}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
