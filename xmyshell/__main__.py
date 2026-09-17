import subprocess
import sys


def main() -> None:
    argv = sys.argv

    if len(argv) == 1:
        from .main import xmyshell_main
        xmyshell_main()
    elif argv[1] == "--update":
        subprocess.run([sys.executable, "-m", "xmyshell.update"] + argv[2:])
    elif argv[1] == "--version":
        from .meta import WELCOME_MESSAGE
        print(WELCOME_MESSAGE)
    elif argv[1] == "--help":
        from .meta import HELP_MESSAGE
        print(HELP_MESSAGE)
    else:
        print(f"Error: cannot parse arguments '{' '.join(argv[1:])}'")
