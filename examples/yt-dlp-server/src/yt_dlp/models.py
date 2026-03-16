"""Data models for yt-dlp MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class IdentityParams:
    """Parameters for identity."""
    x: str

@dataclass
class ACastChannelIeSuitableParams:
    """Parameters for a_cast_channel_ie_suitable."""
    url: str

@dataclass
class AddAcceptEncodingHeaderParams:
    """Parameters for add_accept_encoding_header."""
    headers: str
    supported_encodings: str

@dataclass
class AesCbcDecryptParams:
    """Parameters for aes_cbc_decrypt."""
    data: str
    key: str
    iv: str

@dataclass
class AesCbcEncryptParams:
    """Parameters for aes_cbc_encrypt."""
    data: str
    key: str
    iv: str
    padding_mode: str | None = None

@dataclass
class AesCbcEncryptBytesParams:
    """Parameters for aes_cbc_encrypt_bytes."""
    data: str
    key: str
    iv: str

@dataclass
class AesCtrDecryptParams:
    """Parameters for aes_ctr_decrypt."""
    data: str
    key: str
    iv: str

@dataclass
class AesCtrEncryptParams:
    """Parameters for aes_ctr_encrypt."""
    data: str
    key: str
    iv: str

@dataclass
class AesDecryptParams:
    """Parameters for aes_decrypt."""
    data: str
    expanded_key: str

@dataclass
class AesDecryptTextParams:
    """Parameters for aes_decrypt_text."""
    data: str
    password: str
    key_size_bytes: str

@dataclass
class AesEcbDecryptParams:
    """Parameters for aes_ecb_decrypt."""
    data: str
    key: str
    iv: str | None = None

@dataclass
class AesEcbEncryptParams:
    """Parameters for aes_ecb_encrypt."""
    data: str
    key: str
    iv: str | None = None

@dataclass
class AesEncryptParams:
    """Parameters for aes_encrypt."""
    data: str
    expanded_key: str

@dataclass
class AesGcmDecryptAndVerifyParams:
    """Parameters for aes_gcm_decrypt_and_verify."""
    data: str
    key: str
    tag: str
    nonce: str

@dataclass
class AgeRestrictedParams:
    """Parameters for age_restricted."""
    content_limit: str
    age_limit: str

@dataclass
class AluraCourseIeSuitableParams:
    """Parameters for alura_course_ie_suitable."""
    url: str

@dataclass
class AndereTijdenIeSuitableParams:
    """Parameters for andere_tijden_ie_suitable."""
    url: str

@dataclass
class ArgsToStrParams:
    """Parameters for args_to_str."""
    args: str

@dataclass
class Aria2cFdAria2cRpcParams:
    """Parameters for aria2c_fd_aria2c_rpc."""
    rpc_port: str
    rpc_secret: str
    method: str
    params: str | None = None

@dataclass
class Aria2cFdSupportsManifestParams:
    """Parameters for aria2c_fd_supports_manifest."""
    manifest: str

@dataclass
class ArteTvCategoryIeSuitableParams:
    """Parameters for arte_tv_category_ie_suitable."""
    url: str

@dataclass
class AssSubtitlesTimecodeParams:
    """Parameters for ass_subtitles_timecode."""
    seconds: str

@dataclass
class AwsIdpAuthenticateParams:
    """Parameters for aws_idp_authenticate."""
    username: str
    password: str

@dataclass
class BandcampAlbumIeSuitableParams:
    """Parameters for bandcamp_album_ie_suitable."""
    url: str

@dataclass
class BaseUrlParams:
    """Parameters for base_url."""
    url: str

@dataclass
class BbcieSuitableParams:
    """Parameters for bbcie_suitable."""
    url: str

@dataclass
class BbvtvLiveIeSuitableParams:
    """Parameters for bbvtv_live_ie_suitable."""
    url: str

@dataclass
class BiliIntlBaseIeJson2srtParams:
    """Parameters for bili_intl_base_ie_json2srt."""
    json: str

@dataclass
class BilibiliBaseIeExtractFormatsParams:
    """Parameters for bilibili_base_ie_extract_formats."""
    play_info: str

@dataclass
class BilibiliBaseIeJson2srtParams:
    """Parameters for bilibili_base_ie_json2srt."""
    json_data: str

@dataclass
class BilibiliCollectionListIeSuitableParams:
    """Parameters for bilibili_collection_list_ie_suitable."""
    url: str

@dataclass
class BlockParseParams:
    """Parameters for block_parse."""
    parser: str

@dataclass
class BlockProductParams:
    """Parameters for block_product."""
    block_x: str
    block_y: str

@dataclass
class BlockWriteIntoParams:
    """Parameters for block_write_into."""
    stream: str

@dataclass
class BoolOrNoneParams:
    """Parameters for bool_or_none."""
    v: str
    default: str | None = None

@dataclass
class BoxParams:
    """Parameters for box."""
    box_type: str
    payload: str

@dataclass
class BreaklineStatusPrinterPrintAtLineParams:
    """Parameters for breakline_status_printer_print_at_line."""
    text: str
    pos: str

@dataclass
class BugReportsMessageParams:
    """Parameters for bug_reports_message."""
    before: str | None = None

@dataclass
class BuildFragmentsListParams:
    """Parameters for build_fragments_list."""
    boot_info: str

@dataclass
class BunnyCdnFdPingThreadParams:
    """Parameters for bunny_cdn_fd_ping_thread."""
    stop_event: str
    url: str
    headers: str
    secret: str
    context_id: str

@dataclass
class BunnyCdnFdRealDownloadParams:
    """Parameters for bunny_cdn_fd_real_download."""
    filename: str
    info_dict: str

@dataclass
class BytesToIntlistParams:
    """Parameters for bytes_to_intlist."""
    bs: str

@dataclass
class BytesToLongParams:
    """Parameters for bytes_to_long."""
    s: str

@dataclass
class CacheLoadParams:
    """Parameters for cache_load."""
    section: str
    key: str
    dtype: str | None = None
    default: str | None = None
    min_ver: str | None = None

@dataclass
class CacheStoreParams:
    """Parameters for cache_store."""
    section: str
    key: str
    data: str
    dtype: str | None = None

@dataclass
class CaesarParams:
    """Parameters for caesar."""
    s: str
    alphabet: str
    shift: str

@dataclass
class CallinIeTryGetUserNameParams:
    """Parameters for callin_ie_try_get_user_name."""
    d: str

@dataclass
class CandidatePluginPathsParams:
    """Parameters for candidate_plugin_paths."""
    candidate: str

