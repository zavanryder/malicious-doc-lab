"""Payload model — combines attack content with document template."""

from pydantic import BaseModel

from maldoc.attacks.base import AttackResult


class Payload(BaseModel):
    """A complete payload ready for document generation."""

    attack_result: AttackResult
    template_name: str
    title: str
    body: str
