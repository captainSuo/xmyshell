# XmyShell

**`XmyShell`** is a shell-like tool built on top of `prompt_toolkit` which provides a persistent Python runtime. The main process is Python, and shell commands are executed in subprocesses. It provides a persistent Python namespace, inline Python evaluation, and command output capture. It can be useful if you want Python evaluation in a shell or execute shell command conveniently in Python REPL environment.

## Features

### Command Line Features

- Persistent Python namespace across commands (variables, imports, functions)
- Expand inline Python expressions within `{}`, using independent namespace.
```
❯ mkdir {" ".join(f"test{i}" for i in range(10))}
❯ ls
test0  test1  test2  test3  test4  test5  test6  test7  test8  test9
```

- Evaluate and print Python expressions with `print`
```
❯ print 1 + 1
2
```

- Execute Python statements with `pyexec`
```
❯ pyexec files = [f for f in os.listdir('.') if f.endswith('.py')]
❯ print len(files)
3
```

- Capture command output into a Python variable with `=>`.
```
❯ which python => path
❯ print path
/usr/bin/python
❯ cd {dirname(path)}
❯ pwd
/usr/bin
```

- Redirect the output of Python commands (`print`, `pyexec`) with `|>`
```
❯ print "\n".join(str(i) for i in range(100)) |> grep 42 => result
❯ print result
42
```

- Built-in `source` command to run python scripts.
```
❯ which python
/usr/bin/python
❯ source .venv/bin/activate_this.py
❯ which python
/tmp/test/.venv/bin/python
```

- Built-in `export` command.
```
❯ pyexec foo = "foo"
❯ export ENV_VAR={foo}bar
❯ print ENV_VAR
foobar
```

- Built-in `import` command.
```
❯ import numpy as np
❯ from math import *
```

- Reload with `reload` command.
```
❯ reload
```

- Syntax highlighting via `prompt_toolkit`
- Powerful auto-completion, history search, and automatic bracket/quote pairing
- Startup configuration: `~/.xmyshell/config.py` loaded at launch
- Cross-platform (Windows, Linux, macOS)

### Built-in Helper Functions

- `getlogin()`
Returns the current username.

- `getcwd()`
Returns the absolute path of the current working directory.

- `dirname(path)`
Returns the parent directory of a path.

- `basename(path)`
Returns the final component of a path.

### Reserved global varibles
- `exit_code`
The exit code of the last command.

- `exec_duration`
The duration which last command took.

### Keyboard Shortcuts
- `↑↓` -> Navigate through command history.
- `→` -> Apply selected history entry to the prompt.
- `Ctrl+R` -> Reverse incremental searching (history).
- `Ctrl+D` -> Exit XmyShell.
- Auto bracket/parenthesis/quote pairing


## Limitations

**XmyShell** is Python‑first. This brings power, but also intentional trade‑offs.

- **No `source` for shell scripts** — `source` executes Python files via `runpy.run_path()`. Shell scripts (e.g., `venv/bin/activate`) won't work; use `activate_this.py` instead.

- **No `deactivate`** — This is a shell function, not a real command. Virtual environments can be deactivated by reloading environment (`reload`) or manually restarting a session.

- **Shell scripts cannot modify the current environment** — Every external command runs in a fresh subprocess; `cd`, `export`, aliases, and function definitions inside a script are lost on exit.

- **No pipelines between built‑in commands** — `print` and `pyexec` do not support `|`. Use Python variables to pass data.

- **External command overhead** — Each subprocess spawns with minor delays.

**Why?** `XmyShell` is **NOT** a Bash replacement. It's a Python‑native environment for those who want Python's power at the command line.

## Usage

Start `XmyShell` by running the main module. Commands that are not built-in are passed to `/bin/sh` (or the system shell) for execution.
```bash
$ xmyshell
XmyShell 0.1.0
❯
```