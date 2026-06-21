from typing import Any

from app.models import ProblemSession, PromptVariant
from app.schemas import (
    AnswerItem,
    ClassificationResponse,
    ClarifyingQuestion,
    PromptEngineRunResponse,
    PromptSettings,
    PromptVariantResponse,
    RefinementMode,
)
from app.services.classifier import classify_problem
from app.services.prompt_engine import run_prompt_engine
from app.services.prompt_scorer import score_prompt_variants
from app.services.question_generator import generate_questions

try:
    import dspy
except Exception:  # pragma: no cover - DSPy is optional until optimization begins.
    dspy = None


if dspy is not None:
    _DspyModule = dspy.Module
else:

    class _DspyModule:
        pass


DSPY_MODULE_CONTRACTS = {
    "classification": "ClassificationResponse",
    "clarification": "list[ClarifyingQuestion]",
    "refinement_pipeline": "PromptEngineRunResponse",
    "scoring": "list[PromptVariantResponse]",
}


class SchemaStableClassificationModule(_DspyModule):
    def __init__(self) -> None:
        if dspy is not None:
            super().__init__()

    def forward(self, raw_input: str) -> ClassificationResponse:
        return ClassificationResponse.model_validate(classify_problem(raw_input).model_dump())


class SchemaStableClarificationModule(_DspyModule):
    def __init__(self) -> None:
        if dspy is not None:
            super().__init__()

    def forward(
        self,
        raw_input: str,
        classification: ClassificationResponse,
        profile_traits: list[dict[str, Any]] | None = None,
    ) -> list[ClarifyingQuestion]:
        return [
            ClarifyingQuestion.model_validate(question.model_dump())
            for question in generate_questions(
                raw_input,
                classification,
                profile_traits=profile_traits,
            )
        ]


class SchemaStableRefinementModule(_DspyModule):
    def __init__(self) -> None:
        if dspy is not None:
            super().__init__()

    def forward(
        self,
        session: ProblemSession,
        settings: PromptSettings,
        answers: list[AnswerItem] | None = None,
        mode: RefinementMode = "refinement",
    ) -> PromptEngineRunResponse:
        return PromptEngineRunResponse.model_validate(
            run_prompt_engine(
                session,
                settings=settings,
                answers=answers,
                mode=mode,
            ).model_dump()
        )


class SchemaStableScoringModule(_DspyModule):
    def __init__(self) -> None:
        if dspy is not None:
            super().__init__()

    def forward(
        self,
        problem: str,
        prompts: list[PromptVariant],
        settings: PromptSettings,
        classification: ClassificationResponse | None = None,
    ) -> list[PromptVariantResponse]:
        scored = score_prompt_variants(
            problem=problem,
            prompts=prompts,
            settings=settings,
            classification=classification,
        )
        return [
            PromptVariantResponse.model_validate(prompt)
            for prompt in scored
        ]


def dspy_contract_summary() -> dict[str, Any]:
    return {
        "module_version": "phase15-schema-stable-dspy-v1",
        "dspy_available": dspy is not None,
        "contracts": DSPY_MODULE_CONTRACTS,
        "guardrails": [
            "DSPy modules must return existing Pydantic schemas.",
            "Optimizer traces and intermediate scores are not UI-facing outputs.",
            "Pipeline guardrails, profile settings, and retrieval rules remain outside optimizer control.",
        ],
    }
