import os
import re
import time
import json
import keyword
import pkgutil
from string import whitespace
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from .environment import namespace
from .utils import truncate
from pathlib import Path

MAX_DISPLAY_LEN = 24
MAX_META_LEN = 12

BUILTINS = ("cd", "cp", "cat", "echo", "exit", "import", "ls", "print", "pyexec", "pwd", "source",
            "clear", "grep", "find", "from", "mkdir", "rm", "reload", "mv", "help")

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

COMMAND_TREE = {}
json_path = Path(__file__).parent / "data" / "commands.json"
try:
    with open(json_path, "r", encoding="utf-8") as f:
        COMMAND_TREE = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

class ShellCompleter(Completer):

    def __init__(self, cache_duration: int = 3) -> None:
        self._cache: list[str] = []
        self._cache_time: float = 0
        self._cache_duration = cache_duration
        self._get_commands()

    def _strip_ext(self, name: str) -> str:
        if os.name == "nt":
            ext = os.path.splitext(name)[1].lower()
            if ext in {".exe", ".bat", ".cmd", ".ps1", ".py", ".com"}:
                return os.path.splitext(name)[0]
        return name

    def _get_commands(self) -> list[str]:
        now = time.time()
        if self._cache and now - self._cache_time < self._cache_duration:
            return self._cache

        commands: set[str] = set(BUILTINS)
        for path in os.environ.get("PATH", "").split(os.pathsep):
            if not path or not os.path.isdir(path) or path.startswith("/mnt/"):
                continue
            try:
                for name in os.listdir(path):
                    if os.name == "nt":
                        name = name.lower()
                    full = os.path.join(path, name)
                    if os.path.isfile(full) and self._is_executable(name, full):
                        commands.add(self._strip_ext(name))
            except (OSError, PermissionError):
                continue

        self._cache = self._sort_commands(commands)
        self._cache_time = now
        return self._cache

    def _is_executable(self, name: str, full_path: str) -> bool:
        if name.endswith((".dll", ".pyd", ".pyc", ".sys", ".msi", ".drv")):
            return False

        if os.name == "nt":
            ext = os.path.splitext(name)[1].lower()
            return ext in {".exe", ".bat", ".cmd", ".ps1", ".py", ".com"}

        return os.access(full_path, os.X_OK) and not name.endswith((".so", ".a", ".o"))

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

    def _path_completions(self, text: str, max_results: int = 100):
        if text and text[-1] in whitespace: return
        last = text.split()[-1] if text.split() else ""
        if last == '~': return  # don't remove this
        path = os.path.expanduser(last)
        dirname = os.path.dirname(path) or "."
        prefix = os.path.basename(path)

        try:
            matches = []
            for item in os.listdir(dirname):
                if item.startswith(prefix):
                    matches.append(item)
                    if len(matches) >= max_results:
                        break

            for item in matches:
                full = os.path.join(dirname, item)
                is_dir = os.path.isdir(full)
                name = item + ("/" if is_dir else "")
                yield Completion(
                    name,
                    display=truncate(name, MAX_DISPLAY_LEN),
                    start_position=-len(prefix),
                    display_meta="directory" if is_dir else "file",
                )
        except OSError:
            pass

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
                if root in namespace:
                    obj = namespace[root]
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

        candidates = set(namespace.keys()) | set(builtins_candidates)
        for name in sorted(candidates) + KEYWORDS:
            if name in namespace:
                meta = truncate(type(namespace[name]).__name__, MAX_META_LEN)
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
        parts = text.split()
        if not parts: return
        sub_cmd = COMMAND_TREE.get(parts[0])
        if not sub_cmd: return
        global_flags: set[str] = set()
        if sub_cmd.get("_global"):
            global_flags.update(sub_cmd["_global"])
        if not text.endswith(parts[-1]):
            parts.append("")
        last_word = parts[-1]

        for part in parts[1:-1]:
            if part.startswith("-"):
                continue
            if sub_cmd.get("_global"):
                global_flags.update(sub_cmd["_global"])
            if sub_cmd.get(part):
                sub_cmd = sub_cmd[part]
            else:
                sub_cmd = {}
                break

        for name in sorted(sub_cmd.keys()):
            if name == "_global" or name == "_flags": continue
            if name in parts: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="subcommand"
                )

        for name in sorted(sub_cmd.get("_flags") or set()):
            if name in parts: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="flag",
                )

        for name in sorted(global_flags):
            if name in parts: continue
            if name.startswith(last_word):
                yield Completion(
                    name,
                    start_position=-len(last_word),
                    display=truncate(name, MAX_DISPLAY_LEN),
                    display_meta="flag",
                )

    def get_completions(self, document: Document, complete_event):
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
            for cmd in self._get_commands():
                if cmd.startswith(lstripped):
                    meta = "command" if cmd in BUILTINS else "program"
                    yield Completion(
                        cmd,
                        start_position=-len(lstripped),
                        display=truncate(cmd, MAX_DISPLAY_LEN),
                        display_meta=meta,
                    )

        # special built-ins
        parts = lstripped.split()
        if len(parts) >= 1:
            cmd = parts[0]
            if cmd in ("print", "pyexec"):
                param_text = lstripped[len(cmd):].lstrip()
                yield from self._python_completion(param_text)
                return
            if cmd == "from":
                if not lstripped.endswith(parts[-1]):
                    parts.append("")
                elif len(parts) == 2:
                    for module in pkgutil.iter_modules():
                        name: str = module.name
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
                    for module in pkgutil.iter_modules():
                        name: str = module.name
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

def completer_init() -> None:
    namespace["shell_completer"] = ShellCompleter()
