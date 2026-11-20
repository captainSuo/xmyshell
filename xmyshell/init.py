import os
import sys
from .environment import load_init_namespace, init_environ, aliases
from .themes import load_theme, THEME_DEFAULT
from .utils import pywarning
from .kernel import xmyshell_source


def _load_core() -> None:
    """Namespace, theme and user config. No prompt_toolkit, no PATH scan."""
    if "" not in sys.path:
        sys.path.insert(0, "")

    load_init_namespace()
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
    _load_core()


def xmyshell_init_completer() -> None:
    """Load the completer, i.e. the first part of the stack needing prompt_toolkit.

    Kept separate from `xmyshell_init()` so the caller can show the welcome
    message before paying for prompt_toolkit imports.
    """
    from .completer import completer_init
    completer_init()


def xmyshell_reload() -> None:
    os.environ.clear()
    os.environ.update(init_environ)
    aliases.clear()
    _load_core()
    xmyshell_init_completer()
