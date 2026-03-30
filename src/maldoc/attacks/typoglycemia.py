"""Typoglycemia attack — scrambled words that remain readable by LLMs."""

import re

from maldoc.attacks.base import AttackResult, BaseAttack


def scramble_word(word: str) -> str:
    """Deterministically scramble a word while preserving first/last letters."""
    if len(word) < 4:
        return word
    middle = list(word[1:-1])
    if len(set(middle)) <= 1:
        return word
    scrambled_middle = middle[1:] + middle[:1]
    return f"{word[0]}{''.join(scrambled_middle)}{word[-1]}"


def typoglycemia_transform(text: str) -> str:
    """Apply typoglycemia-style scrambling to alphabetic tokens."""
    return re.sub(r"[A-Za-z]{4,}", lambda m: scramble_word(m.group(0)), text)


class TypoglycemiaAttack(BaseAttack):
    name = "typoglycemia"
    description = "Embeds payload with scrambled middle letters to evade naive keyword filters"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        scrambled_payload = typoglycemia_transform(payload)
        combined = f"{body}\n\n{scrambled_payload}"

        return AttackResult(
            visible_content=combined,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "obfuscated_payload": scrambled_payload,
                "obfuscation_type": "typoglycemia",
            },
        )
