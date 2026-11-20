import os
import sys

# ANSI color codes
RESET   = "\033[0m"
BOLD    = "\033[1m"
NOBOLD  = "\033[22m"
CYAN    = "\033[36m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"

NAME            = "xmyshell"
DISPLAY_NAME    = "XmyShell"
AUTHOR          = "CaptainSuo"
EMAIL           = "captainsuo@outlook.com"


def _version_from_metadata() -> str | None:
    """Read VERSION straight from the installed metadata file.

    `importlib.metadata` costs 60-90ms on import because it drags in
    `email`, `zipfile` and friends, and this module is imported on every
    startup just to print the banner. Reading one small file is enough;
    anything unusual (no metadata, several of them) falls back.
    """
    roots = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    roots += [entry for entry in sys.path if entry]

    candidates: list[str] = []
    seen: set[str] = set()
    for root in roots:
        root = os.path.abspath(root)
        if root in seen:
            continue
        seen.add(root)
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in names:
            if name.startswith(f"{NAME}-") and name.endswith(".dist-info"):
                candidates.append(os.path.join(root, name, "METADATA"))
            elif name == f"{NAME}.egg-info":
                candidates.append(os.path.join(root, name, "PKG-INFO"))
        if len(candidates) > 1:
            return None

    if len(candidates) != 1:
        return None

    try:
        with open(candidates[0], "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("Version:"):
                    return line[len("Version:"):].strip() or None
                if not line.strip():  # end of the header block
                    return None
    except OSError:
        pass
    return None


def _installed_version() -> str:
    version = _version_from_metadata()
    if version is not None:
        return version
    from importlib.metadata import version as metadata_version
    return metadata_version(NAME)


VERSION         = _installed_version()
WELCOME_MESSAGE = f"""{BOLD}{BLUE}{DISPLAY_NAME} {CYAN}{VERSION}{RESET}"""

HELP_MESSAGE = f"""{BOLD}{CYAN}
 ███╗  ███╗ ███╗   ███╗ ██╗   ██╗ ███████╗ ██╗   ██╗ ███████╗ ██╗      ██╗
 ╚═██╗██╔═╝ ████╗ ████║ ╚██╗ ██╔╝ ██╔════╝ ██║   ██║ ██╔════╝ ██║      ██║
   ╚███╔╝   ██╔████╔██║  ╚████╔╝  ███████╗ ████████║ ██████╗  ██║      ██║
   ██╔██╗   ██║╚██╔╝██║   ╚██╔╝   ╚════██║ ██╔═══██║ ██╔═══╝  ██║      ██║
 ███╔╝ ███╗ ██║ ╚═╝ ██║    ██║    ███████║ ██║   ██║ ███████╗ ███████╗ ███████╗
 ╚══╝  ╚══╝ ╚═╝     ╚═╝    ╚═╝    ╚══════╝ ╚═╝   ╚═╝ ╚══════╝ ╚══════╝ ╚══════╝
{RESET}
{WELCOME_MESSAGE}

{BOLD}{YELLOW}Built-in Commands{BOLD}{CYAN}
  {BOLD}{GREEN}help{CYAN}                          {NOBOLD}Show help documents.
  {BOLD}{GREEN}print{CYAN} <expr>                  {NOBOLD}Evaluate and print a Python expression.
  {BOLD}{GREEN}pyexec{CYAN} <stmt>                 {NOBOLD}Execute a Python statement.
  {BOLD}{GREEN}source{CYAN} <file.py>              {NOBOLD}Run a Python script in the current namespace.
  {BOLD}{GREEN}export{CYAN} <NAME>=<value>         {NOBOLD}Set an environment variable (supports {{expr}}).
  {BOLD}{GREEN}import{CYAN} <module> [as <alt>]    {NOBOLD}Import a Python module.
  {BOLD}{GREEN}from{CYAN} <module> import <names>  {NOBOLD}Import names from a module.
  {BOLD}{GREEN}reload{CYAN}                        {NOBOLD}Reload environment.
  {BOLD}{GREEN}update{CYAN} [<version>]            {NOBOLD}Update xmyshell.
  {BOLD}{GREEN}cd{CYAN} <dir>                      {NOBOLD}Change directory (supports {{expr}}).
  {BOLD}{GREEN}pwd{CYAN}                           {NOBOLD}Print working directory.
  {BOLD}{GREEN}clear{CYAN}                         {NOBOLD}Clear the terminal screen.
  {BOLD}{GREEN}alias{CYAN} altname=<cmd>           {NOBOLD}Create an alias command.
  {BOLD}{GREEN}unalias{CYAN} altname               {NOBOLD}Remove an alias command.
  {BOLD}{GREEN}exit{CYAN}                          {NOBOLD}Exit XmyShell.

{BOLD}{YELLOW}Inline Python{NOBOLD}{CYAN}
  Use {{expression}} anywhere in a command to expand its result.
  {BOLD}{MAGENTA}Example{NOBOLD}{CYAN} mkdir {{" ".join(f"test{{i}}" for i in range(3))}}
  Escape braces as {{{{ and }}}}.

{BOLD}{YELLOW}IO{NOBOLD}{CYAN}
  Append => variable to a command to capture its output while still
  displaying it.
  {BOLD}{MAGENTA}Example{NOBOLD}{CYAN} which python => path
  Redirect the output of Python commands (print, pyexec) with |>
  {BOLD}{MAGENTA}Example{NOBOLD}{CYAN} print "\\n".join(str(i) for i in range(100)) |> grep 42

{BOLD}{YELLOW}Helper Functions{NOBOLD}{CYAN}
  {BLUE}getlogin{CYAN}()           current username
  {BLUE}getcwd{CYAN}()             current working directory
  {BLUE}dirname{CYAN}(p)           parent directory of path
  {BLUE}basename{CYAN}(p)          final component of path
  {BLUE}cat{CYAN}(file)            Shortcut for open(file).read().
  {BLUE}alias{CYAN}(altname, cmd)  Same as the command.
  {BLUE}unalias{CYAN}(altname)     Same as the command.

{BOLD}{YELLOW}Built-in variables{NOBOLD}{CYAN}
  {BLUE}exit_code{CYAN}            The exit code of the last command.
  {BLUE}exec_duration{CYAN}        The duration which last command took.
  {BLUE}last_error{CYAN}           The error raised from last Python operation (if exists).
  {BLUE}last_traceback{CYAN}       The traceback of last Python operation (if exists).
  {BLUE}ans{CYAN}                  The result from last print command.
  {BLUE}HOME_DIR{CYAN}             The home directory, similar to "~".
  {BLUE}PROFILE{CYAN}              The path of config file.
  {BLUE}SHOW_WELCOME{CYAN}         Toggle whether to show welcome message.
  {BLUE}SHELL_CMD{CYAN}            Shell command line prefix, e.g. ["cmd", "/c"]

{BOLD}{YELLOW}Keyboard Shortcuts{NOBOLD}{CYAN}
  {MAGENTA}↑↓                   {CYAN}Navigate through command history.
  {MAGENTA}→                    {CYAN}Apply selected history entry to the prompt.
  {MAGENTA}Ctrl+R               {CYAN}Reverse incremental searching (history).
  {MAGENTA}Ctrl+Z               {CYAN}Undo.
  {MAGENTA}Ctrl+Y               {CYAN}Redo.
  {MAGENTA}Ctrl+G               {CYAN}Hide completions.
  {MAGENTA}Ctrl+D               {CYAN}Exit XmyShell.{RESET}"""
