from collections.abc import Callable, Generator, Iterable
import os
import shlex
import sys
import re
import time
import keyword
from string import whitespace
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from .environment import localspace, aliases
from .utils import truncate

MAX_DISPLAY_LEN = 24
MAX_META_LEN = 12


def _display(name: str, matched: str, limit: int = MAX_DISPLAY_LEN) -> StyleAndTextTuples:
    """Display `name` truncated to `limit`, with the matched part highlighted.

    `matched` is the text that produced the completion. It normally sits at the
    start of `name`, but fuzzy path matches can occur anywhere, so the visible
    window slides to keep the match on screen (a leading ``...`` marks the
    omitted prefix).
    """
    if not matched:
        return [("", truncate(name, limit))]

    start = name.lower().find(matched.lower())
    if start < 0:
        return [("", truncate(name, limit))]
    end = start + len(matched)

    # The window is normally the first `limit` characters. If the match falls
    # past it, shift the window so the whole match stays visible.
    span = max(limit, len(matched))
    visible_start = 0 if end <= limit else end - span
    visible_end = min(len(name), visible_start + span)
    visible = name[visible_start:visible_end]

    rel_start = start - visible_start
    rel_end = rel_start + len(matched)

    HIGHLIGHT_STYLE = "class:completion-highlight"
    PLAIN_STYLE = ""

    fragments: StyleAndTextTuples = []
    if visible_start:
        fragments.append((PLAIN_STYLE, "..."))
    if rel_start:
        fragments.append((PLAIN_STYLE, visible[:rel_start]))
    fragments.append((HIGHLIGHT_STYLE, visible[rel_start:rel_end]))
    if rel_end < len(visible):
        fragments.append((PLAIN_STYLE, visible[rel_end:]))
    if visible_end < len(name):
        fragments.append((PLAIN_STYLE, "..."))
    return fragments


MAX_FUZZY_RESULTS = 100


def _match_rank(candidate: str, prefix: str) -> int:
    """Rank how well `candidate` matches `prefix`.

    0 means the candidate starts with the prefix (the best match), 1 means it
    only contains the prefix somewhere else, and -1 means it does not match.
    Prefix matching stays case-sensitive, like on the filesystem; only the
    substring fallback ignores case.
    """
    if candidate.startswith(prefix):
        return 0
    if prefix and prefix.lower() in candidate.lower():
        return 1
    return -1


def _fuzzy_matches(
    candidates: Iterable[str],
    prefix: str,
    *,
    max_results: int | None = None,
    max_fuzzy: int = MAX_FUZZY_RESULTS,
) -> list[str]:
    """Return prefix matches first, followed by substring matches.

    `max_fuzzy` caps the substring matches so a short prefix cannot flood the
    menu; prefix matches are never dropped. When `max_results` is given it caps
    the combined result instead (used by path completion).
    """
    exact: list[str] = []
    fuzzy: list[str] = []
    for candidate in candidates:
        rank = _match_rank(candidate, prefix)
        if rank == 0:
            exact.append(candidate)
        elif rank == 1:
            fuzzy.append(candidate)

    if max_results is not None:
        exact = exact[:max_results]
        fuzzy = fuzzy[: max(0, max_results - len(exact))]
    else:
        fuzzy = fuzzy[:max_fuzzy]
    return exact + fuzzy


def _completions(
    candidates: Iterable[str],
    prefix: str,
    meta: str | Callable[[str], str],
    *,
    start_position: int | None = None,
) -> Generator[Completion, None, None]:
    """Yield fuzzy completions for `candidates` sharing one display format."""
    start = -len(prefix) if start_position is None else start_position
    for name in _fuzzy_matches(candidates, prefix):
        yield Completion(
            name,
            start_position=start,
            display=_display(name, prefix),
            display_meta=meta(name) if callable(meta) else meta,
        )


WIN_EXEC_EXTS = frozenset({".exe", ".bat", ".cmd", ".ps1", ".py", ".com"})
NON_EXEC_SUFFIXES = (".dll", ".pyd", ".pyc", ".sys", ".msi", ".drv")
POSIX_NON_EXEC_SUFFIXES = (".so", ".a", ".o")

BUILTINS = ("cd", "exit", "import", "print", "pyexec", "pwd", "source",
            "clear", "from", "reload", "mv", "help", "update", "alias", "unalias")

COMMON = (
    "ls", "cat", "cp", "echo", "grep", "find", "mkdir", "rm",
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

        # On Windows a backslash is a path separator (`C:\Users\me`), not an
        # escape character, so it must never consume the following character.
        escape = os.name != "nt"

        def last_token_raw(text: str) -> tuple[str, bool]:
            quote = None
            start = 0
            i = 0
            while i < len(text):
                ch = text[i]
                if quote:
                    if ch == quote:
                        quote = None
                    elif ch == "\\" and quote == '"' and escape:
                        i += 1
                else:
                    if ch in ("'", '"'):
                        quote = ch
                    elif ch in " \t":
                        start = i + 1
                    elif ch == "\\" and escape:
                        i += 1
                i += 1
            return text[start:], quote is not None

        def split_lenient(s: str) -> list[str] | None:
            try:
                return shlex.split(s, posix=escape)
            except ValueError:
                pass
            quote = None
            i = 0
            while i < len(s):
                ch = s[i]
                if quote:
                    if ch == quote: quote = None
                    elif ch == '\\' and quote == '"' and escape: i += 1
                else:
                    if ch in ('"', "'"): quote = ch
                    elif ch == '\\' and escape: i += 1
                i += 1
            if quote:
                try:
                    return shlex.split(s + quote, posix=escape)
                except ValueError:
                    pass
            return None

        last, still_in = last_token_raw(text)
        in_string = in_string or still_in
        if last == '~': return  # don't remove this
        parts = split_lenient(last)
        if parts:
            token = parts[0]
            # With posix=False quotes are kept verbatim ('"a dir"'): drop the
            # surrounding pair so the quoted path resolves on disk.
            if not escape and len(token) >= 2 and token[0] == token[-1] and token[0] in ('"', "'"):
                token = token[1:-1]
            path = os.path.expanduser(token)
        else:
            path = os.path.expanduser(last)
        dirname = os.path.dirname(path) or "."
        prefix = os.path.basename(path).strip('"\'')

        try:
            entries = sorted(os.listdir(dirname))
        except OSError:
            return

        selected = _fuzzy_matches(entries, prefix, max_results=max_results)

        for item in selected:
            full = os.path.join(dirname, item)
            is_dir = os.path.isdir(full)
            if ' ' in item and not in_string:
                name = f'"{item}"'
            else:
                name = item
            yield Completion(
                name,
                display=_display(item, prefix),
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

        yield from _completions(sorted(os.environ), last_word, "environment")

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

                def attr_meta(attr: str) -> str:
                    try:
                        value = getattr(obj, attr)
                        return (
                            "method"
                            if callable(value)
                            else truncate(type(value).__name__, MAX_META_LEN)
                        )
                    except Exception:
                        return "attr"

                yield from _completions(attrs, prefix, attr_meta)
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

        candidates = sorted(set(localspace.keys()) | set(builtins_candidates))

        def name_meta(name: str) -> str:
            if name in localspace:
                return truncate(type(localspace[name]).__name__, MAX_META_LEN)
            if name in __builtins__:
                return truncate(type(__builtins__[name]).__name__, MAX_META_LEN)
            return "python"

        yield from _completions(candidates + KEYWORDS, last_word, name_meta)
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

        subcommands = [
            name
            for name in sorted(sub_cmd.keys())
            if name not in ("_global", "_flags") and name not in parts[:-1]
        ]
        # A dash can only start a flag, so do not fuzzy-match subcommands that
        # merely contain one: typing `git -` should list flags, not every
        # hyphenated subcommand.
        if not last_word.startswith("-"):
            yield from _completions(subcommands, last_word, "subcommand")

        # not auto complete flags unless user types them
        if last_word == "": return

        flags = [
            name
            for name in sorted(sub_cmd.get("_flags") or set())
            if name not in parts[:-1]
        ]
        yield from _completions(flags, last_word, "flag")

        global_flag_names = [
            name for name in sorted(global_flags) if name not in parts[:-1]
        ]
        yield from _completions(global_flag_names, last_word, "flag")

    def _module_completion(self, prefix: str):
        modules = (m for m in sorted(_module_names()) if not m.startswith("_"))
        yield from _completions(modules, prefix, "module")

    def _command_completion(self, text):
        commands = (cmd for cmd in self._get_commands() if cmd not in aliases)

        def command_meta(cmd: str) -> str:
            return "command" if cmd in BUILTINS else "program"

        yield from _completions(commands, text, command_meta)

    def _alias_completion(self, text):
        yield from _completions(aliases.keys(), text, "alias")

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
                    yield from self._module_completion(parts[-1])
                elif len(parts) == 3:
                    yield from _completions(["import"], parts[-1], "keyword")
                return
            if cmd == "import":
                if not lstripped.endswith(parts[-1]):
                    parts.append("")
                elif len(parts) == 2:
                    yield from self._module_completion(parts[-1])
                elif len(parts) == 3:
                    yield from _completions(["as"], parts[-1], "keyword")
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
