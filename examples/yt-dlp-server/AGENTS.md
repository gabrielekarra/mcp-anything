# yt-dlp MCP Server

MCP server for yt-dlp (with 50 capabilities)

## Available Tools

### identity

IDENTITY

Parameters:
- `x` (string): 
### a_cast_channel_ie_suitable

Suitable

Parameters:
- `url` (string): 
### add_accept_encoding_header

Add accept encoding header

Parameters:
- `headers` (HTTPHeaderDict): 
- `supported_encodings` (Iterable): 
### aes_cbc_decrypt

Decrypt with aes in CBC mode

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string): 
### aes_cbc_encrypt

Encrypt with aes in CBC mode

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string): 
- `padding_mode` (string, optional):  (default: pkcs7)
### aes_cbc_encrypt_bytes

Aes cbc encrypt bytes

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string): 
### aes_ctr_decrypt

Decrypt with aes in counter mode

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string): 
### aes_ctr_encrypt

Encrypt with aes in counter mode

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string): 
### aes_decrypt

Decrypt one block with aes

Parameters:
- `data` (string): 
- `expanded_key` (string): 
### aes_decrypt_text

Decrypt text

Parameters:
- `data` (string): 
- `password` (string): 
- `key_size_bytes` (string): 
### aes_ecb_decrypt

Decrypt with aes in ECB mode

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string, optional): 
### aes_ecb_encrypt

Encrypt with aes in ECB mode. Using PKCS#7 padding

Parameters:
- `data` (string): 
- `key` (string): 
- `iv` (string, optional): 
### aes_encrypt

Encrypt one block with aes

Parameters:
- `data` (string): 
- `expanded_key` (string): 
### aes_gcm_decrypt_and_verify

Decrypt with aes in GBM mode and checks authenticity using tag

Parameters:
- `data` (string): 
- `key` (string): 
- `tag` (string): 
- `nonce` (string): 
### age_restricted

Returns True iff the content should be blocked 

Parameters:
- `content_limit` (string): 
- `age_limit` (string): 
### alura_course_ie_suitable

Suitable

Parameters:
- `url` (string): 
### andere_tijden_ie_suitable

Suitable

Parameters:
- `url` (string): 
### args_to_str

Args to str

Parameters:
- `args` (string): 
### aria2c_fd_aria2c_rpc

Aria2c rpc

Parameters:
- `rpc_port` (string): 
- `rpc_secret` (string): 
- `method` (string): 
- `params` (string, optional): 
### aria2c_fd_supports_manifest

Supports manifest

Parameters:
- `manifest` (string): 
### arte_tv_category_ie_suitable

Suitable

Parameters:
- `url` (string): 
### ass_subtitles_timecode

Ass subtitles timecode

Parameters:
- `seconds` (string): 
### aws_idp_authenticate

Authenticate with a username and password. 

Parameters:
- `username` (string): 
- `password` (string): 
### bandcamp_album_ie_suitable

Suitable

Parameters:
- `url` (string): 
### base_url

Base url

Parameters:
- `url` (string): 
### bbcie_suitable

Suitable

Parameters:
- `url` (string): 
### bbvtv_live_ie_suitable

Suitable

Parameters:
- `url` (string): 
### bili_intl_base_ie_json2srt

Json2srt

Parameters:
- `json` (string): 
### bilibili_base_ie_extract_formats

Extract formats

Parameters:
- `play_info` (string): 
### bilibili_base_ie_is_logged_in

Is logged in

### bilibili_base_ie_json2srt

Json2srt

Parameters:
- `json_data` (string): 
### bilibili_collection_list_ie_suitable

Suitable

Parameters:
- `url` (string): 
### block_parse

Parse

Parameters:
- `parser` (string): 
### block_product

Block product

Parameters:
- `block_x` (string): 
- `block_y` (string): 
### block_write_into

Write into

Parameters:
- `stream` (string): 
### bool_or_none

Bool or none

Parameters:
- `v` (string): 
- `default` (string, optional): 
### box

Box

Parameters:
- `box_type` (string): 
- `payload` (string): 
### breakline_status_printer_print_at_line

Print at line

Parameters:
- `text` (string): 
- `pos` (string): 
### bug_reports_message

Bug reports message

Parameters:
- `before` (string, optional):  (default: ;)
### build_fragments_list

Return a list of (segment, fragment) for each fragment in the video 

Parameters:
- `boot_info` (string): 
### bunny_cdn_fd_ping_thread

Ping thread

Parameters:
- `stop_event` (string): 
- `url` (string): 
- `headers` (string): 
- `secret` (string): 
- `context_id` (string): 
### bunny_cdn_fd_real_download

Real download

Parameters:
- `filename` (string): 
- `info_dict` (string): 
### bytes_to_intlist

Bytes to intlist

Parameters:
- `bs` (string): 
### bytes_to_long

bytes_to_long(string) : long

Parameters:
- `s` (string): 
### cache_enabled

Enabled

### cache_load

Load

Parameters:
- `section` (string): 
- `key` (string): 
- `dtype` (string, optional):  (default: json)
- `default` (string, optional): 
- `min_ver` (string, optional): 
### cache_store

Store

Parameters:
- `section` (string): 
- `key` (string): 
- `data` (string): 
- `dtype` (string, optional):  (default: json)
### caesar

Caesar

Parameters:
- `s` (string): 
- `alphabet` (string): 
- `shift` (string): 
### callin_ie_try_get_user_name

Try get user name

Parameters:
- `d` (string): 
### candidate_plugin_paths

Candidate plugin paths

Parameters:
- `candidate` (string): 

## Available Resources

- `app://yt-dlp/status` — Current status and version of yt-dlp
- `app://yt-dlp/commands` — Available commands and tools in yt-dlp
- `docs://yt-dlp/tool-index` — Complete index of all yt-dlp tools with parameters and usage
- `docs://yt-dlp/a_cast_channel_ie` — Documentation for yt-dlp a_cast_channel_ie capabilities
- `docs://yt-dlp/alura_course_ie` — Documentation for yt-dlp alura_course_ie capabilities
- `docs://yt-dlp/andere_tijden_ie` — Documentation for yt-dlp andere_tijden_ie capabilities
- `docs://yt-dlp/aria2c_fd` — Documentation for yt-dlp aria2c_fd capabilities
- `docs://yt-dlp/arte_tv_category_ie` — Documentation for yt-dlp arte_tv_category_ie capabilities

## Available Prompts

- `use_yt_dlp` — Guide for using yt-dlp tools effectively
- `debug_yt_dlp` — Diagnose issues with yt-dlp operations

## Usage

This server runs over stdio. Add it to your MCP client config:

```json
{
  "mcpServers": {
    "yt-dlp": {
      "command": "mcp-yt-dlp"
    }
  }
}
```
