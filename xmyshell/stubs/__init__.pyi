# XmyShell built-in names

from typing import Any


def getlogin() -> str: ...
def getcwd() -> str: ...
def dirname(p: str) -> str: ...
def basename(p: str) -> str: ...
def cat(file_path: str) -> str: ...
def alias(altname: str, target: str) -> None: ...
def unalias(altname: str) -> None: ...
SHOW_WELCOME: bool
SHELL_CMD: list[str]
HOME_DIR: str
PROFILE: str
exit_code: int
exec_duration: int
last_error: Exception | None
last_traceback: str | None
ans: Any
shell_prompt: str
shell_rprompt: str
prompt_placeholder: str
prompt_style: dict[str, str]
