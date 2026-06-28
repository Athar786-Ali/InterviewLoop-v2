from app.core.config import settings
from app.schemas.interview import Difficulty


class AdaptiveDifficultyService:
    def next_difficulty(self, current: Difficulty, scores: list[float]) -> Difficulty:
        if not scores:
            return current

        window = scores[-settings.adaptive_score_window :]
        average_score = sum(window) / len(window)

        if average_score >= 8:
            return self._increase(current)
        if average_score <= 4:
            return self._decrease(current)
        return current

    def _increase(self, current: Difficulty) -> Difficulty:
        if current == Difficulty.EASY:
            return Difficulty.MEDIUM
        if current == Difficulty.MEDIUM:
            return Difficulty.HARD
        return Difficulty.HARD

    def _decrease(self, current: Difficulty) -> Difficulty:
        if current == Difficulty.HARD:
            return Difficulty.MEDIUM
        if current == Difficulty.MEDIUM:
            return Difficulty.EASY
        return Difficulty.EASY
