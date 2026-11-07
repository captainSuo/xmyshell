# XmyShell

**`XmyShell`** is a shell-like tool built on top of `prompt_toolkit` which provides a persistent Python runtime. The main process is Python, and shell commands are executed in subprocesses. It provides a persistent Python namespace, inline Python evaluation, and command output capture. It can be useful if you want Python evaluation in a shell or execute shell command conveniently in Python REPL environment.

## Get started

### Installation
```bash
pip install xmyshell
```

### Start
```bash
$ xmyshell
XmyShell 0.1.0
Initialized with 296ms.
Username@hostname ➜  ~ 0ms
❯
```

### Learn more through `help`.
```bash
❯ help
```

## Features

### Command Line Features

- Persistent Python namespace across commands (variables, imports, functions)
- Expand inline Python expressions within `{}`, using independent namespace.
```bash
❯ mkdir {" ".join(f"test{i}" for i in range(10))}
❯ ls
test0  test1  test2  test3  test4  test5  test6  test7  test8  test9
```

- Evaluate and print Python expressions with `print`
```bash
❯ print 1 + 1
2
```

- Execute Python statements with `pyexec`
```bash
❯ pyexec files = [f for f in os.listdir('.') if f.endswith('.py')]
❯ print len(files)
3
```

- Capture command output into a Python variable with `=>`.
```bash
❯ which python => path
❯ print path
/usr/bin/python
❯ cd {dirname(path)}
❯ pwd
/usr/bin
```

- Redirect the output of Python commands (`print`, `pyexec`) with `|>`
```bash
❯ print "\n".join(str(i) for i in range(100)) |> grep 42 => result
❯ print result
42
```

- Built-in `source` command to run python scripts.
```bash
❯ which python
/usr/bin/python
❯ source .venv/bin/activate_this.py
❯ which python
/tmp/test/.venv/bin/python
```

- Built-in `export` command.
```bash
❯ pyexec foo = "foo"
❯ export ENV_VAR={foo}bar
❯ print ENV_VAR
foobar
```

- Built-in `import` command.
```bash
❯ import numpy as np
❯ from math import *
```

- Reload with `reload` command.
```bash
❯ reload
```

- Update xmyshell (optionally to a specific version).
```bash
❯ udpate
```
or
```bash
❯ update 0.1.3
```

- Alias
```bash
❯ alias ll='ls -lh'
❯ unalias ll
```

- Lists, tuples, generators, etc. will be expanded into shell arguments.
E.g. `{["arg1", "arg2 xxx"]}` will be expanded into `arg1 'arg2 xxx'`

Here is an example (though there are other ways to do this, it is just an example )
```bash
❯ pip install {cat("requirements.txt").splitlines()}
```

- Multiline input with ending `\`.
```python
❯ pyexec
def foo():
    print("Hello!")
❯ pyexec foo()
Hello!
```

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

- `cat(file)`
Shortcut for `open(file).read()`.

- `alias(altname, target)`
Same as the command.

- `unalias(altname)`
Same as the command.


### Reserved global varibles
- `exit_code`
The exit code of the last command.

- `exec_duration`
The duration which last command took.

- `last_error`
The error raised from last Python operation (if exists).

- `last_traceback`
The traceback of last Python operation (if exists).

- `ans`
The result from last print command.

- `SHOW_WELCOME`
Toggle whether to show welcome message when staring.

- `SHELL_CMD`
Shell command line prefix, defaults to `["cmd", "/c"]` on Windows and `["bin/sh", "-c"]` on other OS.

- `HOME_DIR`
The home directory, similar to `~`.

- `PROFILE`
The path of config file.

### Keyboard Shortcuts
- `↑↓` -> Navigate through command history.
- `→` -> Apply selected history entry to the prompt.
- `Ctrl+R` -> Reverse incremental searching (history).
- `Ctrl+Z` -> Undo.
- `Ctrl+Y` -> Redo.
- `Ctrl+G` -> Hide completions.
- `Ctrl+D` -> Exit XmyShell.
- Auto bracket/parenthesis/quote pairing


### Stubs

You can write your xmyshell script with these imports:
```python
from xmyshell.themes import ... # themes
from xmyshell.stubs import ...  # stubs for built-in names
```

## Examples / Bash Equivalents

Here are some equivalent forms of common Bash patterns.

### Capture command output into a variable

Bash:
```bash
python_path=$(which python)
echo "Python is at $python_path"
```

XmyShell:
```bash
which python => python_path
print "Python is at " + python_path
```

### Expand file contents into command arguments

Bash:
```bash
pip install $(cat requirements.txt)
```

XmyShell:
```bash
pip install {cat("requirements.txt").splitlines()}
```

`cat()` is a built-in XmyShell helper equivalent to `open(file).read()`. The list returned by `splitlines()` is expanded into separate shell arguments.

### Brace expansion / sequence expansion

Bash:
```bash
echo {0..4}
```

XmyShell:
```bash
echo {range(5)}
```

Bash:
```bash
touch file{0..4}
```

XmyShell:
```bash
touch {f"file{i}" for i in range(5)}
```

Bash:
```bash
mkdir test{0..9}
```

XmyShell:
```bash
mkdir {f"test{i}" for i in range(10)}
```

Lists, tuples, generators, and similar iterables are expanded into separate shell arguments.

### Python expressions and statements

Bash:
```bash
python -c 'print(1 + 1)'
```

XmyShell:
```bash
print 1 + 1
```

Bash:
```bash
python -c 'files=[f for f in __import__("os").listdir(".") if f.endswith(".py")]; print(len(files))'
```

XmyShell:
```bash
pyexec files = [f for f in os.listdir(".") if f.endswith(".py")]
print len(files)
```

`pyexec` executes Python statements and keeps them in the persistent Python namespace.

### Pipe Python output into shell commands

Bash:
```bash
python -c "print('\n'.join(str(i) for i in range(100)))" | grep 42
```

XmyShell:
```bash
print "\n".join(str(i) for i in range(100)) |> grep 42
```

Save the piped result into a variable:

Bash:
```bash
result=$(python -c "print('\n'.join(str(i) for i in range(100)))" | grep 42)
echo "$result"
```

XmyShell:
```bash
print "\n".join(str(i) for i in range(100)) |> grep 42 => result
print result
```

Note: in XmyShell, redirect `print` / `pyexec` output with `|>`, not `|`.

### Environment variables

Bash:
```bash
export ENV_VAR=foobar
echo "$ENV_VAR"
```

XmyShell:
```bash
pyexec foo = "foo"
export ENV_VAR={foo}bar
print ENV_VAR
```

Build an environment variable dynamically:

Bash:
```bash
export PROJECT_HOME="$HOME/projects/$(basename "$PWD")"
```

XmyShell:
```bash
export PROJECT_HOME={HOME_DIR + "/projects/" + basename(getcwd())}
```

### Aliases

Bash:
```bash
alias ll='ls -lh'
unalias ll
```

XmyShell:
```bash
alias ll='ls -lh'
unalias ll
```

The syntax is essentially the same.

### Run Python scripts / virtual environments

Run a Python script in Bash:
```bash
python script.py
```

In XmyShell, load a Python script into the persistent namespace of the current session:
```bash
source script.py
```

Activate a virtual environment:

Bash:
```bash
source .venv/bin/activate
```

XmyShell:
```bash
source .venv/bin/activate_this.py
```

Deactivate

Bash:
```bash
deactivate
```

XmyShell:
```bash
reload
```

XmyShell's `source` executes Python files via `runpy.run_path()`; it does not execute shell scripts. It also has no `deactivate`. Use `reload` to reset the environment.

### Check the exit code of the last command

Bash:
```bash
ls /nonexistent
echo $?
```

XmyShell:
```bash
ls /nonexistent
print exit_code
```

`exit_code` is a reserved XmyShell global variable that holds the exit code of the last command.

### Iterate over files and process them

Bash:
```bash
for f in *.txt; do
  cp "$f" "$f.bak"
done
```

In XmyShell, this kind of task is usually better written directly in Python:
```bash
pyexec import shutil; [shutil.copy(f, f + ".bak") for f in os.listdir(".") if f.endswith(".txt")]
```

### Define a function with multiple lines

Bash:
```bash
greet() {
  echo "Hello, $1!"
}
greet World
```

XmyShell:
```bash
pyexec
def greet(name):
    return "Hello, " + name + "!"
pyexec greet("World")
```

The function definition stays in the persistent Python namespace of the current session.

---

### Notes

- `{...}` contains a Python expression, not Bash command substitution.
- `=>` saves command output into a Python variable.
- `|>` sends Python output from `print` / `pyexec` into a shell pipeline.
- External shell commands run in subprocesses and cannot modify the current directory or environment of the main XmyShell process. Use XmyShell's built-in `cd`, `export`, `alias`, etc. instead.
- `source` only executes Python scripts, not shell scripts.


## Limitations

**XmyShell** is Python‑first. This brings power, but also intentional trade‑offs.

- **No `source` for shell scripts** — `source` executes Python files via `runpy.run_path()`. Shell scripts (e.g., `venv/bin/activate`) won't work; use `activate_this.py` instead.

- **No `deactivate`** — This is a shell function, not a real command. Virtual environments can be deactivated by reloading environment (`reload`) or manually restarting a session.

- **Shell scripts cannot modify the current environment** — Every external command runs in a fresh subprocess; `cd`, `export`, aliases, and function definitions inside a script are lost on exit.

- **External command overhead** — Each subprocess spawns with minor delays.

**Why?** `XmyShell` is **NOT** a Bash replacement. It's a Python‑native environment for those who want Python's power at the command line.
