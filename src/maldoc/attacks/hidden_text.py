"""Hidden text attack — zero-width characters and font-size-zero text."""

from maldoc.attacks.base import AttackResult, BaseAttack

ZERO_WIDTH_SPACE = "\u200b"
ZERO_WIDTH_NON_JOINER = "\u200c"
ZERO_WIDTH_JOINER = "\u200d"


def encode_zero_width(text: str) -> str:
    """Encode text as zero-width character sequences.

    Each character is converted to its binary representation,
    then each bit is mapped to a zero-width character.
    """
    chars = {
        "0": ZERO_WIDTH_SPACE,
        "1": ZERO_WIDTH_NON_JOINER,
    }
    encoded = []
    for char in text:
        bits = format(ord(char), "08b")
        encoded.append("".join(chars[b] for b in bits))
    return ZERO_WIDTH_JOINER.join(encoded)


class HiddenTextAttack(BaseAttack):
    name = "hidden_text"
    description = "Embeds payload using zero-width characters or font-size-zero text"

    def apply(self, payload: str, template: dict) -> AttackResult:
        encoded = encode_zero_width(payload)
        body = template.get("body", "")
        # Insert encoded payload in the middle of the visible content
        midpoint = len(body) // 2
        combined = body[:midpoint] + encoded + body[midpoint:]

        return AttackResult(
            visible_content=combined,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "zero_width_encoded": encoded,
                "font_size_zero_text": payload,
                "insertion_point": midpoint,
            },
        )
