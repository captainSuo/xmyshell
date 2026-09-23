from prompt_toolkit.buffer import _only_one_at_a_time, CompletionState
from prompt_toolkit.application import get_app


def _new_text_and_position(self: CompletionState):

    def new_text_and_position() -> tuple[str, int]:
        """Injected by XmyShell."""
        if self.complete_index is None:
            return self.original_document.text, self.original_document.cursor_position
        else:
            original_text_before_cursor = self.original_document.text_before_cursor
            original_text_after_cursor = self.original_document.text_after_cursor

            c = self.completions[self.complete_index]
            c.text = c.text.rstrip()  # injected
            if c.start_position == 0:
                before = original_text_before_cursor
            else:
                before = original_text_before_cursor[: c.start_position]

            new_text = before + c.text + original_text_after_cursor
            new_cursor_position = len(before) + len(c.text)
            return new_text, new_cursor_position
    return new_text_and_position


def inject() -> None:
    buffer = get_app().current_buffer

    async_completer = buffer._create_completer_coroutine()

    @_only_one_at_a_time
    async def _async_completer(*args, **kwargs) -> None:
        """Injected by XmyShell."""
        await async_completer(*args, **kwargs)
        if buffer.complete_state:
            buffer.complete_state.new_text_and_position = \
                _new_text_and_position(buffer.complete_state)
            buffer.complete_state.go_to_index(0)

    buffer._async_completer = _async_completer
