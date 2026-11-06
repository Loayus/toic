"""Remplit la base avec data/questions.json, généré par scripts/build_questions.py."""

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Passage, Question

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"


def _passage_title(content: str) -> str:
    first_line = next(line.strip() for line in content.splitlines() if line.strip())
    return first_line if len(first_line) <= 80 else f"{first_line[:77]}..."


def seed_if_empty(db: Session) -> None:
    """Remplit la base au premier démarrage ; ne touche pas à une base déjà remplie."""
    if db.scalar(select(func.count()).select_from(Question)):
        return

    passages: dict[str, Passage] = {}
    for item in json.loads(DATA_FILE.read_text(encoding="utf-8")):
        content = item["passage"]
        passage = None
        if content:
            passage = passages.setdefault(
                content, Passage(title=_passage_title(content), content=content)
            )
        db.add(
            Question(
                part=item["part"],
                category=item["category"],
                difficulty=item["difficulty"],
                prompt=item["prompt"],
                options=item["options"],
                correct_choice=item["correct_choice"],
                explanation=item["explanation"],
                source=item["source"],
                passage=passage,
            )
        )
    db.commit()
