import time
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.selection import SelectionState
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.bindings.auto_suggest import load_auto_suggest_bindings
from dataclasses import dataclass

@dataclass
class BufferInfo:
    text: str
    cursor_pos: int

    @staticmethod
    def from_buffer(buffer: Buffer) -> "BufferInfo":
        return BufferInfo(buffer.text, buffer.cursor_position)


MAX_UNDO_LIST_LEN = 100
UNDO_MERGE_TIMEOUT = 0.5
bindings = KeyBindings()
_auto_editing: bool = False
_previous_text: str = ""
_last_info: BufferInfo = BufferInfo("", 0)
_bracket_stack: list[str] = []
_undo_list: list[BufferInfo] = []
_redo_list: list[BufferInfo] = []
_last_edit_time: float = 0
_last_edit_kind: str | None = None   # "insert" / "delete" / "replace"


def on_text_changed(buffer: Buffer) -> None:
    global _last_info
    if not _auto_editing:
        _redo_list.clear()
        if not _should_merge(buffer):
            _undo_list.append(_last_info)
        while len(_undo_list) > MAX_UNDO_LIST_LEN:
            del _undo_list[0]
        _last_info = BufferInfo.from_buffer(buffer)


def clean_buffer() -> None:
    global _auto_editing, _previous_text, _last_info, _last_edit_time, _last_edit_kind
    _auto_editing = False
    _previous_text = ""
    _last_info = BufferInfo("", 0)
    _bracket_stack.clear()
    _undo_list.clear()
    _redo_list.clear()
    _last_edit_time = 0
    _last_edit_kind = None


def is_cursor_before_right(buffer: Buffer, char) -> bool:
    pos = buffer.cursor_position
    return pos < len(buffer.text) and buffer.text[pos] == char

def should_completion(buffer: Buffer) -> bool:
    pos = buffer.cursor_position
    return pos >= len(buffer.text) or buffer.text[pos].isspace() or buffer.text[pos] in ")]}>\"\'"

@bindings.add('(')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    if buffer.selection_state:
        original_cursor_position = buffer.selection_state.original_cursor_position
        start = min(original_cursor_position, buffer.cursor_position)
        end = max(original_cursor_position, buffer.cursor_position)
        text = buffer.text
        buffer.text = text[:start] + '(' + text[start:end] + ')' + text[end:]
        buffer.cursor_position += 1
        buffer.selection_state = SelectionState(
            original_cursor_position=original_cursor_position + 1,
        )
        buffer.selection_state.shift_mode = True
        return
    if should_completion(buffer):
        _auto_editing = True
        buffer.insert_text('()')
        buffer.cursor_left()
        _bracket_stack.append('(')
        _auto_editing = False
        on_text_changed(buffer)
    else:
        buffer.insert_text('(')

@bindings.add('[')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    if buffer.selection_state:
        original_cursor_position = buffer.selection_state.original_cursor_position
        start = min(original_cursor_position, buffer.cursor_position)
        end = max(original_cursor_position, buffer.cursor_position)
        text = buffer.text
        buffer.text = text[:start] + '[' + text[start:end] + ']' + text[end:]
        buffer.cursor_position += 1
        buffer.selection_state = SelectionState(
            original_cursor_position=original_cursor_position + 1,
        )
        buffer.selection_state.shift_mode = True
        return
    if should_completion(buffer):
        _auto_editing = True
        buffer.insert_text('[]')
        buffer.cursor_left()
        _bracket_stack.append('[')
        _auto_editing = False
        on_text_changed(buffer)
    else:
        buffer.insert_text('[')

@bindings.add('{')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    if buffer.selection_state:
        original_cursor_position = buffer.selection_state.original_cursor_position
        start = min(original_cursor_position, buffer.cursor_position)
        end = max(original_cursor_position, buffer.cursor_position)
        text = buffer.text
        buffer.text = text[:start] + '{' + text[start:end] + '}' + text[end:]
        buffer.cursor_position += 1
        buffer.selection_state = SelectionState(
            original_cursor_position=original_cursor_position + 1,
        )
        buffer.selection_state.shift_mode = True
        return
    if should_completion(buffer):
        _auto_editing = True
        buffer.insert_text('{}')
        buffer.cursor_left()
        _bracket_stack.append('{')
        _auto_editing = False
        on_text_changed(buffer)
    else:
        buffer.insert_text('{')

@bindings.add(')')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    stack = _bracket_stack
    if stack and stack[-1] == '(' and is_cursor_before_right(buffer, ')'):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
    else:
        buffer.insert_text(')')

@bindings.add(']')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    stack = _bracket_stack
    if stack and stack[-1] == '[' and is_cursor_before_right(buffer, ']'):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
    else:
        buffer.insert_text(']')

@bindings.add('}')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    stack = _bracket_stack
    if stack and stack[-1] == '{' and is_cursor_before_right(buffer, '}'):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
    else:
        buffer.insert_text('}')

@bindings.add('"')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    if buffer.selection_state:
        original_cursor_position = buffer.selection_state.original_cursor_position
        start = min(original_cursor_position, buffer.cursor_position)
        end = max(original_cursor_position, buffer.cursor_position)
        text = buffer.text
        buffer.text = text[:start] + '"' + text[start:end] + '"' + text[end:]
        buffer.cursor_position += 1
        buffer.selection_state = SelectionState(
            original_cursor_position=original_cursor_position + 1,
        )
        buffer.selection_state.shift_mode = True
        return
    stack = _bracket_stack
    if stack and stack[-1] == '"' and is_cursor_before_right(buffer, '"'):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
        return
    pos = buffer.cursor_position
    text = buffer.text
    before_ok = pos == 0 or (pos > 0 and (text[pos - 1].isspace()
            or text[pos - 1] in set(r"!@#$%^&*:;,./?|+-=~()[]{}<>_")))
    not_on_quote = pos >= len(text) or text[pos] != '"'
    if should_completion(buffer) and before_ok and not_on_quote:
        _auto_editing = True
        buffer.insert_text('""')
        buffer.cursor_left()
        stack.append('"')
        _auto_editing = False
        on_text_changed(buffer)
    else:
        buffer.insert_text('"')

@bindings.add("'")
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    if buffer.selection_state:
        original_cursor_position = buffer.selection_state.original_cursor_position
        start = min(original_cursor_position, buffer.cursor_position)
        end = max(original_cursor_position, buffer.cursor_position)
        text = buffer.text
        buffer.text = text[:start] + "'" + text[start:end] + "'" + text[end:]
        buffer.cursor_position += 1
        buffer.selection_state = SelectionState(
            original_cursor_position=original_cursor_position + 1,
        )
        buffer.selection_state.shift_mode = True
        return
    stack = _bracket_stack
    if stack and stack[-1] == "'" and is_cursor_before_right(buffer, "'"):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
        return
    if should_completion(buffer):
        _auto_editing = True
        buffer.insert_text("''")
        buffer.cursor_left()
        stack.append("'")
        _auto_editing = False
        on_text_changed(buffer)
    else:
        buffer.insert_text("'")

@bindings.add(Keys.Backspace)
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    pos = buffer.cursor_position
    text = buffer.text

    if buffer.selection_state:
        start = min(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        end = max(buffer.cursor_position, buffer.selection_state.original_cursor_position)
        buffer.text = buffer.text[:start] + buffer.text[end:]
        buffer.cursor_position = start
        buffer.selection_state = None
        _bracket_stack.clear()
        buffer.start_completion()
        return

    if pos > 0 and pos < len(text):
        left = text[pos-1]
        right = text[pos]
        if (left == '(' and right == ')') or \
           (left == '[' and right == ']') or \
           (left == '{' and right == '}') or \
           (left == '"' and right == '"') or \
           (left == "'" and right == "'"):
            stack = _bracket_stack
            _auto_editing = True
            if stack and stack[-1] == left:
                stack.pop()
                buffer.delete()
            buffer.delete_before_cursor()
            _auto_editing = False
            return

    buffer.delete_before_cursor()
    buffer.start_completion()

def on_cursor_position_changed(buffer: Buffer) -> None:
    global _auto_editing, _last_info, _previous_text

    if _auto_editing:
        _previous_text = buffer.text
        return

    _last_info = BufferInfo.from_buffer(buffer)

    if buffer.text != _previous_text:
        _previous_text = buffer.text
        return

    # Any cursor movement without editing will clear the stack
    _bracket_stack.clear()


def _reset_undo_merge() -> None:
    global _last_edit_time, _last_edit_kind
    _last_edit_time = 0.0
    _last_edit_kind = None


def _should_merge(buffer: Buffer) -> bool:
    global _last_edit_time, _last_edit_kind

    old_text = _last_info.text
    new_text = buffer.text
    if len(new_text) > len(old_text):
        kind = "insert"
    elif len(new_text) < len(old_text):
        kind = "delete"
    else:
        kind = "replace"

    now = time.monotonic()
    same_kind = (kind == _last_edit_kind)
    in_time = (now - _last_edit_time) <= UNDO_MERGE_TIMEOUT

    _last_edit_time = now
    _last_edit_kind = kind

    return same_kind and in_time

@bindings.add(Keys.ControlZ)
def _(event: KeyPressEvent) -> None:
    global _auto_editing, _last_info
    _auto_editing = True
    buffer = event.current_buffer
    if _undo_list:
        _redo_list.append(BufferInfo.from_buffer(buffer))
        info = _undo_list.pop()
        buffer.text = info.text
        buffer._set_cursor_position(info.cursor_pos)
    _auto_editing = False
    _last_info = BufferInfo.from_buffer(buffer)
    _reset_undo_merge()

@bindings.add(Keys.ControlY)
def _(event: KeyPressEvent) -> None:
    global _auto_editing, _last_info
    _auto_editing = True
    buffer = event.current_buffer
    if _redo_list:
        _undo_list.append(BufferInfo.from_buffer(buffer))
        info = _redo_list.pop()
        buffer.text = info.text
        buffer._set_cursor_position(info.cursor_pos)
    _auto_editing = False
    _last_info = BufferInfo.from_buffer(buffer)
    _reset_undo_merge()
