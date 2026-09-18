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
  help                          Show help documents.
  print <expr>                  Evaluate and print a Python expression.
  pyexec <stmt>                 Execute a Python statement (e.g. pyexec x = 1).
  source <file.py>              Run a Python script in the current namespace.
  export <NAME>=<value>         Set an environment variable (supports {{expr}}).
  import <module> [as <alt>]    Import a Python module.
  from <module> import <names>  Import names from a module.
  reload                        Reload environment (e.g. exit virtualenv).
  update [<version>]            Update xmyshell (optionally to a specific version).
  cd <dir>                      Change directory (supports {{expr}}).
  pwd                           Print working directory.
  clear                         Clear the terminal screen.
  alias altname=<cmd>           Create an alias command.
  unalias altname               Remove an alias command.
  exit                          Exit XmyShell.

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
  getlogin()          -  current username
  getcwd()            -  current working directory
  dirname(p)          -  parent directory of path
  basename(p)         -  final component of path
  cat(file)           -  Shortcut for open(file).read().
  alias(altname, cmd) -  Same as the command.
  unalias(altname) -  Same as the command.

Built-in variables:
  exit_code       -  The exit code of the last command.
  exec_duration   -  The duration which last command took.
  HOME_DIR        -  The home directory, similar to "~".
  PROFILE         -  The path of config file.

Keyboard Shortcuts:
  ↑↓      -  Navigate through command history.
  →       -  Apply selected history entry to the prompt.
  Ctrl+R  -  Reverse incremental searching (history).
  Ctrl+D  -  Exit XmyShell."""
