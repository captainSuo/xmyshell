import os
import sys
from .environment import load_init_namespace, init_environ
from .themes import load_theme, THEME_DEFAULT
from .completer import completer_init
from .utils import pywarning
from .kernel import xmyshell_source


def xmyshell_load() -> None:
    if "" not in sys.path:
        sys.path.insert(0, "")

    load_init_namespace()
    completer_init()
    load_theme(THEME_DEFAULT)

    try:
        xmyshell_source("~/.xmyshell/config.py")
    except FileNotFoundError:
        pass
    except Exception as e:
        pywarning(
            f"An error occured when loading config from ~/.xmyshell/config.py"
            f"\n{type(e).__name__}: {e}"
        )


def xmyshell_init() -> None:
    os.makedirs(os.path.expanduser("~/.xmyshell/"), exist_ok=True)
    xmyshell_load()


def xmyshell_reload() -> None:
    os.environ.clear()
    os.environ.update(init_environ)
    xmyshell_load()
