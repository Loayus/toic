from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Passage(Base):
    """Texte partagé par plusieurs questions (parties 6 et 7)."""

    __tablename__ = "passages"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str]


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    part: Mapped[int] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    difficulty: Mapped[str] = mapped_column(String(10), index=True)
    prompt: Mapped[str]
    options: Mapped[dict[str, str]] = mapped_column(JSON)
    correct_choice: Mapped[str] = mapped_column(String(1))
    explanation: Mapped[str]
    passage_id: Mapped[int | None] = mapped_column(ForeignKey("passages.id"))

    passage: Mapped[Passage | None] = relationship()


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    items: Mapped[list["SessionItem"]] = relationship(
        back_populates="session",
        order_by="SessionItem.position",
        cascade="all, delete-orphan",
    )


class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = (UniqueConstraint("session_id", "question_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("practice_sessions.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int]
    chosen_choice: Mapped[str | None] = mapped_column(String(1))

    session: Mapped[PracticeSession] = relationship(back_populates="items")
    question: Mapped[Question] = relationship()

    @property
    def is_correct(self) -> bool | None:
        if self.chosen_choice is None:
            return None
        return self.chosen_choice == self.question.correct_choice
