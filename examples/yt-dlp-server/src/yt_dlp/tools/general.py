"""general tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register general tools with the server."""

    @server.tool()
    async def identity(
        x: str,
    ) -> str:
        """IDENTITY"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("identity")

    @server.tool()
    async def aes_cbc_decrypt(
        data: str,
        key: str,
        iv: str,
    ) -> str:
        """Decrypt with aes in CBC mode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_cbc_decrypt")

    @server.tool()
    async def aes_cbc_encrypt(
        data: str,
        key: str,
        iv: str,
        padding_mode: str | None = "pkcs7",
    ) -> str:
        """Encrypt with aes in CBC mode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_cbc_encrypt")

    @server.tool()
    async def aes_cbc_encrypt_bytes(
        data: str,
        key: str,
        iv: str,
    ) -> str:
        """Aes cbc encrypt bytes"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_cbc_encrypt_bytes")

    @server.tool()
    async def aes_ctr_decrypt(
        data: str,
        key: str,
        iv: str,
    ) -> str:
        """Decrypt with aes in counter mode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_ctr_decrypt")

    @server.tool()
    async def aes_ctr_encrypt(
        data: str,
        key: str,
        iv: str,
    ) -> str:
        """Encrypt with aes in counter mode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_ctr_encrypt")

    @server.tool()
    async def aes_decrypt(
        data: str,
        expanded_key: str,
    ) -> str:
        """Decrypt one block with aes"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_decrypt")

    @server.tool()
    async def aes_decrypt_text(
        data: str,
        password: str,
        key_size_bytes: str,
    ) -> str:
        """Decrypt text"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_decrypt_text")

    @server.tool()
    async def aes_ecb_decrypt(
        data: str,
        key: str,
        iv: str | None = None,
    ) -> str:
        """Decrypt with aes in ECB mode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_ecb_decrypt")

    @server.tool()
    async def aes_ecb_encrypt(
        data: str,
        key: str,
        iv: str | None = None,
    ) -> str:
        """Encrypt with aes in ECB mode. Using PKCS#7 padding"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_ecb_encrypt")

    @server.tool()
    async def aes_encrypt(
        data: str,
        expanded_key: str,
    ) -> str:
        """Encrypt one block with aes"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_encrypt")

    @server.tool()
    async def aes_gcm_decrypt_and_verify(
        data: str,
        key: str,
        tag: str,
        nonce: str,
    ) -> str:
        """Decrypt with aes in GBM mode and checks authenticity using tag"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aes_gcm_decrypt_and_verify")

    @server.tool()
    async def age_restricted(
        content_limit: str,
        age_limit: str,
    ) -> str:
        """Returns True iff the content should be blocked"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("age_restricted")

    @server.tool()
    async def args_to_str(
        args: str,
    ) -> str:
        """Args to str"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("args_to_str")

    @server.tool()
    async def ass_subtitles_timecode(
        seconds: str,
    ) -> str:
        """Ass subtitles timecode"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("ass_subtitles_timecode")

    @server.tool()
    async def base_url(
        url: str,
    ) -> str:
        """Base url"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("base_url")

    @server.tool()
    async def block_product(
        block_x: str,
        block_y: str,
    ) -> str:
        """Block product"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("block_product")

    @server.tool()
    async def bool_or_none(
        v: str,
        default: str | None = None,
    ) -> str:
        """Bool or none"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bool_or_none")

    @server.tool()
    async def box(
        box_type: str,
        payload: str,
    ) -> str:
        """Box"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("box")

    @server.tool()
    async def bug_reports_message(
        before: str | None = ";",
    ) -> str:
        """Bug reports message"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bug_reports_message")

    @server.tool()
    async def build_fragments_list(
        boot_info: str,
    ) -> str:
        """Return a list of (segment, fragment) for each fragment in the video"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("build_fragments_list")

    @server.tool()
    async def bytes_to_intlist(
        bs: str,
    ) -> str:
        """Bytes to intlist"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bytes_to_intlist")

    @server.tool()
    async def bytes_to_long(
        s: str,
    ) -> str:
        """bytes_to_long(string) : long"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bytes_to_long")

    @server.tool()
    async def caesar(
        s: str,
        alphabet: str,
        shift: str,
    ) -> str:
        """Caesar"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("caesar")

    @server.tool()
    async def candidate_plugin_paths(
        candidate: str,
    ) -> str:
        """Candidate plugin paths"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("candidate_plugin_paths")

