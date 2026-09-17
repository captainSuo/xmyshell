# Change Log

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
