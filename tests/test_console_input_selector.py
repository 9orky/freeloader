from freeloader.shared.console.input_selector import (
    BRACKETED_PASTE_END,
    BRACKETED_PASTE_START,
    InputSelector,
)


def test_input_selector_ignores_newlines_inside_bracketed_paste() -> None:
    value, submitted = InputSelector.consume_tokens(
        [
            BRACKETED_PASTE_START,
            "{",
            "\n",
            '"token":',
            "\n",
            '"secret"',
            "\n",
            "}",
            BRACKETED_PASTE_END,
            "\n",
        ]
    )

    assert submitted is True
    assert value == '{"token":"secret"}'


def test_input_selector_submits_on_newline_outside_paste() -> None:
    value, submitted = InputSelector.consume_tokens(["a", "b", "c", "\n", "d"])

    assert submitted is True
    assert value == "abc"


def test_input_selector_backspace_removes_previous_character() -> None:
    value, submitted = InputSelector.consume_tokens(
        ["a", "b", "\x7f", "c", "\n"])

    assert submitted is True
    assert value == "ac"
