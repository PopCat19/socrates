# prompt.py
#
# Purpose: Generates Socrates-style clarifying questions from partial prompts
#
# This module:
# - Defines system prompts for question generation and extended reasoning
# - Parses ranked question lists from LLM JSON responses
# - Guards against short or empty prompts before making LLM calls

import json
import re
from dataclasses import dataclass

from shared.llm_client import LLMClient

SOCRATES_SYSTEM = """\
Analyze this partial user prompt and generate 1-3 clarifying questions.
Return ONLY a JSON array — no prose, no markdown fences.
Each question must be ≤3 simple sentences. Rank by priority.
P0 = most critical ambiguity · P1 = important context · P2 = nice to know.

Format: [{"priority":"P0","question":"..."},{"priority":"P1","question":"..."}]"""

EXTENDED_SYSTEM = """\
The user submitted this prompt for extended reasoning.
Think step-by-step: identify unstated assumptions, edge cases,
and the most useful interpretation. Respond in a structured, thorough way."""

MIN_PROMPT_LEN = 10


@dataclass
class Question:
    priority: str
    question: str


def parse_questions(text: str) -> list[Question]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group())
        return [Question(i.get("priority", "P?"), i.get("question", "")) for i in items]
    except json.JSONDecodeError:
        return []


async def get_questions(
    client: LLMClient, prompt: str, model: str
) -> list[Question]:
    if len(prompt.strip()) < MIN_PROMPT_LEN:
        return []
    messages = [
        {"role": "system", "content": SOCRATES_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    try:
        text = await client.complete(messages, model)
        return parse_questions(text)
    except Exception:
        return []
