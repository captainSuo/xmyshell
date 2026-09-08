from importlib.metadata import version

NAME            = "xmyshell"
DISPLAY_NAME    = "XmyShell"
VERSION         = version(NAME)
AUTHOR          = "CaptainSuo"
EMAIL           = "captainsuo@outlook.com"
WELCOME_MESSAGE = f"""{DISPLAY_NAME} {VERSION}"""
HELP_MESSAGE    = f"""\033[1;36m
 ███╗  ███╗ ███╗   ███╗ ██╗   ██╗ ███████╗ ██╗   ██╗ ███████╗ ██╗      ██╗
 ╚═██╗██╔═╝ ████╗ ████║ ╚██╗ ██╔╝ ██╔════╝ ██║   ██║ ██╔════╝ ██║      ██║
   ╚███╔╝   ██╔████╔██║  ╚████╔╝  ███████╗ ████████║ ██████╗  ██║      ██║
   ██╔██╗   ██║╚██╔╝██║   ╚██╔╝   ╚════██║ ██╔═══██║ ██╔═══╝  ██║      ██║
 ███╔╝ ███╗ ██║ ╚═╝ ██║    ██║    ███████║ ██║   ██║ ███████╗ ███████╗ ███████╗
 ╚══╝  ╚══╝ ╚═╝     ╚═╝    ╚═╝    ╚══════╝ ╚═╝   ╚═╝ ╚══════╝ ╚══════╝ ╚══════╝
\033[0m
{WELCOME_MESSAGE}

Built-in Commands:
  help                        Show helping documents.
  print <expr>                Evaluate and print a Python expression.
  pyexec <stmt>               Execute a Python statement (e.g. pyexec x = 1).
  source <file.py>            Run a Python script in the current namespace.
  export NAME=VALUE           Set an environment variable (supports {{expr}}).
  import <module> [as <alt>]  Import a Python module.
  from <module> import *      Import names from a module.
  reload                      Reload environment (e.g. exit virtualenv).
  cd <dir>                    Change directory (supports {{expr}}).
  pwd                         Print working directory.
  clear                       Clear the terminal screen.
  exit                        Exit XmyShell.

Inline Python:
  Use {{expression}} anywhere in a command to expand its result.
  Example: mkdir {{" ".join(f"test{{i}}" for i in range(3))}}
  Escape braces as {{{{ and }}}}.

IO:
  Append => variable to a command to capture its output while still
  displaying it.
  Example: which python => path
  Redirect the output of Python commands (print, pyexec) with |>
  Example: print "\\n".join(str(i) for i in range(100)) |> grep 42

Helper Functions:
  getlogin()   -  current username
  getcwd()     -  current working directory
  dirname(p)   -  parent directory of path
  basename(p)  -  final component of path

Keyboard Shortcuts:
  ↑↓      -  Navigate through command history.
  →       -  Apply selected history entry to the prompt.
  Ctrl+R  -  Reverse incremental searching (history).
  Ctrl+D  -  Exit XmyShell."""
