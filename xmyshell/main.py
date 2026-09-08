from time import time_ns
_start_time = time_ns()

import os
from prompt_toolkit import HTML, PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from .meta import WELCOME_MESSAGE
from .environment import namespace
from .keybindings import bindings, on_cursor_position_changed
from .init import xmyshell_init
from .kernel import pyeval, xmyshell
from .lexer import XmyShellLexer


def xmyshell_main() -> None:
    xmyshell_init()

    print(WELCOME_MESSAGE)
    print(f"Initialized with {(time_ns() - _start_time) // 1_000_000}ms.")

    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.xmyshell/history.txt")),
        auto_suggest=AutoSuggestFromHistory(),
        complete_in_thread=True,
        complete_while_typing=True,
        key_bindings=bindings,
        lexer=XmyShellLexer(),
    )
    session.default_buffer.on_cursor_position_changed += on_cursor_position_changed

    try:
        while True:
            try:
                cmd_line: str = session.prompt(
                    HTML(pyeval(namespace["shell_prompt"])),
                    rprompt=HTML(pyeval(namespace["shell_rprompt"])),
                    completer=namespace["shell_completer"],
                    placeholder=HTML(namespace["prompt_placeholder"]),
                    style=Style.from_dict(namespace["prompt_style"]),
                )
                start_time = time_ns()
                namespace["exit_code"] = xmyshell(cmd_line)
                namespace["exec_duration"] = time_ns() - start_time
            except KeyboardInterrupt:
                print("Ctrl-C")
            except EOFError:
                print("EOF")
                break
    finally:
        print("exit")


if __name__ == "__main__":
    xmyshell_main()
