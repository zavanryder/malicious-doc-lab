"""Attack class implementations."""

from maldoc.attacks.chunk_split import ChunkSplitAttack
from maldoc.attacks.delayed_trigger import DelayedTriggerAttack
from maldoc.attacks.encoding_obfuscation import EncodingObfuscationAttack
from maldoc.attacks.hidden_text import HiddenTextAttack
from maldoc.attacks.markdown_exfil import MarkdownExfilAttack
from maldoc.attacks.metadata import MetadataAttack
from maldoc.attacks.ocr_bait import OcrBaitAttack
from maldoc.attacks.off_page import OffPageAttack
from maldoc.attacks.retrieval_poison import RetrievalPoisonAttack
from maldoc.attacks.summary_steer import SummarySteerAttack
from maldoc.attacks.tool_routing import ToolRoutingAttack
from maldoc.attacks.typoglycemia import TypoglycemiaAttack
from maldoc.attacks.visual_scaling_injection import VisualScalingInjectionAttack
from maldoc.attacks.white_on_white import WhiteOnWhiteAttack

ATTACK_REGISTRY: dict[str, type] = {
    "hidden_text": HiddenTextAttack,
    "white_on_white": WhiteOnWhiteAttack,
    "metadata": MetadataAttack,
    "retrieval_poison": RetrievalPoisonAttack,
    "ocr_bait": OcrBaitAttack,
    "off_page": OffPageAttack,
    "chunk_split": ChunkSplitAttack,
    "summary_steer": SummarySteerAttack,
    "delayed_trigger": DelayedTriggerAttack,
    "tool_routing": ToolRoutingAttack,
    "encoding_obfuscation": EncodingObfuscationAttack,
    "typoglycemia": TypoglycemiaAttack,
    "markdown_exfil": MarkdownExfilAttack,
    "visual_scaling_injection": VisualScalingInjectionAttack,
}


def get_attack(name: str):
    """Get an attack class instance by name."""
    cls = ATTACK_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(ATTACK_REGISTRY.keys())
        raise ValueError(f"Unknown attack '{name}'. Available: {available}")
    return cls()


def list_attacks() -> list[str]:
    """Return list of available attack names."""
    return list(ATTACK_REGISTRY.keys())
