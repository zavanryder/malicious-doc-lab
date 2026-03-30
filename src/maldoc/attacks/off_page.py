"""Off-page / layered text attack — payload placed outside visible area or under layers."""

from maldoc.attacks.base import AttackResult, BaseAttack


class OffPageAttack(BaseAttack):
    name = "off_page"
    description = "Places payload outside the visible page area or behind overlapping elements"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        return AttackResult(
            visible_content=body,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "off_page_text": payload,
                "x_offset": -1000,
                "y_offset": -1000,
                "layer": "background",
            },
        )
