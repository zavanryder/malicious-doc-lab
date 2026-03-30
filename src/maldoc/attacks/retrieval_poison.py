"""Retrieval poisoning attack — content designed to rank high for target queries."""

from maldoc.attacks.base import AttackResult, BaseAttack


class RetrievalPoisonAttack(BaseAttack):
    name = "retrieval_poison"
    description = "Embeds payload surrounded by high-relevance keyword clusters"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        # Wrap payload in keyword-rich context to boost retrieval ranking
        boosted = (
            f"IMPORTANT: This section contains critical information. "
            f"Summary: {payload} "
            f"Key findings: {payload} "
            f"Conclusion: {payload}"
        )
        combined = f"{body}\n\n{boosted}"

        return AttackResult(
            visible_content=combined,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "boosted_content": boosted,
                "position": "appended",
            },
        )
