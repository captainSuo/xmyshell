from copy import deepcopy
from typing import TypedDict
from .environment import update_namespace

__all__ = [
    "load_theme",
    "XmyShellTheme",
    "THEME_DEFAULT",
    "THEME_LIGHT",
    "THEME_NORD",
    "THEME_CATPPUCCIN",
    "THEME_MINIMAL",
    "THEME_EMPTY",
    "THEME_CLASSIC"
]


class XmyShellTheme(TypedDict, total=False):
    shell_prompt: str
    shell_rprompt: str
    prompt_placeholder: str
    prompt_style: dict[str, str]


THEME_DEFAULT: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='ansigreen'><b>{getlogin()}</b></style>"
        "<style fg='ansicyan'>@</style>"
        "<style fg='ansiblue'><b>{socket.gethostname()}</b></style>"
        "<style fg='ansiblue'> ➜ </style>"
        "<style fg='ansimagenta'> </style>"
        "<style fg='ansiblue'>{getcwd().replace(HOME_DIR, '~')}</style> "
        "<style fg='ansicyan'>{exec_duration//1_000_000}ms</style>"
        "{'<style fg=\"ansired\"> ✗</style>' if exit_code else ''}"
        "\n<style fg='ansiblue'>❯ </style>"
    ),
    "shell_rprompt": (
        "<style fg='ansicyan'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</style>"
    ),
    "prompt_style": {
        "completion-menu": "bg:#282d34",
        "completion-menu.completion": "bg:#282d34 #e0e0d0",
        "completion-menu.completion.current": "bg:#282d34 #9090f0",
        "completion-menu.meta.completion": "bg:#282d34 #a0d0f0 italic",
        "completion-menu.meta.completion.current": "bg:#9090f0 #282d34 italic",
    },
}


THEME_LIGHT: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='ansiblack'><b>{getlogin()}</b></style>"
        "<style fg='ansired'>@</style>"
        "<style fg='ansiblue'><b>{socket.gethostname()}</b></style>"
        "<style fg='ansiblack'> ➜ </style>"
        "<style fg='ansiblue'> </style>"
        "<style fg='ansiblue'>{getcwd().replace(HOME_DIR, '~')}</style> "
        "<style fg='ansidarkgray'>{exec_duration//1_000_000}ms</style>"
        "{'<style fg=\"ansired\"> ✗</style>' if exit_code else ''}"
        "\n<style fg='ansiblue'>❯ </style>"
    ),
    "shell_rprompt": (
        "<style fg='ansiblack'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</style>"
    ),
    "prompt_style": {
        "completion-menu": "bg:#f5f5f5",
        "completion-menu.completion": "bg:#f5f5f5 #000000",
        "completion-menu.completion.current": "bg:#e0e0e0 #0000ff",
        "completion-menu.meta.completion": "bg:#f5f5f5 #6666cc italic",
        "completion-menu.meta.completion.current": "bg:#0000ff #ffffff italic",
    },
}


THEME_NORD: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='#88c0d0'>╭─</style>"
        "<style fg='#d8dee9'><b>{getlogin()}</b></style>"
        "<style fg='#81a1c1'>@</style>"
        "<style fg='#8fbcbb'><b>{socket.gethostname()}</b></style>"
        "<style fg='#d8dee9'> {getcwd().replace(HOME_DIR, '~')} </style>"
        "{'<style fg=\"#bf616a\"> ✗</style>' if exit_code else ''}"
        "\n<style fg='#88c0d0'>╰─❯</style> "
    ),
    "shell_rprompt": "",
    "prompt_style": {
        "completion-menu": "bg:#2e3440",
        "completion-menu.completion": "bg:#2e3440 #d8dee9",
        "completion-menu.completion.current": "bg:#434c5e #88c0d0",
        "completion-menu.meta.completion": "bg:#2e3440 #81a1c1 italic",
        "completion-menu.meta.completion.current": "bg:#88c0d0 #2e3440 italic",
    },
}


THEME_CATPPUCCIN: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='#89b4fa'>╭─</style>"
        "<style fg='#a6e3a1'><b>{getlogin()}</b></style>"
        "<style fg='#94e2d5'>@</style>"
        "<style fg='#89b4fa'><b>{socket.gethostname()}</b></style>"
        "<style fg='#cdd6f4'> {getcwd().replace(HOME_DIR, '~')} </style>"
        "{'<style fg=\"#f38ba8\"> ✗</style>' if exit_code else ''}"
        "\n<style fg='#89b4fa'>╰─❯</style> "
    ),
    "shell_rprompt": "",
    "prompt_style": {
        "completion-menu": "bg:#1e1e2e",
        "completion-menu.completion": "bg:#1e1e2e #cdd6f4",
        "completion-menu.completion.current": "bg:#313244 #89b4fa",
        "completion-menu.meta.completion": "bg:#1e1e2e #cba6f7 italic",
        "completion-menu.meta.completion.current": "bg:#89b4fa #1e1e2e italic",
    },
}


THEME_POWERLINE: XmyShellTheme = {
    "shell_prompt": (
        "<style bg='#8ae234' fg='#2e3436'> {getlogin()} </style>"
        "<style bg='#729fcf' fg='#8ae234'></style>"
        "<style bg='#729fcf' fg='#2e3436'> {socket.gethostname()} </style>"
        "<style bg='#3465a4' fg='#729fcf'></style>"
        "<style bg='#3465a4' fg='#d3d7cf'> {getcwd().replace(HOME_DIR, '~')} </style>"
        "<style bg='#2e3436' fg='#3465a4'></style>"
        "<style bg='#2e3436' fg='#d3d7cf'>"
        "{' ✗' if exit_code else ''}"
        " </style>"
        "\n<style fg='#8ae234'>❯</style> "
    ),
    "shell_rprompt": (
        "<style fg='#d3d7cf'></style>"
        "<style bg='#3465a4' fg='#d3d7cf'> {datetime.now().strftime('%H:%M')} </style>"
    ),
    "prompt_style": {
        "completion-menu": "bg:#2e3436",
        "completion-menu.completion": "bg:#2e3436 #d3d7cf",
        "completion-menu.completion.current": "bg:#3465a4 #8ae234",
        "completion-menu.meta.completion": "bg:#2e3436 #729fcf italic",
        "completion-menu.meta.completion.current": "bg:#8ae234 #2e3436 italic",
    },
}


THEME_MINIMAL: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='ansiblue'>[</style>"
        "<style fg='ansigreen'>{getcwd().replace(HOME_DIR, '~')}</style>"
        "<style fg='ansiblue'>]</style>"
        "<style fg='ansigray'> $ </style>"
    ),
    "shell_rprompt": "",
    "prompt_style": {
        "completion-menu": "bg:#1e1e2e",
        "completion-menu.completion": "bg:#1e1e2e #cdd6f4",
        "completion-menu.completion.current": "bg:#313244 #89b4fa",
        "completion-menu.meta.completion": "bg:#1e1e2e #cba6f7 italic",
        "completion-menu.meta.completion.current": "bg:#89b4fa #1e1e2e italic",
    },
}


THEME_EMPTY: XmyShellTheme = {
    "shell_prompt": "<style fg='ansigray'>$ </style>",
    "shell_rprompt": "",
    "prompt_style": {
        "completion-menu": "",
        "completion-menu.completion": "",
        "completion-menu.completion.current": "",
        "completion-menu.meta.completion": "",
        "completion-menu.meta.completion.current": "",
    },
}


THEME_CLASSIC: XmyShellTheme = {
    "shell_prompt": (
        "<style fg='ansigreen'><b>{getlogin()}</b></style>@"
        "<style fg='ansicyan'><b>{socket.gethostname()}</b></style>:"
        "<style fg='ansibrightmagenta'>{getcwd().replace(HOME_DIR, '~')}</style>"
        "<style fg='ansigreen'>$</style> "
    ),
    "shell_rprompt": (
        "<style fg='ansidarkgray'>[{datetime.now().strftime('%H:%M')}]</style>"
    ),
    "prompt_style": {
        "completion-menu": "bg:#2e3440",
        "completion-menu.completion": "bg:#2e3440 #d8dee9",
        "completion-menu.completion.current": "bg:#434c5e #88c0d0",
        "completion-menu.meta.completion": "bg:#2e3440 #81a1c1 italic",
        "completion-menu.meta.completion.current": "bg:#88c0d0 #2e3440 italic",
    },
}


def load_theme(theme: XmyShellTheme) -> None:
    update_namespace(deepcopy(theme))

