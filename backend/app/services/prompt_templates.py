from app.schemas.interview import Difficulty, InterviewMode, Persona, PressureMode, InterviewSessionState


# ---------------------------------------------------------------------------
# Behavioral interviewer preamble (Phase 2.2)
# ---------------------------------------------------------------------------

BEHAVIORAL_PREAMBLE = (
    "You are an experienced HR interviewer conducting a behavioral interview using the STAR method "
    "(Situation, Task, Action, Result). Ask scenario-based questions about past experiences, "
    "teamwork, conflict resolution, leadership, and problem-solving. "
    "Do NOT ask technical or coding questions. "
    "When evaluating answers, assess how well the candidate structures their response: "
    "Did they describe a clear Situation? A specific Task? Concrete Actions? Measurable Results? "
    "Be encouraging but expect real examples, not generic platitudes."
)


# ---------------------------------------------------------------------------
# Persona preambles — injected before every question prompt
# ---------------------------------------------------------------------------

_PERSONA_PREAMBLES: dict[Persona, str] = {
    Persona.SERVICE: (
        "You are a senior interviewer at a large service company (e.g., TCS, Infosys, Wipro). "
        "Your style is structured and process-oriented. You value breadth of knowledge, "
        "familiarity with SDLC, project management, and teamwork. Questions lean toward "
        "conceptual understanding, standard patterns, and real-world project scenarios. "
        "You are professional and methodical."
    ),
    Persona.PRODUCT: (
        "You are a Staff Engineer at a top product company (e.g., Google, Amazon, Meta). "
        "Your style is rigorous and depth-first. You probe for first-principles reasoning, "
        "system design trade-offs, edge cases, algorithmic efficiency, and scalability. "
        "You ask follow-up questions when answers are vague. You do not accept hand-waving. "
        "You are direct and intellectually demanding."
    ),
    Persona.STARTUP: (
        "You are a founding engineer at a fast-moving startup. "
        "Your style is pragmatic and full-stack. You care about getting things shipped correctly "
        "without over-engineering. You value ownership, resourcefulness, cross-functional ability, "
        "and fast iteration. Questions often blend backend, frontend, infra, and product thinking. "
        "You are collaborative but expect candidates to drive conversations."
    ),
}

# ---------------------------------------------------------------------------
# Structured output instructions
# ---------------------------------------------------------------------------

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
  "feedback": "one concise sentence summarising the overall answer quality",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1"],
  "what_went_well": ["specific thing that was done well 1", "specific thing 2"],
  "next_time_try": "one concrete, actionable improvement tip for the candidate"
}
"""

HINT_OUTPUT_INSTRUCTIONS = """
Return only valid JSON with this exact shape:
{
  "hint": "a Socratic guiding question or nudge that points the candidate toward the answer without revealing it"
}
"""


# ---------------------------------------------------------------------------
# Prompt renderers
# ---------------------------------------------------------------------------

def render_question_prompt(state: InterviewSessionState, difficulty: Difficulty) -> str:
    # Use behavioral preamble for behavioral mode; otherwise use persona preamble
    if state.mode == InterviewMode.BEHAVIORAL:
        persona_preamble = BEHAVIORAL_PREAMBLE
    else:
        persona_preamble = _PERSONA_PREAMBLES[state.persona]
    context = _mode_context(state.mode, state.topic, state.resume_text, state.jd_text)
    memory = _render_memory(state)
    pressure_note = (
        "This is a Practice session — be encouraging and educational."
        if state.pressure_mode == PressureMode.PRACTICE
        else "This is a Simulated Real Interview — be rigorous and hold the candidate to a high standard."
    )
    return f"""
{persona_preamble}

Mode: {state.mode.value}
Difficulty: {difficulty.value}
Atmosphere: {pressure_note}
Context:
{context}

Conversation memory:
{memory}

Ask the next single interview question. Avoid repeating prior questions.
{QUESTION_OUTPUT_INSTRUCTIONS}
""".strip()


def render_evaluation_prompt(state: InterviewSessionState, answer: str) -> str:
    memory = _render_memory(state)
    pressure_note = (
        "Apply a coaching lens — highlight growth opportunities warmly."
        if state.pressure_mode == PressureMode.PRACTICE
        else "Apply a strict interview lens — score accurately; do not inflate."
    )
    return f"""
You are InterviewLoop, evaluating a candidate answer.

Mode: {state.mode.value}
Current difficulty: {state.current_difficulty.value}
Scoring guidance: {pressure_note}
Conversation memory:
{memory}

Candidate answer:
{answer}

Score the answer fairly from 0 to 10. Provide specific, actionable feedback.
{EVALUATION_OUTPUT_INSTRUCTIONS}
""".strip()


def render_hint_prompt(state: InterviewSessionState, current_question: str) -> str:
    memory = _render_memory(state)
    persona_preamble = _PERSONA_PREAMBLES[state.persona]
    return f"""
{persona_preamble}

A candidate is struggling with the following interview question and has asked for a hint.
Do NOT give away the answer. Instead, ask a Socratic guiding question or give a nudge
that helps them think toward the answer on their own.

Interview question:
{current_question}

Conversation so far:
{memory}

Provide exactly one short Socratic hint.
{HINT_OUTPUT_INSTRUCTIONS}
""".strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mode_context(mode: InterviewMode, topic: str | None, resume_text: str | None, jd_text: str | None = None) -> str:
    if mode == InterviewMode.TOPIC:
        return f"Focus only on topic: {topic or 'general software engineering'}."
    if mode == InterviewMode.RESUME:
        return f"Ask from this resume content:\n{resume_text or 'No resume content provided.'}"
    if mode == InterviewMode.BEHAVIORAL:
        return "Ask STAR-method behavioral questions about past work experiences and soft skills."
    if mode == InterviewMode.JOB_DESCRIPTION:
        return (
            f"Ask questions aligned with the following job description. "
            f"Weight heavily toward skills, tools, and responsibilities explicitly mentioned in it.\n"
            f"Job Description:\n{jd_text or 'No job description provided.'}"
        )
    return (
        f"Blend topic and resume. Topic: {topic or 'general software engineering'}.\n"
        f"Resume:\n{resume_text or 'No resume content provided.'}"
    )


def _render_memory(state: InterviewSessionState) -> str:
    if not state.turns:
        return "No prior turns."
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in state.turns)
