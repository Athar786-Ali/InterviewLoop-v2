"""Speech analytics service.

Lightweight heuristic analysis of candidate answer text.
No LLM or external service required — pure string processing.

Detects:
  - Filler word count (um, uh, like, you know, basically, etc.)
  - Words-per-minute (when elapsed_seconds is provided by the frontend)

Results are appended to InterviewEvaluation so the end-of-interview summary
can surface coaching messages like "You used filler words 8 times — try pausing
instead of saying 'um'."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Common English filler words to track
_FILLERS = frozenset(
    [
        "um", "uh", "umm", "uhh",
        "like", "literally", "basically", "actually", "obviously",
        "you know", "i mean", "kind of", "sort of", "right",
        "so yeah", "you see", "honestly", "frankly",
    ]
)

# Pre-compile a regex that matches any filler as a whole phrase
_FILLER_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(f) for f in sorted(_FILLERS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


@dataclass
class SpeechMetrics:
    filler_count: int
    words_per_minute: float | None


class SpeechAnalyticsService:
    """Stateless heuristic analyser — call via class method, no instantiation needed."""

    @staticmethod
    def analyse(text: str, elapsed_seconds: float | None = None) -> SpeechMetrics:
        """Return filler count and optional WPM for the given answer text.

        Args:
            text:             The raw answer text (typed or transcribed).
            elapsed_seconds:  Time from question display to answer submission, sent
                              by the frontend. None when unavailable (typed input
                              without timestamp).
        """
        filler_count = len(_FILLER_PATTERN.findall(text))

        words_per_minute: float | None = None
        if elapsed_seconds and elapsed_seconds > 0:
            word_count = len(text.split())
            minutes = elapsed_seconds / 60.0
            words_per_minute = round(word_count / minutes, 1)

        return SpeechMetrics(filler_count=filler_count, words_per_minute=words_per_minute)
