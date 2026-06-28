from app.schemas.interview import Difficulty, InterviewMode, InterviewSessionState


QUESTION_OUTPUT_INSTRUCTIONS = """
Return only valid JSON with this exact shape:
{
  "question": "one interview question",
  "topic": "short topic label",
  "difficulty": "easy|medium|hard",
  "expected_signals": ["signal 1", "signal 2"]
}
"""

EVALUATION_OUTPUT_INSTRUCTIONS = """
Return only valid JSON with this exact shape:
{
  "score": 0-10,
  "feedback": "specific concise feedback",
  "strengths": ["strength 1"],
  "weaknesses": ["weakness 1"]
}
"""


def render_question_prompt(state: InterviewSessionState, difficulty: Difficulty) -> str:
    context = _mode_context(state.mode, state.topic, state.resume_text)
    memory = _render_memory(state)
    return f"""
You are InterviewLoop-v2, a rigorous AI mock interviewer.

Mode: {state.mode.value}
Difficulty: {difficulty.value}
Context:
{context}

Conversation memory:
{memory}

Ask the next single interview question. Avoid repeating prior questions.
{QUESTION_OUTPUT_INSTRUCTIONS}
""".strip()


def render_evaluation_prompt(state: InterviewSessionState, answer: str) -> str:
    memory = _render_memory(state)
    return f"""
You are InterviewLoop-v2, evaluating a candidate answer.

Mode: {state.mode.value}
Current difficulty: {state.current_difficulty.value}
Conversation memory:
{memory}

Candidate answer:
{answer}

Score the answer fairly from 0 to 10.
{EVALUATION_OUTPUT_INSTRUCTIONS}
""".strip()


def _mode_context(mode: InterviewMode, topic: str | None, resume_text: str | None) -> str:
    if mode == InterviewMode.TOPIC:
        return f"Focus only on topic: {topic or 'general software engineering'}."
    if mode == InterviewMode.RESUME:
        return f"Ask from this resume content:\n{resume_text or 'No resume content provided.'}"
    return f"Blend topic and resume. Topic: {topic or 'general software engineering'}.\nResume:\n{resume_text or 'No resume content provided.'}"


def _render_memory(state: InterviewSessionState) -> str:
    if not state.turns:
        return "No prior turns."
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in state.turns)
