from collections.abc import Generator
import os
import shlex
import sys
import re
import time
import keyword
from string import whitespace
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from .environment import localspace, aliases
from .utils import truncate

MAX_DISPLAY_LEN = 24
MAX_META_LEN = 12

WIN_EXEC_EXTS = frozenset({".exe", ".bat", ".cmd", ".ps1", ".py", ".com"})
NON_EXEC_SUFFIXES = (".dll", ".pyd", ".pyc", ".sys", ".msi", ".drv")
POSIX_NON_EXEC_SUFFIXES = (".so", ".a", ".o")

BUILTINS = ("cd", "cp", "cat", "echo", "exit", "import", "ls", "print", "pyexec", "pwd", "source",
            "clear", "grep", "find", "from", "mkdir", "rm", "reload", "mv", "help",
            "update", "alias", "unalias")

COMMON = (
    "python", "python3", "pip", "pip3", "git", "conda", "uv",
    "ssh", "scp", "curl", "wget", "winget", "docker",
    "vim", "nvim", "nano", "code",
    "sudo", "apt", "yum", "brew", "chmod", "chown",
    "ps", "top", "htop", "kill", "pkill", "killall",
    "systemctl", "journalctl", "service", "watch", "screen", "tmux", "nohup",
    "ping", "dig", "nslookup", "traceroute", "nc", "route", "arp", "iptables", "ufw",
    "ip", "ifconfig", "netstat", "ss",
    "tar", "gzip", "gunzip", "bzip2", "xz", "zip", "unzip",
    "node", "npm", "npx", "yarn", "pnpm",
    "java", "javac", "mvn", "gradle", "ant",
    "gcc", "g++", "make", "cmake",
    "go", "rustc", "cargo", "gdb",
    "sqlite3", "mysql", "psql", "mongosh", "redis-cli",
    "free", "ffmpeg", "df", "du", "iostat", "vmstat",
    "awk", "sed", "xargs"
)

KEYWORDS = list(keyword.kwlist)

COMMAND_TREE: dict | None = None
COMMAND_TREE_PATH = os.path.join(os.path.dirname(__file__), "data", "commands.json")


def _command_tree() -> dict:
    global COMMAND_TREE
    if COMMAND_TREE is None:
        COMMAND_TREE = {}
        try:
            import json
            with open(COMMAND_TREE_PATH, "r", encoding="utf-8") as f:
                COMMAND_TREE = json.load(f)
        except (OSError, ValueError):
            pass
    return COMMAND_TREE or {}


def _module_names() -> set[str]:
    """Module names offered after `import` / `from` (pkgutil is not cheap)."""
    import pkgutil
    return set(sys.builtin_module_names) | {m.name for m in pkgutil.iter_modules()}


class ShellCompleter(Completer):

    def __init__(self, cache_duration: int = 30) -> None:
        self._cache: list[str] = []
        self._cache_time: float = 0.0
        self._cache_duration = cache_duration
        self._loaded = False
        # The PATH scan is deferred to the first completion request: it costs
        # tens of milliseconds and nothing needs it to show the prompt.

    def _strip_ext(self, name: str) -> str:
        if os.name == "nt":
            stem, ext = os.path.splitext(name)
            if ext in WIN_EXEC_EXTS:
                return stem
        return name

    def _get_commands(self) -> list[str]:
        now = time.monotonic()
        if self._loaded and now - self._cache_time < self._cache_duration:
            return self._cache

        commands: set[str] = set(BUILTINS)
        for path in os.environ.get("PATH", "").split(os.pathsep):
            if not path or path.startswith("/mnt/"):
                continue
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        name = entry.name.lower() if os.name == "nt" else entry.name
                        if not self._is_executable(name):
                            continue
                        try:
                            if not entry.is_file():
                                continue
                        except OSError:
                            continue
                        if os.name != "nt" and not os.access(entry.path, os.X_OK):
                            continue
                        commands.add(self._strip_ext(name))
            except OSError:
                continue

        self._cache = self._sort_commands(commands)
        self._cache_time = now
        self._loaded = True
        return self._cache

    def _is_executable(self, name: str) -> bool:
        """Name-only filter, applied before any filesystem access."""
        if name.endswith(NON_EXEC_SUFFIXES):
            return False
        if os.name == "nt":
            return os.path.splitext(name)[1] in WIN_EXEC_EXTS
        return not name.endswith(POSIX_NON_EXEC_SUFFIXES)

    def _inside_braces(self, text: str) -> bool:
        count = 0
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == '{' and (i == 0 or text[i-1] != '{'):
                count += 1
                i += 1
            elif ch == '}' and (i == 0 or text[i-1] != '}'):
                count -= 1
                i += 1
            else:
                i += 1
        return count > 0

    def _sort_commands(self, commands: set[str]) -> list[str]:
        builtins = [c for c in BUILTINS if c in commands]
        common = [c for c in COMMON if c in commands]
        others = sorted(c for c in commands if c not in COMMON and c not in BUILTINS)
        return builtins + common + others

    def _path_completions(self, text: str, max_results: int = 100, in_string: bool=False):
        if text and text[-1] in whitespace: return

        def last_token_raw(text: str) -> tuple[str, bool]:
            quote = None
            start = 0
            i = 0
            while i < len(text):
                ch = text[i]
                if quote:
                    if ch == quote:
                        quote = None
                    elif ch == "\\" and quote == '"':
                        i += 1
                else:
                    if ch in ("'", '"'):
                        quote = ch
                    elif ch in " \t":
                        start = i + 1
                    elif ch == "\\":
                        i += 1
                i += 1
            return text[start:], quote is not None

        def split_lenient(s: str) -> list[str] | None:
            try:
                return shlex.split(s)
            except ValueError:
                pass
            quote = None
            i = 0
            while i < len(s):
                ch = s[i]
                if quote:
                    if ch == quote: quote = None
                    elif ch == '\\' and quote == '"': i += 1
                else:
                    if ch in ('"', "'"): quote = ch
                    elif ch == '\\': i += 1
                i += 1
            if quote:
                try:
                    return shlex.split(s + quote)
                except ValueError:
                    pass
            return None

        last, still_in = last_token_raw(text)
        in_string = in_string or still_in
        if last == '~': return  # don't remove this
        parts = split_lenient(last)
        if parts:
            path = os.path.expanduser(parts[0])
        else:
            path = os.path.expanduser(last)
        dirname = os.path.dirname(path) or "."
        prefix = os.path.basename(path).strip('"\'')

        try:
            entries = sorted(os.listdir(dirname))
        except OSError:
            return

        exact = [e for e in entries if e.startswith(prefix)]
        fuzzy = [e for e in entries if not e.startswith(prefix) and prefix in e]

        budget = max_results - len(exact[:max_results])
        selected = exact[:max_results] + fuzzy[:max(0, budget)]

        for item in selected:
            full = os.path.join(dirname, item)
            is_dir = os.path.isdir(full)
            if ' ' in item and not in_string:
                name = f'"{item}"'
            else:
                name = item
            yield Completion(
                name,
                display=truncate(item, MAX_DISPLAY_LEN),
                start_position=-len(prefix),
                display_meta="directory" if is_dir else "file",
            )

    @staticmethod
    def _last_identifier(text: str) -> str:
        i = len(text) - 1
        while i >= 0 and (text[i].isalnum() or text[i] == '_'):
            i -= 1
        start = i + 1
        identifier = text[start:]
        return identifier

    def _environment_completion(self, text: str):
        last_word = self._last_identifier(text)
        if not last_word:
            return

        candidates = set(os.environ)
        for name in sorted(candidates):
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="environment"
                )

    def _python_completion(self, text: str):

        def _in_string(text: str) -> str | None:
            i, n = 0, len(text)
            quote = ''
            content_start = 0

            while i < n:
                c = text[i]
                if not quote:
                    if c in ('"', "'"):
                        if text[i:i+3] in ('"""', "'''"):
                            quote = text[i:i+3]
                            i += 3
                        else:
                            quote = c
                            i += 1
                        content_start = i
                        continue
                    i += 1
                else:
                    if c == '\\':
                        i += 2
                        continue
                    if text.startswith(quote, i):
                        i += len(quote)
                        quote = ''
                        continue
                    i += 1

            if not quote:
                return None
            return text[content_start:]

        string = _in_string(text)
        if string:
            yield from self._path_completions(string, in_string=True)
            return

        if text and text[-1].isspace():
            return
        last_token = text.split()[-1] if text.split() else ''
        if not last_token:
            return

        if '.' in last_token:
            last_dot = last_token.rfind('.')
            after_dot = last_token[last_dot+1:]
            if after_dot == "" or after_dot.isidentifier():
                parts = last_token.split('.')

                # find the start point of identifiers chain
                start = 0
                for idx in range(len(parts)-2, -1, -1):
                    if not parts[idx].isidentifier():
                        start = idx
                        break

                obj = None
                root = self._last_identifier(parts[start])
                if root in localspace:
                    obj = localspace[root]
                elif hasattr(__builtins__, root):
                    obj = getattr(__builtins__, root)
                elif isinstance(__builtins__, dict) and root in __builtins__:
                    obj = __builtins__[root]

                if obj is None:
                    return

                for part in parts[start+1:-1]:
                    try:
                        obj = getattr(obj, part)
                    except AttributeError:
                        return

                prefix = parts[-1]
                attrs = dir(obj)
                attrs.sort(key=lambda x: (x.startswith('_'), x))
                for attr in attrs:
                    if attr.startswith(prefix):
                        try:
                            value = getattr(obj, attr)
                            meta = (
                                "method"
                                if callable(value)
                                else truncate(type(value).__name__, MAX_META_LEN)
                            )
                        except Exception:
                            meta = "attr"
                        yield Completion(
                            attr,
                            start_position=-len(prefix),
                            display=attr,
                            display_meta=meta,
                        )
                return

        last_word = self._last_identifier(last_token)
        if not last_word:
            return

        builtins_candidates = []
        if isinstance(__builtins__, dict):
            builtins_candidates = list(__builtins__.keys())
        elif hasattr(__builtins__, '__dict__'):
            builtins_candidates = dir(__builtins__)
        else:
            builtins_candidates = []

        candidates = set(localspace.keys()) | set(builtins_candidates)
        for name in sorted(candidates) + KEYWORDS:
            if name in localspace:
                meta = truncate(type(localspace[name]).__name__, MAX_META_LEN)
            elif name in __builtins__:
                meta = truncate(type(__builtins__[name]).__name__, MAX_META_LEN)
            else:
                meta = "python"
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=name,
                    display_meta=meta
                )
        yield from self._environment_completion(text)

    def _subcommand_completion(self, text: str):
        try:
            parts = shlex.split(text)
        except ValueError:
            parts = text.split()
        if not parts: return
        sub_cmd = _command_tree().get(parts[0])
        if not sub_cmd: return
        global_flags: set[str] = set()
        if sub_cmd.get("_global"):
            global_flags.update(sub_cmd["_global"])
        if not text.endswith(parts[-1]):
            parts.append("")
        last_word = parts[-1]

        for part in parts[1:-1]:
            if sub_cmd.get("_global"):
                global_flags.update(sub_cmd["_global"])
            if sub_cmd.get(part):
                sub_cmd = sub_cmd[part]

        for name in sorted(sub_cmd.keys()):
            if name == "_global" or name == "_flags": continue
            if name in parts[:-1]: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="subcommand"
                )

        # not auto complete flags unless user types them
        if last_word == "": return

        for name in sorted(sub_cmd.get("_flags") or set()):
            if name in parts[:-1]: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="flag",
                )

        for name in sorted(global_flags):
            if name in parts[:-1]: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="flag",
                )

    def _command_completion(self, text):
        for cmd in self._get_commands():
            if cmd in aliases: continue
            if cmd.startswith(text):
                meta = "command" if cmd in BUILTINS else "program"
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=truncate(cmd, MAX_DISPLAY_LEN),
                    display_meta=meta,
                )

    def _alias_completion(self, text):
        for alias in aliases.keys():
            if alias.startswith(text):
                yield Completion(
                    alias,
                    start_position=-len(text),
                    display=truncate(alias, MAX_DISPLAY_LEN),
                    display_meta="alias",
                )

    def _get_completions(self, document: Document, complete_event) -> Generator[Completion, None, None]:
        text = document.text_before_cursor
        if "=>" in text: return
        segments = re.split(r'\|>|\|', text)
        current_segment = segments[-1] if segments else text
        lstripped = current_segment.lstrip()
        if lstripped.startswith("sudo"):
            lstripped = lstripped[4:].lstrip()

        if self._inside_braces(lstripped):
            yield from self._python_completion(lstripped)
            return

        if " " not in lstripped:
            if len(lstripped) < 1:
                return
            yield from self._alias_completion(lstripped)
            yield from self._command_completion(lstripped)

        # special built-ins
        parts = lstripped.split()
        if len(parts) >= 1:
            cmd = parts[0]
            if cmd in ("print", "pyexec", "alias"):
                param_text = lstripped[len(cmd):].lstrip()
                yield from self._python_completion(param_text)
                return
            if cmd == "unalias":
                param_text = lstripped[len(cmd):].lstrip()
                yield from self._alias_completion(param_text)
            if cmd == "from":
                if not lstripped.endswith(parts[-1]):
                    parts.append("")
                elif len(parts) == 2:
                    mods = _module_names()
                    for name in sorted(mods):
                        if not name.startswith(parts[-1]):
                            continue
                        if name.startswith("_"):
                            continue
                        yield Completion(
                            name,
                            start_position=-len(parts[-1]),
                            display=truncate(name, MAX_DISPLAY_LEN),
                            display_meta="module",
                        )
                elif len(parts) == 3:
                    yield Completion(
                        "import",
                        start_position=-len(parts[-1]),
                        display_meta="keyword",
                    )
                return
            if cmd == "import":
                if not lstripped.endswith(parts[-1]):
                    parts.append("")
                elif len(parts) == 2:
                    mods = _module_names()
                    for name in sorted(mods):
                        if not name.startswith(parts[-1]):
                            continue
                        if name.startswith("_"):
                            continue
                        yield Completion(
                            name,
                            start_position=-len(parts[-1]),
                            display=truncate(name, MAX_DISPLAY_LEN),
                            display_meta="module",
                        )
                elif len(parts) == 3:
                    yield Completion(
                        "as",
                        start_position=-len(parts[-1]),
                        display_meta="keyword",
                    )
                return

        yield from self._subcommand_completion(lstripped)
        yield from self._path_completions(lstripped)

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> list[Completion]:
        completions: list[Completion] = list(self._get_completions(document, complete_event))
        if len(completions) == 1:
            # Trailing space bypasses prompt_toolkit's `completion_does_nothing`
            # filter (which hides completions identical to the replaced text) and
            # doubles as the shell argument separator. Invisible characters would
            # also bypass the filter, but would corrupt command parsing.
            completion = completions[0]
            text_before_cursor = document.text_before_cursor
            replaced_text = text_before_cursor[
                len(text_before_cursor) + completion.start_position :
            ]
            if replaced_text == completion.text:
                completion.text = completion.text + " "
        return completions

def completer_init() -> None:
    localspace["shell_completer"] = ShellCompleter()
