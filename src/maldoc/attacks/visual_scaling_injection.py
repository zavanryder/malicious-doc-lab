"""Visual scaling injection attack — payload hidden in visuals intended for resized inputs."""

from maldoc.attacks.base import AttackResult, BaseAttack


class VisualScalingInjectionAttack(BaseAttack):
    name = "visual_scaling_injection"
    description = "Hides payload in low-visibility visual regions likely to appear after scaling"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")

        return AttackResult(
            visible_content=body,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "decoy_text": "Quarterly KPI chart (reference view)",
                "visual_trigger_text": payload,
                "intended_transform": "downscale",
            },
        )
