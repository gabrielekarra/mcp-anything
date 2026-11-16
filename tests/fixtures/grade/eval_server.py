"""A small MCP server on stdio whose tools really answer, for the eval tests."""

import json
import sys

TOOLS = json.load(open(sys.argv[1]))["tools"]


def call(name, args):
    if name == "search_issues":
        return {"content": [{"type": "text", "text": f"Found 2 issues matching {args.get('query')!r}: #12, #15"}]}
    if name == "manage_issue":
        if "operation" not in args:
            return {"content": [{"type": "text", "text": "Error: missing required argument operation"}], "isError": True}
        return {"content": [{"type": "text", "text": f"Issue {args.get('number', 99)}: {args['operation']} done"}]}
    if name == "delete_comment":
        return {"content": [{"type": "text", "text": f"Deleted comment {args.get('comment_id')}"}]}
    return {"content": [{"type": "text", "text": f"Unknown tool {name}"}], "isError": True}


for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    method, params = message["method"], message.get("params") or {}
    if method == "initialize":
        result = {"protocolVersion": params["protocolVersion"], "capabilities": {"tools": {}}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        result = call(params["name"], params.get("arguments") or {})
    else:
        result = {}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
