from __future__ import annotations

import os
import sys
import termios
import tty
from dataclasses import dataclass, field
from typing import TextIO

import typer


BRACKETED_PASTE_START = "\x1b[200~"
BRACKETED_PASTE_END = "\x1b[201~"
BACKSPACE_TOKENS = {"\b", "\x7f"}
NEWLINE_TOKENS = {"\r", "\n"}


@dataclass
class _InputState:
    characters: list[str] = field(default_factory=list)
    in_paste: bool = False
    submitted: bool = False


class InputSelector:
    def __init__(
        self,
        prompt: str,
        hide_input: bool = False,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        self.prompt = prompt
        self.hide_input = hide_input
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout

    def ask(self) -> str:
        if not self._supports_interactive_tty():
            return typer.prompt(self.prompt, hide_input=self.hide_input)

        return self._ask_from_tty()

    @staticmethod
    def consume_tokens(tokens: list[str]) -> tuple[str, bool]:
        state = _InputState()
        for token in tokens:
            InputSelector._consume_token(state, token)
            if state.submitted:
                break
        return "".join(state.characters), state.submitted

    @staticmethod
    def _consume_token(state: _InputState, token: str) -> str | None:
        if token == BRACKETED_PASTE_START:
            state.in_paste = True
            return None

        if token == BRACKETED_PASTE_END:
            state.in_paste = False
            return None

        if token in BACKSPACE_TOKENS:
            if state.characters:
                state.characters.pop()
                return "backspace"
            return None

        if token in NEWLINE_TOKENS:
            if state.in_paste:
                return None

            state.submitted = True
            return "submit"

        if token.startswith("\x1b"):
            return None

        state.characters.append(token)
        return "append"

    def _supports_interactive_tty(self) -> bool:
        return (
            os.name == "posix"
            and hasattr(self.input_stream, "isatty")
            and hasattr(self.output_stream, "isatty")
            and self.input_stream.isatty()
            and self.output_stream.isatty()
            and hasattr(self.input_stream, "fileno")
        )

    def _ask_from_tty(self) -> str:
        file_descriptor = self.input_stream.fileno()
        previous_settings = termios.tcgetattr(file_descriptor)
        state = _InputState()

        self.output_stream.write(f"{self.prompt}: ")
        self.output_stream.flush()

        try:
            tty.setraw(file_descriptor)
            self._enable_bracketed_paste()

            while not state.submitted:
                token = self._read_token()
                if token == "\x03":
                    raise typer.Abort()

                action = self._consume_token(state, token)
                self._render_action(action, token)

            self.output_stream.write("\n")
            self.output_stream.flush()
            return "".join(state.characters)
        finally:
            self._disable_bracketed_paste()
            termios.tcsetattr(
                file_descriptor, termios.TCSADRAIN, previous_settings)

    def _read_token(self) -> str:
        character = self.input_stream.read(1)
        if character != "\x1b":
            return character

        sequence = [character]
        while True:
            next_character = self.input_stream.read(1)
            if not next_character:
                break

            sequence.append(next_character)
            if next_character.isalpha() or next_character == "~":
                break

        return "".join(sequence)

    def _render_action(self, action: str | None, token: str) -> None:
        if action != "append" and action != "backspace":
            return

        if self.hide_input:
            return

        if action == "append":
            self.output_stream.write(token)
        else:
            self.output_stream.write("\b \b")

        self.output_stream.flush()

    def _enable_bracketed_paste(self) -> None:
        self.output_stream.write("\x1b[?2004h")
        self.output_stream.flush()

    def _disable_bracketed_paste(self) -> None:
        self.output_stream.write("\x1b[?2004l")
        self.output_stream.flush()


def prompt(text: str, hide_input: bool = False) -> str:
    return InputSelector(text, hide_input=hide_input).ask()
