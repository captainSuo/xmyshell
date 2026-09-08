import os
import sys
import runpy
import subprocess
from .environment import namespace
from .utils import pywarning, pyerror, getcwd
from .meta import HELP_MESSAGE

def _reload() -> None:
    # lazy import
    from .init import xmyshell_reload
    xmyshell_reload()


def xmyshell_source(path: str) -> None:
    _updated = runpy.run_path(os.path.expanduser(path), namespace)
    namespace.clear()
    namespace.update(_updated)


def pyeval(cmd_line: str) -> str:
    if not isinstance(cmd_line, str):
        return ""

    result = []
    i = 0
    n = len(cmd_line)

    while i < n:
        if cmd_line[i] == '{':
            # {{ -> {
            if i + 1 < n and cmd_line[i+1] == '{':
                result.append('{')
                i += 2
                continue

            j = i + 1
            depth = 1
            while j < n and depth > 0:
                if cmd_line[j] == '{':
                    depth += 1
                elif cmd_line[j] == '}':
                    depth -= 1
                j += 1

            if depth == 0:
                expr = cmd_line[i+1:j-1].strip()
                if expr:
                    try:
                        val = eval(expr, dict(os.environ), namespace)
                        result.append(str(val) if val is not None else '')
                    except Exception as e:
                        pywarning(f"An error occured when unfolding {expr!r}, using original string instead"
                                  f"\n{type(e).__name__}: {e}")
                        result.append(cmd_line[i:j])
                else:
                    result.append('{}')
                i = j
                continue
            else:
                result.append(cmd_line[i])
                i += 1
        elif cmd_line[i] == '}':
            # }} -> }
            if i + 1 < n and cmd_line[i+1] == '}':
                result.append('}')
                i += 2
                continue
            else:
                result.append(cmd_line[i])
                i += 1
        else:
            result.append(cmd_line[i])
            i += 1

    return ''.join(result)


def xmyshell_raw_command(cmd_line: str) -> int | None:
    args = cmd_line.split()
    if len(args) == 0: return 0
    command = args[0]
    match command:
        case "pyexec":
            code = cmd_line[len(command):].strip()
            if not code:
                pyerror("pyexec: missing code")
                return -1
            try:
                exec(code, dict(os.environ), namespace)
                namespace["last_error"] = None
                return 0
            except Exception as e:
                import traceback
                namespace["last_error"] = e
                namespace["last_traceback"] = traceback.format_exc()
                pyerror(f"{type(e).__name__}: {e}")
                return -1

        case "export":
            code: str = cmd_line[len(command):].strip()
            if not code:
                pyerror("export: missing code")
                return -1
            try:
                export_source, export_target = code.split('=', 1)
                export_source = export_source.strip()
                os.environ[export_source] = pyeval(export_target)
                return 0
            except Exception as e:
                pyerror(f"{type(e).__name__}: {e}")
                return -1

        case "print":
            expr = cmd_line[len(command):].strip()
            if not expr:
                pyerror("print: missing expression")
                return -1
            try:
                result = eval(expr, dict(os.environ), namespace)
                print(result)
                return 0
            except Exception as e:
                pyerror(f"{type(e).__name__}: {e}")
                return -1

        case "reload":
            _reload()
            return 0

    if command.startswith("import") or command.startswith("from"):
        try:
            exec(cmd_line, dict(os.environ), namespace)
            return 0
        except Exception as e:
            pyerror(f"{type(e).__name__}: {e}")
            return -1


def xmyshell(cmd_line: str) -> int:
    cmd_line = cmd_line.strip()
    if not cmd_line:
        return 0

    target_var = None
    sh_cmd = None
    if "=>" in cmd_line:
        cmd_line, target_var = (part.strip() for part in cmd_line.split("=>", 1))
    if "|>" in cmd_line:
        cmd_line, sh_cmd = cmd_line.split("|>", 1)

    if sh_cmd:
        proc = subprocess.Popen(
            sh_cmd,
            shell=True,
            env=os.environ,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        old_stdout = sys.stdout
        sys.stdout = proc.stdin
        return_code = xmyshell_raw_command(cmd_line)
        if return_code is None:
            pyerror(f"'{cmd_line}' cannot be used in a pipeline with '|>'")
            return -1
        assert proc.stdin
        proc.stdin.close()
        sys.stdout = old_stdout
        if target_var:
            result, _ = proc.communicate()
            namespace[target_var] = result
            return proc.returncode
        else:
            return proc.wait()

    if target_var:
        from io import StringIO
        from contextlib import redirect_stdout
        f = StringIO()
        with redirect_stdout(f):
            return_code = xmyshell_raw_command(cmd_line)
        if return_code is not None:
            namespace[target_var] = f.getvalue()
            return return_code
    else:
        return_code = xmyshell_raw_command(cmd_line)
        if return_code is not None:
            return return_code

    try:
        cmd_line = pyeval(cmd_line).strip()
    except Exception as e:
        pyerror(f"{type(e).__name__}: {e}")
        return -1

    if not cmd_line:
        return 0

    args = cmd_line.split()
    command = args[0]

    match command:
        case "cd":
            splited = cmd_line.split(maxsplit=1)
            target_dir = "~" if len(splited) <= 1 else splited[1].strip()
            try:
                target_dir = os.path.expanduser(target_dir)
                # only works on Windows
                if os.name == "nt" and target_dir.startswith("/"):
                    import re

                    if target_dir.startswith("/"):
                        m = re.match(r"^/([a-zA-Z])/", target_dir)
                        if m:
                            drive = m.group(1).upper()
                            target_dir = drive + ":/" + target_dir[3:]
                os.chdir(target_dir)
                return 0
            except FileNotFoundError:
                pyerror(f"file not found: '{target_dir}'")
                return -1
            except NotADirectoryError:
                pyerror(f"not a directory: '{target_dir}'")
                return -1

        case "help":
            print(HELP_MESSAGE)
            return 0

        case "clear":
            print("\033[2J\033[H", end="")
            return 0

        case "source":
            if len(args) < 2:
                pyerror("source: missing script")
                return -1
            try:
                xmyshell_source(args[1])
                return 0
            except Exception as e:
                pyerror(f"source error: {e}")
                return -1

        case "pwd":
            print(getcwd())
            return 0

        case "exit":
            sys.exit(0)

    if target_var:
        result = subprocess.run(
            cmd_line, shell=True, env=os.environ, capture_output=True, text=True
        )
        namespace[target_var] = result.stdout
    else:
        result = subprocess.run(cmd_line, shell=True, env=os.environ)

    return result.returncode
