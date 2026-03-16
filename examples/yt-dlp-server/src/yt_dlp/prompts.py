"""Server-delivered MCP prompts (skills) for yt-dlp."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_yt_dlp")
    async def use_yt_dlp_prompt() -> str:
        """Guide for using yt-dlp tools effectively"""
        return """You have access to the yt-dlp MCP server with these tools:

- IDENTITY: IDENTITY
- a_cast_channel_ie_suitable: Suitable
- add_accept_encoding_header: Add accept encoding header
- aes_cbc_decrypt: Decrypt with aes in CBC mode
- aes_cbc_encrypt: Encrypt with aes in CBC mode
- aes_cbc_encrypt_bytes: Aes cbc encrypt bytes
- aes_ctr_decrypt: Decrypt with aes in counter mode
- aes_ctr_encrypt: Encrypt with aes in counter mode
- aes_decrypt: Decrypt one block with aes
- aes_decrypt_text: Decrypt text
- aes_ecb_decrypt: Decrypt with aes in ECB mode
- aes_ecb_encrypt: Encrypt with aes in ECB mode. Using PKCS#7 padding
- aes_encrypt: Encrypt one block with aes
- aes_gcm_decrypt_and_verify: Decrypt with aes in GBM mode and checks authenticity using tag
- age_restricted: Returns True iff the content should be blocked 
- alura_course_ie_suitable: Suitable
- andere_tijden_ie_suitable: Suitable
- args_to_str: Args to str
- aria2c_fd_aria2c_rpc: Aria2c rpc
- aria2c_fd_supports_manifest: Supports manifest

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_yt_dlp")
    async def debug_yt_dlp_prompt(error_message: str) -> str:
        """Diagnose issues with yt-dlp operations"""
        return """The user encountered an error while using yt-dlp.

Error: {{error_message}}

Available tools: IDENTITY, a_cast_channel_ie_suitable, add_accept_encoding_header, aes_cbc_decrypt, aes_cbc_encrypt, aes_cbc_encrypt_bytes, aes_ctr_decrypt, aes_ctr_encrypt, aes_decrypt, aes_decrypt_text, aes_ecb_decrypt, aes_ecb_encrypt, aes_encrypt, aes_gcm_decrypt_and_verify, age_restricted

Diagnose the issue and suggest which tool to use to resolve it."""

