from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.selection import SelectionState
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.bindings.auto_suggest import load_auto_suggest_bindings

bindings = KeyBindings()
_auto_editing = False

def buffer_get_stack(buffer) -> list[str]:
    if not hasattr(buffer, '_bracket_stack'):
        buffer._bracket_stack = []
    return buffer._bracket_stack

def is_cursor_before_right(buffer, char) -> bool:
    pos = buffer.cursor_position
    return pos < len(buffer.text) and buffer.text[pos] == char

def should_completion(buffer) -> bool:
    pos = buffer.cursor_position
    return pos >= len(buffer.text) or buffer.text[pos].isspace() or buffer.text[pos] in ")]}>"

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
        buffer_get_stack(buffer).append('(')
        _auto_editing = False
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
        buffer_get_stack(buffer).append('[')
        _auto_editing = False
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
        buffer_get_stack(buffer).append('{')
        _auto_editing = False
    else:
        buffer.insert_text('{')

@bindings.add(')')
def _(event: KeyPressEvent) -> None:
    global _auto_editing
    buffer = event.current_buffer
    stack = buffer_get_stack(buffer)
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
    stack = buffer_get_stack(buffer)
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
    stack = buffer_get_stack(buffer)
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
    stack = buffer_get_stack(buffer)
    if stack and stack[-1] == '"' and is_cursor_before_right(buffer, '"'):
        _auto_editing = True
        buffer.cursor_right()
        stack.pop()
        _auto_editing = False
        return
    if should_completion(buffer) and (
        len(buffer.text) > 0
        and buffer.cursor_position > 0
        and (
            buffer.text[buffer.cursor_position - 1] in r"!@#$%^&*:;,./?|\+-=~()[]{}<>_"
            or buffer.text[buffer.cursor_position - 1].isspace()
        )
        or buffer.cursor_position == 0
    ):
        _auto_editing = True
        buffer.insert_text('""')
        buffer.cursor_left()
        stack.append('"')
        _auto_editing = False
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
    stack = buffer_get_stack(buffer)
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
        _auto_editing = True
        buffer.text = buffer.text[:start] + buffer.text[end:]
        buffer.cursor_position = start
        buffer.selection_state = None
        buffer_get_stack(buffer).clear()
        _auto_editing = False
        return

    if pos > 0 and pos < len(text):
        left = text[pos-1]
        right = text[pos]
        if (left == '(' and right == ')') or \
           (left == '[' and right == ']') or \
           (left == '{' and right == '}') or \
           (left == '"' and right == '"') or \
           (left == "'" and right == "'"):
            stack = buffer_get_stack(buffer)
            _auto_editing = True
            if stack and stack[-1] == left:
                stack.pop()
                buffer.delete()
            buffer.delete_before_cursor()
            _auto_editing = False
            return

    buffer.delete_before_cursor()

def on_cursor_position_changed(buffer) -> None:
    global _auto_editing
    if _auto_editing:
        return

    if not hasattr(buffer, '_previous_text'):
        buffer._previous_text = buffer.text
        return

    if buffer.text != buffer._previous_text:
        buffer._previous_text = buffer.text
        return

    # Any cursor movement without editing will clear the stack
    buffer_get_stack(buffer).clear()
