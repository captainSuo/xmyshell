from time import time_ns

_start_time = time_ns()


import os
from .meta import WELCOME_MESSAGE
from .environment import localspace


def xmyshell_main() -> None:
    # Startup is import-bound, and prompt_toolkit is by far the most expensive
    # import we have. Everything below is imported as late as possible so that
    # initialization (and the welcome message) can happen first.
    from .init import xmyshell_init, xmyshell_init_completer

    xmyshell_init()

    if localspace.get("SHOW_WELCOME"):
        print(WELCOME_MESSAGE)

    xmyshell_init_completer()

    from prompt_toolkit import HTML, PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    from .injection import inject
    from .kernel import pyeval, xmyshell
    from .keybindings import (
        bindings,
        clean_buffer,
        on_cursor_position_changed,
        on_text_changed,
    )

    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.xmyshell/history.txt")),
        auto_suggest=AutoSuggestFromHistory(),
        complete_in_thread=True,
        complete_while_typing=True,
        key_bindings=bindings,
        multiline=True,
        prompt_continuation="",
    )
    session.default_buffer.on_cursor_position_changed += on_cursor_position_changed
    session.default_buffer.on_text_changed += on_text_changed

    if localspace.get("SHOW_WELCOME"):
        print(f"Initialized with {(time_ns() - _start_time) // 1_000_000}ms.")

    try:
        while True:
            try:
                cmd_line: str = session.prompt(
                    HTML(pyeval(localspace["shell_prompt"])),
                    rprompt=HTML(pyeval(localspace["shell_rprompt"])),
                    completer=localspace["shell_completer"],
                    placeholder=HTML(localspace["prompt_placeholder"]),
                    style=Style.from_dict(localspace["prompt_style"]),
                    pre_run=inject,
                )
                start_time = time_ns()
                localspace["exit_code"] = xmyshell(cmd_line)
                localspace["exec_duration"] = time_ns() - start_time
                clean_buffer()
            except KeyboardInterrupt:
                print("Ctrl-C")
            except EOFError:
                print("EOF")
                break
    finally:
        print("exit")


if __name__ == "__main__":
    xmyshell_main()
