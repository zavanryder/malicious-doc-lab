"""OCR bait attack — payload embedded in images designed to be extracted by OCR."""

from maldoc.attacks.base import AttackResult, BaseAttack


class OcrBaitAttack(BaseAttack):
    name = "ocr_bait"
    description = "Embeds payload as text in images that OCR will extract but humans may overlook"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        return AttackResult(
            visible_content=body,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "ocr_text": payload,
                "font_size": 6,
                "font_color": "#E0E0E0",
                "background_color": "#F0F0F0",
                "position": "footer",
            },
        )
