# main.py
#
# Purpose: Textual TUI for the Socrates prompt assistant
#
# This module:
# - Renders a split-pane layout with prompt input and question panel
# - Debounces LLM question generation on input changes (~400ms)
# - Streams extended reasoning output on Ctrl+Enter

import asyncio
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static, TextArea

if TYPE_CHECKING:
    from textual.timer import Timer

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.llm_client import LLMClient
from shared.prompt import EXTENDED_SYSTEM, Question, get_questions

DEFAULT_MODEL = os.getenv("LLM_MODEL", "")
PRIORITY_COLORS: dict[str, str] = {"P0": "red", "P1": "yellow", "P2": "green"}


class QuestionsPanel(Static):
    DEFAULT_CSS = "QuestionsPanel { border: solid $accent; width: 40%; padding: 1; }"

    def show(self, questions: list[Question]) -> None:
        if not questions:
            self.update("[dim]Waiting for input…[/dim]")
            return
        lines = [
            f"[bold {PRIORITY_COLORS.get(q.priority, 'white')}]{q.priority}[/] {q.question}"
            for q in questions
        ]
        self.update("\n\n".join(lines))


class ResponsePanel(Static):
    DEFAULT_CSS = "ResponsePanel { border: solid $panel; height: 1fr; padding: 1; }"


class SocratesApp(App):
    TITLE = "Socrates"
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+enter", "submit_extended", "Submit (extended)"),
    ]
    CSS = """
    Screen { layout: vertical; }
    #top { height: 3; }
    #body { layout: horizontal; height: 1fr; }
    #left { layout: vertical; width: 1fr; }
    TextArea { height: 8; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.llm = LLMClient()
        self.model = DEFAULT_MODEL
        self._debounce: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top"):
            yield Input(placeholder="Model name", id="model-input", value=self.model)
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield TextArea(id="prompt")
                yield ResponsePanel("[dim]Response appears here after Ctrl+Enter[/dim]", id="response")
            yield QuestionsPanel("[dim]Waiting for input…[/dim]", id="questions")
        yield Footer()

    async def on_mount(self) -> None:
        models = await self.llm.list_models()
        inp = self.query_one("#model-input", Input)
        if models:
            self.model = models[0]
            inp.value = self.model
            inp.placeholder = f"Model ({', '.join(models[:3])}…)"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "model-input" and event.value.strip():
            self.model = event.value.strip()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._debounce:
            self._debounce.stop()
        self._debounce = self.set_timer(0.4, lambda: self._fetch_questions(event.text_area.text))

    async def _fetch_questions(self, prompt: str) -> None:
        questions = await get_questions(self.llm, prompt, self.model)
        self.query_one(QuestionsPanel).show(questions)

    async def action_submit_extended(self) -> None:
        prompt = self.query_one("#prompt", TextArea).text.strip()
        if not prompt:
            return

        panel = self.query_one("#response", ResponsePanel)
        panel.update("[dim]Reasoning…[/dim]")

        messages = [
            {"role": "system", "content": EXTENDED_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        text = ""
        async for token in self.llm.stream_complete(messages, self.model):
            text += token
            panel.update(text)


if __name__ == "__main__":
    SocratesApp().run()
