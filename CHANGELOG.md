# Change Log


## [0.2.2] 2026-09-18 Bug fixs
### Fixed
- Completer now completes `unalias`.


## [0.2.1] 2026-09-18 New Features
### Added
- `unalias` command and function.
- Alias completer.


## [0.2.0] 2026-09-18 Bug fixs & New Features
### Fixed
- Fix update

### Improved
- Automaticlly unpack Sequence objects in expansion.

### Added
- Built-in `cat(f)` function as a shortcut for `open(f).read()`.
- Built-in `alias(altname, target)` function, same as `alias` command.
- Built-in `PROFILE` variable as a shortcut to the path of config file.
- `alias` command for command aliases. eg. `alias ll='ls -l'`


## [0.1.4] 2026-09-17 Bug fixs & Features
### Fixed
- Fix update on Linux

### Added
(feat) Add --update flag to executable


## [0.1.3] 2026-09-17 Features
### Improved
- Support slash paths on Windows.
- Set `__name__` to `"__main__"` when running Python scripts.

### Added
- Add the `xmyshell.update` module, accessible via the `update <version>` command (version optional).


## [0.1.2] 2026-09-11 Minor feature improvement

### Improved
- `source` and `import` commands now can import modules from current working directory.
- Completes built-in modules for the import command.


## [0.1.1] 2026-09-10 Minor bug-fixes

### Improved
- More subcommands completion.
- Addjust built-in themes.

### Fixed
- Fix on auto bracket pairing.
- Paths ending with '.' now will also be completed.
