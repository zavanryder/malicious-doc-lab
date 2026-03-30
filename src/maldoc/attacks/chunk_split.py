"""Chunk-boundary split attack — payload split across chunk boundaries to evade detection."""

from maldoc.attacks.base import AttackResult, BaseAttack

TARGET_CHUNK_SIZE = 500


def split_payload_for_chunks(payload: str, filler: str, chunk_size: int = TARGET_CHUNK_SIZE) -> str:
    """Insert filler text between payload segments so each lands in a different chunk.

    Splits payload at midpoint and pads with filler to push the second half
    across a chunk boundary.
    """
    words = payload.split()
    if len(words) <= 1:
        return filler + payload

    mid = len(words) // 2
    part_a = " ".join(words[:mid])
    part_b = " ".join(words[mid:])

    pad_length = max(0, chunk_size - len(part_a) - 50)
    padding = (filler + " ") * (pad_length // (len(filler) + 1) + 1)
    padding = padding[:pad_length]

    return f"{part_a}\n{padding}\n{part_b}"


class ChunkSplitAttack(BaseAttack):
    name = "chunk_split"
    description = "Splits payload across chunk boundaries so no single chunk contains the full instruction"

    def apply(self, payload: str, template: dict) -> AttackResult:
        body = template.get("body", "")
        split_content = split_payload_for_chunks(payload, body)

        return AttackResult(
            visible_content=split_content,
            hidden_content=payload,
            technique=self.name,
            format_hints={
                "split_strategy": "mid_word_boundary",
                "target_chunk_size": TARGET_CHUNK_SIZE,
            },
        )
