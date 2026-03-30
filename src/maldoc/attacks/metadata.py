"""Metadata injection attack — payload injected into document metadata fields."""

from maldoc.attacks.base import AttackResult, BaseAttack


class MetadataAttack(BaseAttack):
    name = "metadata"
    description = "Injects payload into document metadata fields (author, subject, keywords)"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        return AttackResult(
            visible_content=body,
            hidden_content=payload,
            technique=self.name,
            metadata={
                "author": payload,
                "subject": payload,
                "keywords": payload,
                "description": payload,
            },
            format_hints={"inject_metadata": True},
        )
