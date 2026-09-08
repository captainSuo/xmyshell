import re
import keyword
import inspect
from collections.abc import Callable
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import FormattedText
from .environment import namespace

def _is_number_literal(s: str) -> bool:
    try:
        import ast  # lazy
        result = ast.literal_eval(s)
        return isinstance(result, (int, float, complex))
    except (ValueError, SyntaxError):
        return False

def _split_with_braces_and_pipes(line: str) -> list[str]:
    parts = []
    outer_buf = []
    inner_buf = []
    depth = 0
    i = 0
    n = len(line)

    while i < n:
        ch = line[i]

        if i + 1 < n and ((ch == '{' and line[i+1] == '{') or (ch == '}' and line[i+1] == '}')):
            seq = line[i:i+2]
            if depth == 0:
                outer_buf.extend(seq)
            else:
                inner_buf.extend(seq)
            i += 2
            continue

        if ch == '{':
            if depth == 0:
                if outer_buf:
                    parts.append(''.join(outer_buf))
                    outer_buf = []
                parts.append('{')
                depth = 1
                inner_buf = []
            else:
                inner_buf.append(ch)
                depth += 1
            i += 1

        elif ch == '}':
            if depth == 0:
                outer_buf.append(ch)
            else:
                depth -= 1
                if depth == 0:
                    parts.append(''.join(inner_buf))
                    parts.append('}')
                    inner_buf = []
                else:
                    inner_buf.append(ch)
            i += 1

        elif ch == '|':
            if depth == 0:
                if outer_buf:
                    parts.append(''.join(outer_buf))
                    outer_buf = []
                parts.append('|')
            else:
                inner_buf.append(ch)
            i += 1

        else:
            if depth == 0:
                outer_buf.append(ch)
            else:
                inner_buf.append(ch)
            i += 1

    if outer_buf:
        parts.append(''.join(outer_buf))

    if depth > 0 and inner_buf:
        parts.append(''.join(inner_buf))

    return parts

def _lex_cmd(cmd: str, first_word: bool = True) -> list[tuple[str, str]]:
    parts: list[str] = re.split(r"(\s+)", cmd)
    result: list[tuple[str, str]] = []
    for part in parts:
        if part == "":
            continue
        if part.isspace():
            result.append(("", part))
            continue
        if first_word:
            result.append(("ansigreen bold", part))
            first_word = False
            continue
        if part.startswith("-"):
            result.append(("ansibrightblue", part))
            continue
        # if part in keyword.kwlist:
        #     result.append(("ansibrightmagenta bold", part))
        #     continue
        if _is_number_literal(part):
            result.append(("ansibrightblue", part))
            continue
        result.append(("", part))
    return result


STYLE_KEYWORD = "ansibrightmagenta bold"
STYLE_NUMBER = "ansiblue"
STYLE_VARIABLE = "ansibrightcyan"
STYLE_FUNCTION = "ansibrightblue"
STYLE_CLASS = "ansibrightred"

TOKEN_PATTERN = re.compile(r'[a-zA-Z_]\w*|\d+\.?\d*')

def _lex_python(text: str) -> list[tuple[str, str]]:
    result = []
    pos = 0

    for match in TOKEN_PATTERN.finditer(text):
        start, end = match.span()
        if start > pos:
            result.append(("", text[pos:start]))

        token = match.group()

        if token.isdigit() or (token.replace('.', '').isdigit() and token.count('.') <= 1):
            result.append((STYLE_NUMBER, token))
        elif keyword.iskeyword(token):
            result.append((STYLE_KEYWORD, token))
        else:
            if token in namespace:
                obj = namespace[token]
                if inspect.isclass(obj):
                    style = STYLE_CLASS
                elif callable(obj):
                    style = STYLE_FUNCTION
                else:
                    style = STYLE_VARIABLE
            else:
                style = STYLE_VARIABLE
            result.append((style, token))

        pos = end

    if pos < len(text):
        result.append(("", text[pos:]))

    return result

def _lex_sh(line: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    parts: list[str] = _split_with_braces_and_pipes(line)
    in_expr: bool = False
    first_word: bool = True
    for part in parts:
        if part.startswith("|"):
            first_word = True
            result.append(("ansicyan", part))
        elif part == "{":
            result.append(("ansimagenta", "{"))
            in_expr = True
            first_word = False
        elif part == "}":
            result.append(("ansimagenta", "}"))
            in_expr = False
        elif in_expr:
            result.extend(_lex_python(part))
        else:
            result.extend(_lex_cmd(part, first_word))
    return result

def _lex_line(line: str) -> list[tuple[str, str]]:

    result: list[tuple[str, str]] = []

    target_var = None
    if "=>" in line:
        line, target_var = line.split("=>", 1)

    leading_spaces = line[:len(line) - len(line.lstrip())]
    _splited = line.lstrip().split(None, 1)
    _cmd = _splited[0] if _splited else ""
    if _cmd in ["pyexec", "print"]:
        sh_cmd = None
        if "|>" in line:
            line, sh_cmd = line.split("|>", 1)
        result.append(("", leading_spaces))
        result.append(("ansigreen bold", _cmd))
        result.extend(_lex_python(line[len(leading_spaces) + len(_cmd):]))
        if sh_cmd is not None:
            result.append(("ansiblue", "|>"))
            result.extend(_lex_sh(sh_cmd))
    else:
        result.extend(_lex_sh(line))

    if target_var is not None:
        result.append(("ansiblue", "=>"))
        result.append(("ansibrightcyan", target_var))

    return result


class XmyShellLexer(Lexer):
    def lex_document(self, document) -> Callable[[int], FormattedText]:
        def _lex(line_number: int) -> FormattedText:
            lines = document.text.splitlines()
            if line_number >= len(lines):
                return FormattedText([("", "")])
            line = lines[line_number]
            return FormattedText(_lex_line(line))

        return _lex
