"""Encoding and obfuscation attack — payload hidden via encoded text variants."""

from base64 import b64encode

from maldoc.attacks.base import AttackResult, BaseAttack


def _unicode_escape(text: str) -> str:
    return "".join(f"\\u{ord(ch):04x}" for ch in text)


class EncodingObfuscationAttack(BaseAttack):
    name = "encoding_obfuscation"
    description = "Embeds encoded payload variants (base64/hex/unicode) to evade simple filters"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        payload_bytes = payload.encode("utf-8")
        b64_payload = b64encode(payload_bytes).decode("ascii")
        hex_payload = payload_bytes.hex()
        unicode_payload = _unicode_escape(payload)

        obfuscated_block = (
            "Diagnostic payloads (machine-generated):\n"
            f"base64: {b64_payload}\n"
            f"hex: {hex_payload}\n"
            f"unicode: {unicode_payload}"
        )
        combined = f"{body}\n\n{obfuscated_block}"

        return AttackResult(
            visible_content=combined,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "obfuscated_variants": [b64_payload, hex_payload, unicode_payload],
                "encoding_methods": ["base64", "hex", "unicode_escape"],
            },
        )
