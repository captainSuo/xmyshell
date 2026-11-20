from .meta import NAME, VERSION, AUTHOR, EMAIL

__title__ = NAME
__version__ = VERSION
__author__ = AUTHOR
__author_email__ = EMAIL

__all__ = ["xmyshell_main"]

xmyshell_main = ...

def __getattr__(name: str):
    # Importing the shell runtime pulls in prompt_toolkit (~350ms), so keep it
    # lazy: `import xmyshell`, `from xmyshell.themes import ...` and the
    # `--version` / `--help` paths must not pay for it.
    if name == "xmyshell_main":
        from .main import xmyshell_main
        return xmyshell_main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
