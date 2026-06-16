from app.schemas import ClarifyingQuestion, ClassificationResponse


DOMAIN_QUESTIONS = {
    "car_home_troubleshooting": [
        (
            "symptoms",
            "What exact symptoms do you see, hear, smell, or notice?",
            "The prompt needs observable details before suggesting diagnostics.",
        ),
        (
            "recent_changes",
            "What changed recently, and what have you already tried?",
            "Recent changes and attempted fixes narrow the likely causes.",
        ),
    ],
    "software_project_building": [
        (
            "tech_stack",
            "What stack, framework, language, or tool versions are involved?",
            "Technical prompts work better when the environment is explicit.",
        ),
        (
            "failure_mode",
            "What error message, unexpected behavior, or goal should the AI focus on?",
            "The model needs a concrete target for debugging or implementation.",
        ),
    ],
    "writing_business_communication": [
        (
            "audience",
            "Who is the audience, and what outcome should the message achieve?",
            "Audience and desired outcome shape tone, structure, and wording.",
        ),
        (
            "constraints",
            "Are there details, sensitivities, or phrases that must be included or avoided?",
            "Communication prompts need context boundaries to avoid awkward drafts.",
        ),
    ],
    "learning_research": [
        (
            "current_level",
            "What do you already know, and what level should the explanation target?",
            "The prompt should match the user's starting point.",
        ),
        (
            "output_goal",
            "Do you want a summary, study plan, comparison, examples, or sources?",
            "The output format determines how the research prompt should be framed.",
        ),
    ],
    "general_problem_solving": [
        (
            "goal",
            "What would a useful final answer help you decide or do?",
            "The prompt needs a clear success condition.",
        ),
        (
            "context",
            "What context, constraints, or failed attempts should the AI know?",
            "Context and constraints prevent generic answers.",
        ),
    ],
}


def generate_questions(
    problem: str,
    classification: ClassificationResponse,
) -> list[ClarifyingQuestion]:
    del problem
    seeds = DOMAIN_QUESTIONS.get(
        classification.domain,
        DOMAIN_QUESTIONS["general_problem_solving"],
    )

    questions = [
        ClarifyingQuestion(id=question_id, question=question, reason=reason)
        for question_id, question, reason in seeds
    ]

    if classification.risk_level in {"medium", "high"}:
        questions.append(
            ClarifyingQuestion(
                id="safety_boundary",
                question="Are there safety, legal, financial, or professional boundaries the answer must respect?",
                reason="Higher-risk prompts should make boundaries explicit.",
                required=classification.risk_level == "high",
            )
        )

    return questions
