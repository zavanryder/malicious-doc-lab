"""Attack/format compatibility matrix and helpers."""

from collections.abc import Mapping

IMAGE_FORMATS = {"image", "png", "jpg", "jpeg"}
TEXT_FORMATS = {"pdf", "docx", "html", "md", "txt", "csv", "xlsx", "pptx", "eml"}

ATTACK_FORMAT_COVERAGE: dict[str, dict[str, set[str]]] = {
    "hidden_text": {
        "supported": {"pdf", "docx", "html", "md", "txt"},
        "degraded": {"csv", "xlsx", "pptx", "eml"} | IMAGE_FORMATS,
    },
    "white_on_white": {
        "supported": {"pdf", "docx", "html"} | IMAGE_FORMATS,
        "degraded": {"md", "txt"},
    },
    "metadata": {
        "supported": {"pdf", "docx", "html", "eml", "xlsx", "pptx"},
        "degraded": {"md"},
    },
    "retrieval_poison": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "ocr_bait": {
        "supported": {"pdf", "html"} | IMAGE_FORMATS,
        "degraded": set(),
    },
    "off_page": {
        "supported": {"pdf", "html", "pptx"},
        "degraded": {"docx"},
    },
    "chunk_split": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "summary_steer": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "delayed_trigger": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "tool_routing": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "encoding_obfuscation": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "typoglycemia": {
        "supported": set(TEXT_FORMATS),
        "degraded": set(IMAGE_FORMATS),
    },
    "markdown_exfil": {
        "supported": {"html", "md", "eml", "txt"},
        "degraded": {"pdf", "docx"},
    },
    "visual_scaling_injection": {
        "supported": {"pdf"} | IMAGE_FORMATS,
        "degraded": set(),
    },
}


def assess_attack_format(attack_name: str, fmt: str) -> tuple[bool, bool, str]:
    """Return (allowed, degraded, message) for an attack/format pair."""
    coverage: Mapping[str, set[str]] | None = ATTACK_FORMAT_COVERAGE.get(attack_name)
    if coverage is None:
        return True, False, ""

    supported = coverage.get("supported", set())
    degraded = coverage.get("degraded", set())

    if fmt in supported:
        return True, False, ""
    if fmt in degraded:
        return (
            True,
            True,
            f"{attack_name} on {fmt} is a degraded simulation and may not reflect real parser behavior.",
        )
    return (
        False,
        False,
        f"{attack_name} is not supported for {fmt}. Choose a compatible format for this technique.",
    )
