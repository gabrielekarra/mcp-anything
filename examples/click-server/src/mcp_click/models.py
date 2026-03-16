"""Data models for click MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RunClickParams:
    """Parameters for run_click."""
    args: str

@dataclass
class AddCompletionClassParams:
    """Parameters for add_completion_class."""
    name: str | None = None

@dataclass
class ArgumentAddToParserParams:
    """Parameters for argument_add_to_parser."""
    parser: str
    ctx: str

@dataclass
class ArgumentGetErrorHintParams:
    """Parameters for argument_get_error_hint."""
    ctx: str

@dataclass
class ArgumentGetUsagePiecesParams:
    """Parameters for argument_get_usage_pieces."""
    ctx: str

@dataclass
class ArgumentMakeMetavarParams:
    """Parameters for argument_make_metavar."""
    ctx: str

@dataclass
class AugmentUsageErrorsParams:
    """Parameters for augment_usage_errors."""
    ctx: str
    param: str | None = None

@dataclass
class BashCompleteFormatCompletionParams:
    """Parameters for bash_complete_format_completion."""
    item: str

@dataclass
class BatchParams:
    """Parameters for batch."""
    iterable: str
    batch_size: int

@dataclass
class BoolParamTypeConvertParams:
    """Parameters for bool_param_type_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class BoolParamTypeStrToBoolParams:
    """Parameters for bool_param_type_str_to_bool."""
    value: str

@dataclass
class BytesIoCopyWriteParams:
    """Parameters for bytes_io_copy_write."""
    b: str

@dataclass
class ChoiceConvertParams:
    """Parameters for choice_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class ChoiceGetInvalidChoiceMessageParams:
    """Parameters for choice_get_invalid_choice_message."""
    value: str
    ctx: str

@dataclass
class ChoiceGetMetavarParams:
    """Parameters for choice_get_metavar."""
    param: str
    ctx: str

@dataclass
class ChoiceGetMissingMessageParams:
    """Parameters for choice_get_missing_message."""
    param: str
    ctx: str

@dataclass
class ChoiceNormalizeChoiceParams:
    """Parameters for choice_normalize_choice."""
    choice: str
    ctx: str

@dataclass
class ChoiceShellCompleteParams:
    """Parameters for choice_shell_complete."""
    ctx: str
    param: str
    incomplete: str

@dataclass
class CliRunnerGetDefaultProgNameParams:
    """Parameters for cli_runner_get_default_prog_name."""
    cli: str

@dataclass
class CliRunnerIsolatedFilesystemParams:
    """Parameters for cli_runner_isolated_filesystem."""
    temp_dir: str | None = None

@dataclass
class CliRunnerMakeEnvParams:
    """Parameters for cli_runner_make_env."""
    overrides: str | None = None

@dataclass
class ClickExceptionShowParams:
    """Parameters for click_exception_show."""
    file: str | None = None

@dataclass
class CommandParams:
    """Parameters for command."""
    name: str

@dataclass
class CommandCollectUsagePiecesParams:
    """Parameters for command_collect_usage_pieces."""
    ctx: str

@dataclass
class CommandCollectionAddSourceParams:
    """Parameters for command_collection_add_source."""
    group: str

@dataclass
class CommandCollectionGetCommandParams:
    """Parameters for command_collection_get_command."""
    ctx: str
    cmd_name: str

@dataclass
class CommandCollectionListCommandsParams:
    """Parameters for command_collection_list_commands."""
    ctx: str

@dataclass
class CommandFormatEpilogParams:
    """Parameters for command_format_epilog."""
    ctx: str
    formatter: str

@dataclass
class CommandFormatHelpParams:
    """Parameters for command_format_help."""
    ctx: str
    formatter: str

@dataclass
class CommandFormatHelpTextParams:
    """Parameters for command_format_help_text."""
    ctx: str
    formatter: str

@dataclass
class CommandFormatOptionsParams:
    """Parameters for command_format_options."""
    ctx: str
    formatter: str

@dataclass
class CommandFormatUsageParams:
    """Parameters for command_format_usage."""
    ctx: str
    formatter: str

@dataclass
class CommandGetHelpParams:
    """Parameters for command_get_help."""
    ctx: str

@dataclass
class CommandGetHelpOptionParams:
    """Parameters for command_get_help_option."""
    ctx: str

@dataclass
class CommandGetHelpOptionNamesParams:
    """Parameters for command_get_help_option_names."""
    ctx: str

@dataclass
class CommandGetParamsParams:
    """Parameters for command_get_params."""
    ctx: str

@dataclass
class CommandGetShortHelpStrParams:
    """Parameters for command_get_short_help_str."""
    limit: int | None = None

@dataclass
class CommandGetUsageParams:
    """Parameters for command_get_usage."""
    ctx: str

@dataclass
class CommandMakeContextParams:
    """Parameters for command_make_context."""
    info_name: str
    args: list
    parent: str | None = None

@dataclass
class CommandMakeParserParams:
    """Parameters for command_make_parser."""
    ctx: str

@dataclass
class CommandShellCompleteParams:
    """Parameters for command_shell_complete."""
    ctx: str
    incomplete: str

@dataclass
class CommandToInfoDictParams:
    """Parameters for command_to_info_dict."""
    ctx: str

@dataclass
class ConfirmParams:
    """Parameters for confirm."""
    text: str
    default: bool | None = None
    abort: bool | None = None
    prompt_suffix: str | None = None
    show_default: bool | None = None
    err: bool | None = None

@dataclass
class ConsoleStreamWriteParams:
    """Parameters for console_stream_write."""
    x: str

@dataclass
class ConsoleStreamWritelinesParams:
    """Parameters for console_stream_writelines."""
    lines: str

@dataclass
class ContextCallOnCloseParams:
    """Parameters for context_call_on_close."""
    f: str

@dataclass
class ContextEnsureObjectParams:
    """Parameters for context_ensure_object."""
    object_type: str

@dataclass
class ContextExitParams:
    """Parameters for context_exit."""
    code: int | None = None

@dataclass
class ContextFailParams:
    """Parameters for context_fail."""
    message: str

@dataclass
class ContextFindObjectParams:
    """Parameters for context_find_object."""
    object_type: str

@dataclass
class ContextGetParameterSourceParams:
    """Parameters for context_get_parameter_source."""
    name: str

@dataclass
class ContextLookupDefaultParams:
    """Parameters for context_lookup_default."""
    name: str
    call: str | None = None

@dataclass
class ContextScopeParams:
    """Parameters for context_scope."""
    cleanup: bool | None = None

@dataclass
class ContextSetParameterSourceParams:
    """Parameters for context_set_parameter_source."""
    name: str
    source: str

@dataclass
class ContextWithResourceParams:
    """Parameters for context_with_resource."""
    context_manager: str

@dataclass
class ConvertTypeParams:
    """Parameters for convert_type."""
    ty: str
    default: str | None = None

@dataclass
class DateTimeConvertParams:
    """Parameters for date_time_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class DateTimeGetMetavarParams:
    """Parameters for date_time_get_metavar."""
    param: str
    ctx: str

@dataclass
class EchoParams:
    """Parameters for echo."""
    message: str | None = None
    file: str | None = None
    nl: bool | None = None
    err: bool | None = None
    color: bool | None = None

@dataclass
class EchoViaPagerParams:
    """Parameters for echo_via_pager."""
    text_or_generator: str
    color: bool | None = None

@dataclass
class EchoingStdinReadParams:
    """Parameters for echoing_stdin_read."""
    n: int | None = None

@dataclass
class EchoingStdinRead1Params:
    """Parameters for echoing_stdin_read1."""
    n: int | None = None

@dataclass
class EchoingStdinReadlineParams:
    """Parameters for echoing_stdin_readline."""
    n: int | None = None

@dataclass
class EditParams:
    """Parameters for edit."""
    text: str
    editor: str | None = None
    env: str | None = None
    require_save: bool | None = None
    extension: str | None = None

@dataclass
class EditorEditParams:
    """Parameters for editor_edit."""
    text: str

@dataclass
class EditorEditFilesParams:
    """Parameters for editor_edit_files."""
    filenames: str

@dataclass
class FileConvertParams:
    """Parameters for file_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class FileResolveLazyFlagParams:
    """Parameters for file_resolve_lazy_flag."""
    value: str

@dataclass
class FileShellCompleteParams:
    """Parameters for file_shell_complete."""
    ctx: str
    param: str
    incomplete: str

@dataclass
class FishCompleteFormatCompletionParams:
    """Parameters for fish_complete_format_completion."""
    item: str

@dataclass
class FormatFilenameParams:
    """Parameters for format_filename."""
    filename: str
    shorten: bool | None = None

@dataclass
class FuncParamTypeConvertParams:
    """Parameters for func_param_type_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class GetAppDirParams:
    """Parameters for get_app_dir."""
    app_name: str
    roaming: bool | None = None
    force_posix: bool | None = None

@dataclass
class GetBestEncodingParams:
    """Parameters for get_best_encoding."""
    stream: str

@dataclass
class GetBinaryStreamParams:
    """Parameters for get_binary_stream."""
    name: str

@dataclass
class GetCompletionClassParams:
    """Parameters for get_completion_class."""
    shell: str

@dataclass
class GetCurrentContextParams:
    """Parameters for get_current_context."""
    silent: str | None = None

@dataclass
class GetTextStderrParams:
    """Parameters for get_text_stderr."""
    encoding: str | None = None
    errors: str | None = None

@dataclass
class GetTextStdinParams:
    """Parameters for get_text_stdin."""
    encoding: str | None = None
    errors: str | None = None

@dataclass
class GetTextStdoutParams:
    """Parameters for get_text_stdout."""
    encoding: str | None = None
    errors: str | None = None

@dataclass
class GetTextStreamParams:
    """Parameters for get_text_stream."""
    name: str
    encoding: str | None = None
    errors: str | None = None

@dataclass
class GetcharParams:
    """Parameters for getchar."""
    echo: bool | None = None

@dataclass
class GroupParams:
    """Parameters for group."""
    name: str

@dataclass
class GroupAddCommandParams:
    """Parameters for group_add_command."""
    cmd: str
    name: str | None = None

@dataclass
class GroupCollectUsagePiecesParams:
    """Parameters for group_collect_usage_pieces."""
    ctx: str

@dataclass
class GroupCommandParams:
    """Parameters for group_command."""
    func: str

@dataclass
class GroupFormatCommandsParams:
    """Parameters for group_format_commands."""
    ctx: str
    formatter: str

@dataclass
class GroupFormatOptionsParams:
    """Parameters for group_format_options."""
    ctx: str
    formatter: str

@dataclass
class GroupGetCommandParams:
    """Parameters for group_get_command."""
    ctx: str
    cmd_name: str

@dataclass
class GroupGroupParams:
    """Parameters for group_group."""
    func: str

@dataclass
class GroupListCommandsParams:
    """Parameters for group_list_commands."""
    ctx: str

@dataclass
class GroupResolveCommandParams:
    """Parameters for group_resolve_command."""
    ctx: str
    args: list

@dataclass
class GroupShellCompleteParams:
    """Parameters for group_shell_complete."""
    ctx: str
    incomplete: str

@dataclass
class GroupToInfoDictParams:
    """Parameters for group_to_info_dict."""
    ctx: str

@dataclass
class HelpFormatterSectionParams:
    """Parameters for help_formatter_section."""
    name: str

@dataclass
class HelpFormatterWriteParams:
    """Parameters for help_formatter_write."""
    string: str

@dataclass
class HelpFormatterWriteDlParams:
    """Parameters for help_formatter_write_dl."""
    rows: str
    col_max: int | None = None
    col_spacing: int | None = None

@dataclass
class HelpFormatterWriteHeadingParams:
    """Parameters for help_formatter_write_heading."""
    heading: str

@dataclass
class HelpFormatterWriteTextParams:
    """Parameters for help_formatter_write_text."""
    text: str

@dataclass
class HelpFormatterWriteUsageParams:
    """Parameters for help_formatter_write_usage."""
    prog: str
    args: str | None = None
    prefix: str | None = None

@dataclass
class HiddenPromptFuncParams:
    """Parameters for hidden_prompt_func."""
    prompt: str

@dataclass
class IsAsciiEncodingParams:
    """Parameters for is_ascii_encoding."""
    encoding: str

@dataclass
class IsattyParams:
    """Parameters for isatty."""
    stream: str

@dataclass
class IterParamsForProcessingParams:
    """Parameters for iter_params_for_processing."""
    invocation_order: str
    declaration_order: str

@dataclass
class IterRowsParams:
    """Parameters for iter_rows."""
    rows: str
    col_count: int

@dataclass
class JoinOptionsParams:
    """Parameters for join_options."""
    options: str

@dataclass
class LaunchParams:
    """Parameters for launch."""
    url: str
    wait: bool | None = None
    locate: bool | None = None

@dataclass
class MakeDefaultShortHelpParams:
    """Parameters for make_default_short_help."""
    help: str
    max_length: int | None = None

@dataclass
class MakeInputStreamParams:
    """Parameters for make_input_stream."""
    input: str
    charset: str

@dataclass
class MakeStrParams:
    """Parameters for make_str."""
    value: str

@dataclass
class MeasureTableParams:
    """Parameters for measure_table."""
    rows: str

@dataclass
class NoArgsIsHelpErrorShowParams:
    """Parameters for no_args_is_help_error_show."""
    file: str | None = None

@dataclass
class OpenFileParams:
    """Parameters for open_file."""
    filename: str
    mode: str | None = None
    encoding: str | None = None
    errors: str | None = None
    lazy: bool | None = None
    atomic: bool | None = None

@dataclass
class OpenStreamParams:
    """Parameters for open_stream."""
    filename: str
    mode: str | None = None
    encoding: str | None = None
    errors: str | None = None
    atomic: bool | None = None

@dataclass
class OptionAddToParserParams:
    """Parameters for option_add_to_parser."""
    parser: str
    ctx: str

@dataclass
class OptionConsumeValueParams:
    """Parameters for option_consume_value."""
    ctx: str
    opts: str

@dataclass
class OptionGetErrorHintParams:
    """Parameters for option_get_error_hint."""
    ctx: str

@dataclass
class OptionGetHelpExtraParams:
    """Parameters for option_get_help_extra."""
    ctx: str

@dataclass
class OptionProcessValueParams:
    """Parameters for option_process_value."""
    ctx: str
    value: str

@dataclass
class OptionPromptForValueParams:
    """Parameters for option_prompt_for_value."""
    ctx: str

@dataclass
class OptionResolveEnvvarValueParams:
    """Parameters for option_resolve_envvar_value."""
    ctx: str

@dataclass
class OptionValueFromEnvvarParams:
    """Parameters for option_value_from_envvar."""
    ctx: str

@dataclass
class PagerParams:
    """Parameters for pager."""
    generator: str
    color: bool | None = None

@dataclass
class ParamTypeConvertParams:
    """Parameters for param_type_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class ParamTypeFailParams:
    """Parameters for param_type_fail."""
    message: str
    param: str | None = None
    ctx: str | None = None

@dataclass
class ParamTypeGetMetavarParams:
    """Parameters for param_type_get_metavar."""
    param: str
    ctx: str

@dataclass
class ParamTypeGetMissingMessageParams:
    """Parameters for param_type_get_missing_message."""
    param: str
    ctx: str

@dataclass
class ParamTypeShellCompleteParams:
    """Parameters for param_type_shell_complete."""
    ctx: str
    param: str
    incomplete: str

@dataclass
class ParamTypeSplitEnvvarValueParams:
    """Parameters for param_type_split_envvar_value."""
    rv: str

@dataclass
class ParameterAddToParserParams:
    """Parameters for parameter_add_to_parser."""
    parser: str
    ctx: str

@dataclass
class ParameterConsumeValueParams:
    """Parameters for parameter_consume_value."""
    ctx: str
    opts: str

@dataclass
class ParameterGetDefaultParams:
    """Parameters for parameter_get_default."""
    ctx: str
    call: str | None = None

@dataclass
class ParameterGetErrorHintParams:
    """Parameters for parameter_get_error_hint."""
    ctx: str

@dataclass
class ParameterGetHelpRecordParams:
    """Parameters for parameter_get_help_record."""
    ctx: str

@dataclass
class ParameterGetUsagePiecesParams:
    """Parameters for parameter_get_usage_pieces."""
    ctx: str

@dataclass
class ParameterHandleParseResultParams:
    """Parameters for parameter_handle_parse_result."""
    ctx: str
    opts: str
    args: list

@dataclass
class ParameterMakeMetavarParams:
    """Parameters for parameter_make_metavar."""
    ctx: str

@dataclass
class ParameterProcessValueParams:
    """Parameters for parameter_process_value."""
    ctx: str
    value: str

@dataclass
class ParameterResolveEnvvarValueParams:
    """Parameters for parameter_resolve_envvar_value."""
    ctx: str

@dataclass
class ParameterShellCompleteParams:
    """Parameters for parameter_shell_complete."""
    ctx: str
    incomplete: str

@dataclass
class ParameterValueFromEnvvarParams:
    """Parameters for parameter_value_from_envvar."""
    ctx: str

@dataclass
class ParameterValueIsMissingParams:
    """Parameters for parameter_value_is_missing."""
    value: str

@dataclass
class PassContextParams:
    """Parameters for pass_context."""
    f: str

@dataclass
class PassObjParams:
    """Parameters for pass_obj."""
    f: str

@dataclass
class PathCoercePathResultParams:
    """Parameters for path_coerce_path_result."""
    value: str

@dataclass
class PathConvertParams:
    """Parameters for path_convert."""
    value: str
    param: str
    ctx: str

@dataclass
class PathShellCompleteParams:
    """Parameters for path_shell_complete."""
    ctx: str
    param: str
    incomplete: str

@dataclass
class PauseParams:
    """Parameters for pause."""
    info: str | None = None
    err: bool | None = None

@dataclass
class ProgressBarMakeStepParams:
    """Parameters for progress_bar_make_step."""
    n_steps: int

@dataclass
class ProgressbarParams:
    """Parameters for progressbar."""
    length: int
    label: str | None = None
    hidden: bool | None = None
    show_eta: bool | None = None
    show_percent: bool | None = None
    show_pos: bool | None = None
    fill_char: str | None = None
    empty_char: str | None = None
    bar_template: str | None = None
    info_sep: str | None = None
    width: int | None = None
    file: str | None = None
    color: bool | None = None
    update_min_steps: int | None = None

@dataclass
class PushContextParams:
    """Parameters for push_context."""
    ctx: str

@dataclass
class ResolveColorDefaultParams:
    """Parameters for resolve_color_default."""
    color: bool | None = None

@dataclass
class SafecallParams:
    """Parameters for safecall."""
    func: str

@dataclass
class SechoParams:
    """Parameters for secho."""
    message: str | None = None
    file: str | None = None
    nl: bool | None = None
    err: bool | None = None
    color: bool | None = None

@dataclass
class ShellCompleteParams:
    """Parameters for shell_complete."""
    cli: str
    ctx_args: str
    prog_name: str
    complete_var: str
    instruction: str

@dataclass
class ShellCompleteFormatCompletionParams:
    """Parameters for shell_complete_format_completion."""
    item: str

