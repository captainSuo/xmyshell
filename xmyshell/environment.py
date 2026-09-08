import os
import sys
import socket
import time
from datetime import datetime
from typing import Any
from collections.abc import Mapping
from .utils import XMYSHELL_MAGIC, getcwd, getlogin, HOME_DIR

namespace: dict[str, Any] = {}
init_environ: dict[str, str] = dict(os.environ)


_init_namespace: dict[str, Any] = {
    "_xmyshell_magic": XMYSHELL_MAGIC,
    "__builtins__": __builtins__,
    "os": os,
    "sys": sys,
    "time": time,
    "datetime": datetime,
    "socket": socket,
    "getlogin": getlogin,
    "getcwd": getcwd,
    "dirname": os.path.dirname,
    "basename": os.path.basename,
    "HOME_DIR": HOME_DIR,
    "exit_code": 0,
    "exec_duration": 0,
    "last_error": None,
    "last_traceback": None,
    "shell_prompt": "",
    "shell_rprompt": "",
    "prompt_placeholder": "",
    "prompt_style": {},
}


def load_init_namespace() -> None:
    namespace.clear()
    namespace.update(_init_namespace)


def update_namespace(values: Mapping[str, object]) -> None:
    import sys
    depth = 0
    while True:  # looking for special namespace recursively
        try:
            frame = sys._getframe(depth)
        except ValueError:
            break
        if "_xmyshell_magic" in frame.f_globals:  # source
            frame.f_globals.update(values)
            return
        if "_xmyshell_magic" in frame.f_locals:  # pyexec
            frame.f_locals.update(values)
            return
        depth += 1
    namespace.update(values)  # kernal

