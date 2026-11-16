# Records the README demo with VHS: https://github.com/charmbracelet/vhs
#   vhs docs/demo.tape
# Needs mcp-anything installed and network access. Produces docs/demo.gif.

Output docs/demo.gif
Set FontSize 16
Set Width 1300
Set Height 720
Set Theme "Dracula"
Set TypingSpeed 40ms

Type "mcp-anything https://petstore3.swagger.io/api/v3/openapi.json --no-llm -o petstore"
Enter
Sleep 12s
Type "mcp-anything grade petstore"
Enter
Sleep 6s
Type "mcp-anything install petstore --client claude-code"
Enter
Sleep 4s
