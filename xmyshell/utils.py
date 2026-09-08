import os
import sys

XMYSHELL_MAGIC = object()


def truncate(s: str, n: int) -> str:
    return s[:n] + "..." if len(s) > n else s


def pyerror(msg: str) -> None:
    sys.stderr.write(f"Error: {msg}\n")


def pywarning(msg: str) -> None:
    sys.stderr.write(f"Warning: {msg}\n")


def getlogin() -> str:
    try:
        return os.getlogin()
    except OSError:
        try:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name  # pyright: ignore
        except Exception:
            return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))

def getcwd() -> str:
    if os.name == "nt":
        return os.getcwd().replace('\\', '/')
    else:
        return os.getcwd()

HOME_DIR = os.path.expanduser("~").replace('\\', '/')
