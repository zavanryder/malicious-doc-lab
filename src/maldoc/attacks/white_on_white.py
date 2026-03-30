"""White-on-white text attack — payload rendered in white text on white background."""

from maldoc.attacks.base import AttackResult, BaseAttack


class WhiteOnWhiteAttack(BaseAttack):
    name = "white_on_white"
    description = "Embeds payload as white text on a white background"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        return AttackResult(
            visible_content=body,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "hidden_font_color": "#FFFFFF",
                "background_color": "#FFFFFF",
                "position": "end",
            },
        )
