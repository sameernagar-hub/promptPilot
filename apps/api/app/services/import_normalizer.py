import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


NORMALIZER_VERSION = "chat_import_normalizer_v1"

ROLE_ALIASES = {
    "ai": "assistant",
    "assistant": "assistant",
    "bot": "assistant",
    "chatgpt": "assistant",
    "claude": "assistant",
    "codex": "assistant",
    "human": "user",
    "me": "user",
    "model": "assistant",
    "system": "system",
    "tool": "tool",
    "user": "user",
}

REDACTION_PATTERNS = [
    (
        "secret",
        re.compile(
            r"(?i)\b(?:api[_\-\s]?key|access[_\-\s]?token|token|secret|password)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=\-]{8,}['\"]?"
        ),
    ),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]{16,}\b")),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "phone",
        re.compile(
            r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)"
        ),
    ),
]


@dataclass(frozen=True)
class NormalizedMessage:
    role: str
    message_text: str
    redacted_text: str | None
    position: int
    message_timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedConversation:
    platform: str
    title: str | None
    external_conversation_id: str | None
    messages: list[NormalizedMessage]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedImport:
    platform: str
    source_type: str
    title: str | None
    redaction_status: str
    conversations: list[NormalizedConversation]
    metadata: dict[str, Any]


def normalize_import(
    *,
    platform: str,
    source_type: str,
    title: str | None,
    raw_text: str,
) -> NormalizedImport:
    parsed_conversations, input_format = _parse_json_import(raw_text, platform, title)
    if not parsed_conversations:
        parsed_conversations = [
            NormalizedConversation(
                platform=platform,
                title=title or "Pasted transcript",
                external_conversation_id=None,
                messages=_parse_transcript(raw_text),
                metadata={"input_format": "transcript"},
            )
        ]
        input_format = "transcript"

    redaction_types: set[str] = set()
    redaction_count = 0
    conversations: list[NormalizedConversation] = []
    for conversation in parsed_conversations:
        messages: list[NormalizedMessage] = []
        for position, message in enumerate(conversation.messages):
            redacted, replacements = redact_text(message.message_text)
            redaction_types.update(replacements)
            redaction_count += len(replacements)
            messages.append(
                NormalizedMessage(
                    role=message.role,
                    message_text=message.message_text,
                    redacted_text=redacted if redacted != message.message_text else None,
                    position=position,
                    message_timestamp=message.message_timestamp,
                    metadata={
                        **message.metadata,
                        "redaction_types": sorted(replacements),
                    },
                )
            )

        if messages:
            conversations.append(
                NormalizedConversation(
                    platform=conversation.platform,
                    title=conversation.title or title or "Imported conversation",
                    external_conversation_id=conversation.external_conversation_id,
                    messages=messages,
                    metadata=conversation.metadata,
                )
            )

    if not conversations:
        raise ValueError("Import did not contain any readable messages")

    return NormalizedImport(
        platform=platform,
        source_type=source_type,
        title=title,
        redaction_status="redacted" if redaction_count else "clean",
        conversations=conversations,
        metadata={
            "normalizer_version": NORMALIZER_VERSION,
            "input_format": input_format,
            "redaction_count": redaction_count,
            "redaction_types": sorted(redaction_types),
            "message_count": sum(len(conversation.messages) for conversation in conversations),
        },
    )


def redact_text(text: str) -> tuple[str, set[str]]:
    redacted = text
    replacement_types: set[str] = set()

    for kind, pattern in REDACTION_PATTERNS:
        def replace(match: re.Match[str]) -> str:
            replacement_types.add(kind)
            return f"[redacted:{kind}]"

        redacted = pattern.sub(replace, redacted)

    return redacted, replacement_types


def _parse_json_import(
    raw_text: str,
    platform: str,
    title: str | None,
) -> tuple[list[NormalizedConversation], str | None]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return [], None

    conversations = _conversations_from_json(payload, platform, title)
    return conversations, "json"


def _conversations_from_json(
    payload: Any,
    platform: str,
    fallback_title: str | None,
) -> list[NormalizedConversation]:
    if isinstance(payload, dict):
        if isinstance(payload.get("conversations"), list):
            conversations: list[NormalizedConversation] = []
            for item in payload["conversations"]:
                conversations.extend(_conversations_from_json(item, platform, fallback_title))
            return conversations

        if isinstance(payload.get("mapping"), dict):
            messages = _messages_from_chatgpt_mapping(payload["mapping"])
            return _conversation_list(payload, platform, fallback_title, messages, "chatgpt_mapping")

        for message_key in ("messages", "chat_messages", "items"):
            if isinstance(payload.get(message_key), list):
                messages = _messages_from_list(payload[message_key])
                return _conversation_list(payload, platform, fallback_title, messages, message_key)

        message = _message_from_dict(payload, 0)
        return _conversation_list(payload, platform, fallback_title, [message] if message else [], "single_message")

    if isinstance(payload, list):
        if all(isinstance(item, dict) and "mapping" in item for item in payload):
            conversations: list[NormalizedConversation] = []
            for item in payload:
                conversations.extend(_conversations_from_json(item, platform, fallback_title))
            return conversations

        if all(isinstance(item, dict) and _has_message_shape(item) for item in payload):
            return [
                NormalizedConversation(
                    platform=platform,
                    title=fallback_title or "Imported conversation",
                    external_conversation_id=None,
                    messages=_messages_from_list(payload),
                    metadata={"adapter": "message_list"},
                )
            ]

        conversations = []
        for item in payload:
            conversations.extend(_conversations_from_json(item, platform, fallback_title))
        return conversations

    return []


def _conversation_list(
    payload: dict[str, Any],
    platform: str,
    fallback_title: str | None,
    messages: list[NormalizedMessage],
    adapter: str,
) -> list[NormalizedConversation]:
    if not messages:
        return []

    return [
        NormalizedConversation(
            platform=str(payload.get("platform") or platform),
            title=str(payload.get("title") or payload.get("name") or fallback_title or "Imported conversation"),
            external_conversation_id=_optional_str(
                payload.get("id")
                or payload.get("conversation_id")
                or payload.get("external_conversation_id")
            ),
            messages=messages,
            metadata={"adapter": adapter},
        )
    ]


def _messages_from_list(items: list[Any]) -> list[NormalizedMessage]:
    messages: list[NormalizedMessage] = []
    for position, item in enumerate(items):
        if not isinstance(item, dict):
            text = _stringify_content(item)
            if text:
                messages.append(
                    NormalizedMessage(
                        role="user" if not messages else "assistant",
                        message_text=text,
                        redacted_text=None,
                        position=position,
                    )
                )
            continue

        message = _message_from_dict(item, position)
        if message:
            messages.append(message)
    return messages


def _messages_from_chatgpt_mapping(mapping: dict[str, Any]) -> list[NormalizedMessage]:
    ordered_nodes = sorted(
        mapping.values(),
        key=lambda node: (
            _timestamp_sort_key(_nested_get(node, ["message", "create_time"])),
            str(_nested_get(node, ["id"]) or ""),
        ),
    )
    messages: list[NormalizedMessage] = []
    for position, node in enumerate(ordered_nodes):
        if not isinstance(node, dict):
            continue
        message_payload = node.get("message")
        if not isinstance(message_payload, dict):
            continue
        message = _message_from_dict(message_payload, position)
        if message:
            messages.append(message)
    return messages


def _message_from_dict(payload: dict[str, Any], position: int) -> NormalizedMessage | None:
    role = _normalize_role(
        payload.get("role")
        or payload.get("sender")
        or payload.get("speaker")
        or payload.get("from")
        or _nested_get(payload, ["author", "role"])
    )
    text = _stringify_content(
        payload.get("content")
        or payload.get("text")
        or payload.get("message")
        or payload.get("body")
        or payload.get("value")
    )
    if not text:
        return None

    return NormalizedMessage(
        role=role,
        message_text=text,
        redacted_text=None,
        position=position,
        message_timestamp=_parse_timestamp(
            payload.get("message_timestamp")
            or payload.get("created_at")
            or payload.get("timestamp")
            or payload.get("create_time")
        ),
        metadata={"raw_role": role},
    )


def _parse_transcript(raw_text: str) -> list[NormalizedMessage]:
    messages: list[NormalizedMessage] = []
    current_role: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_role, current_lines
        text = "\n".join(current_lines).strip()
        if current_role and text:
            messages.append(
                NormalizedMessage(
                    role=current_role,
                    message_text=text,
                    redacted_text=None,
                    position=len(messages),
                    metadata={"adapter": "transcript"},
                )
            )
        current_role = None
        current_lines = []

    for line in raw_text.splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9 _-]{0,30})\s*:\s?(.*)$", line)
        if match:
            role = _normalize_role(match.group(1))
            if role in {"user", "assistant", "system", "tool"}:
                flush()
                current_role = role
                current_lines = [match.group(2)]
                continue
        if current_role is None and line.strip():
            current_role = "user"
        current_lines.append(line)
    flush()

    if messages:
        return messages

    cleaned = raw_text.strip()
    return [
        NormalizedMessage(
            role="user",
            message_text=cleaned,
            redacted_text=None,
            position=0,
            metadata={"adapter": "plain_text"},
        )
    ] if cleaned else []


def _normalize_role(value: Any) -> str:
    label = str(value or "user").strip().lower()
    return ROLE_ALIASES.get(label, "user")


def _has_message_shape(item: dict[str, Any]) -> bool:
    return any(key in item for key in ("role", "sender", "speaker", "content", "text", "message"))


def _stringify_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(filter(None, (_stringify_content(item) for item in value))).strip()
    if isinstance(value, dict):
        for key in ("text", "content", "message", "body", "value"):
            text = _stringify_content(value.get(key))
            if text:
                return text
        if isinstance(value.get("parts"), list):
            return _stringify_content(value["parts"])
    return str(value).strip()


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, UTC)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            normalized = stripped.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _timestamp_sort_key(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    timestamp = _parse_timestamp(value)
    return timestamp.timestamp() if timestamp else 0.0


def _nested_get(payload: Any, path: list[str]) -> Any:
    value = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
