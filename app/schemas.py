from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Choice = Literal["A", "B", "C", "D"]
Category = Literal["grammar", "vocabulary", "comprehension"]
Difficulty = Literal["easy", "medium", "hard"]
Status = Literal["in_progress", "completed"]


class PassageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str


class QuestionOut(BaseModel):
    """Question telle que vue par le candidat : jamais la bonne réponse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    part: int
    category: Category
    difficulty: Difficulty
    prompt: str
    options: dict[Choice, str]
    source: str
    passage: PassageOut | None


class QuestionPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[QuestionOut]


class CheckRequest(BaseModel):
    choice: Choice


class CheckResult(BaseModel):
    question_id: int
    chosen_choice: Choice
    is_correct: bool
    correct_choice: Choice
    explanation: str


class SessionCreate(BaseModel):
    question_count: int = Field(default=100, ge=1, le=100)
    part: int | None = Field(default=None, ge=5, le=7)
    category: Category | None = None
    difficulty: Difficulty | None = None


class SessionQuestion(BaseModel):
    position: int
    chosen_choice: Choice | None
    question: QuestionOut


class SessionOut(BaseModel):
    id: int
    created_at: datetime
    status: Status
    total: int
    answered: int
    questions: list[SessionQuestion]


class AnswerRequest(BaseModel):
    question_id: int
    choice: Choice


class Breakdown(BaseModel):
    label: str
    answered: int
    correct: int
    accuracy_percent: float


class ResultItem(BaseModel):
    """La correction n'est renseignée que pour les questions déjà répondues."""

    position: int
    question_id: int
    chosen_choice: Choice | None
    is_correct: bool | None
    correct_choice: Choice | None
    explanation: str | None


class SessionResults(BaseModel):
    session_id: int
    status: Status
    total: int
    answered: int
    correct: int
    score: float
    max_score: float
    by_part: list[Breakdown]
    by_category: list[Breakdown]
    items: list[ResultItem]


class Stats(BaseModel):
    answered: int
    correct: int
    accuracy_percent: float
    by_part: list[Breakdown]
    by_category: list[Breakdown]
