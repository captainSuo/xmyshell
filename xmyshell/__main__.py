import sys

def main() -> None:
    if "--version" in sys.argv:
        from .meta import WELCOME_MESSAGE
        print(WELCOME_MESSAGE)
    elif "--help" in sys.argv:
        from .meta import HELP_MESSAGE
        print(HELP_MESSAGE)
    else:
        from .main import xmyshell_main
        xmyshell_main()
