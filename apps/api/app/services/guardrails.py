from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    status: str
    category: str | None = None
    message: str | None = None
    safe_redirect: str | None = None

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"


MISUSE_PATTERNS: dict[str, tuple[str, ...]] = {
    "credential_theft": (
        "steal password",
        "phish",
        "credential harvester",
        "session cookie",
        "bypass login",
        "dump tokens",
    ),
    "malware_or_intrusion": (
        "write malware",
        "ransomware",
        "keylogger",
        "reverse shell",
        "exploit a server",
        "evade antivirus",
        "bypass detection",
    ),
    "weapons_or_harm": (
        "build a bomb",
        "make explosives",
        "poison someone",
        "hurt someone",
        "kill someone",
    ),
    "deception_or_abuse": (
        "fake identity",
        "impersonate",
        "forge documents",
        "blackmail",
        "harass",
    ),
}


SAFE_REDIRECTS = {
    "credential_theft": (
        "I can help turn this into a defensive security prompt for auditing access, "
        "rotating credentials, or detecting phishing safely."
    ),
    "malware_or_intrusion": (
        "I can help reframe this as a defensive security review, incident response plan, "
        "or vulnerability reproduction in an authorized lab."
    ),
    "weapons_or_harm": (
        "I can help with safety planning, emergency response, prevention, or harmless "
        "educational context instead."
    ),
    "deception_or_abuse": (
        "I can help rewrite this toward transparent communication, policy-compliant outreach, "
        "or abuse-prevention guidance."
    ),
}


def evaluate_guardrails(raw_input: str) -> GuardrailResult:
    lowered = raw_input.lower()
    for category, patterns in MISUSE_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            return GuardrailResult(
                status="blocked",
                category=category,
                message=(
                    "This request crosses PromptPilot's safety rules, so I cannot "
                    "help optimize it as written."
                ),
                safe_redirect=SAFE_REDIRECTS[category],
            )
    return GuardrailResult(status="passed")
