import random
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import schemas
from .database import Base, SessionLocal, engine, get_db
from .models import PracticeSession, Question, SessionItem
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(
    title="API QCM TOEIC",
    description=(
        "Entraînement au TOEIC Reading (parties 5, 6 et 7) avec des questions de style "
        "TOEIC sous licence ouverte. Ce ne sont pas des questions officielles d'ETS."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

Db = Annotated[Session, Depends(get_db)]

POINTS_PER_QUESTION = 4.95  # 495 points pour les 100 questions du Reading
EXAM_QUESTION_COUNT = 100
EXAM_QUOTAS = {5: 30, 6: 16, 7: 54}
# Comme au vrai test : 4 questions par texte en partie 6, au moins 2 en partie 7.
EXAM_MIN_GROUP_SIZES = {5: 1, 6: 4, 7: 2}
EXAM_DRAW_ATTEMPTS = 200


def _points(question_count: int) -> float:
    return round(question_count * POINTS_PER_QUESTION, 2)


def _fill_quota(groups: list[list], quota: int) -> list | None:
    """Prend des groupes entiers au hasard jusqu'à atteindre exactement le quota."""
    for _ in range(EXAM_DRAW_ATTEMPTS):
        random.shuffle(groups)
        picked: list = []
        for group in groups:
            if len(picked) + len(group) <= quota:
                picked += group
            if len(picked) == quota:
                return picked
    return None


def _draw_exam(candidates: list) -> list | None:
    """Tire un examen réparti comme le vrai test, sans couper les textes."""
    exam: list = []
    for part, quota in EXAM_QUOTAS.items():
        groups: dict[int, list] = {}
        for row in candidates:
            if row.part == part:
                key = row.passage_id if row.passage_id else -row.id
                groups.setdefault(key, []).append(row)
        usable = [g for g in groups.values() if len(g) >= EXAM_MIN_GROUP_SIZES[part]]
        picked = _fill_quota(usable, quota)
        if picked is None:
            return None
        exam += picked
    return exam


def _filters(part: int | None, category: str | None, difficulty: str | None) -> list:
    conditions = []
    if part is not None:
        conditions.append(Question.part == part)
    if category is not None:
        conditions.append(Question.category == category)
    if difficulty is not None:
        conditions.append(Question.difficulty == difficulty)
    return conditions


def _get_question(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question introuvable.")
    return question


def _get_session(db: Session, session_id: int) -> PracticeSession:
    session = db.get(PracticeSession, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session introuvable.")
    return session


def _percent(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def _breakdown(
    items: Iterable[SessionItem], label: Callable[[Question], str]
) -> list[schemas.Breakdown]:
    """Regroupe les réponses données par libellé (partie, catégorie...)."""
    groups: dict[str, list[int]] = {}
    for item in items:
        if item.chosen_choice is None:
            continue
        counts = groups.setdefault(label(item.question), [0, 0])
        counts[0] += 1
        counts[1] += item.is_correct
    return [
        schemas.Breakdown(
            label=name,
            answered=answered,
            correct=correct,
            accuracy_percent=_percent(correct, answered),
        )
        for name, (answered, correct) in sorted(groups.items())
    ]


def _part_label(question: Question) -> str:
    return f"Part {question.part}"


def _category_label(question: Question) -> str:
    return question.category


def _session_status(session: PracticeSession) -> str:
    done = all(item.chosen_choice is not None for item in session.items)
    return "completed" if done else "in_progress"


def _session_out(session: PracticeSession) -> schemas.SessionOut:
    return schemas.SessionOut(
        id=session.id,
        created_at=session.created_at,
        status=_session_status(session),
        total=len(session.items),
        answered=sum(item.chosen_choice is not None for item in session.items),
        questions=[
            schemas.SessionQuestion(
                position=item.position,
                chosen_choice=item.chosen_choice,
                question=schemas.QuestionOut.model_validate(item.question),
            )
            for item in session.items
        ],
    )


@app.get("/questions", response_model=schemas.QuestionPage, tags=["Questions"])
def list_questions(
    db: Db,
    part: Annotated[int | None, Query(ge=5, le=7)] = None,
    category: schemas.Category | None = None,
    difficulty: schemas.Difficulty | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    conditions = _filters(part, category, difficulty)
    total = db.scalar(select(func.count()).select_from(Question).where(*conditions))
    items = db.scalars(
        select(Question).where(*conditions).order_by(Question.id).limit(limit).offset(offset)
    ).all()
    return schemas.QuestionPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[schemas.QuestionOut.model_validate(q) for q in items],
    )


@app.get("/questions/{question_id}", response_model=schemas.QuestionOut, tags=["Questions"])
def get_question(question_id: int, db: Db):
    return _get_question(db, question_id)


@app.post(
    "/questions/{question_id}/check", response_model=schemas.CheckResult, tags=["Questions"]
)
def check_question(question_id: int, payload: schemas.CheckRequest, db: Db):
    """Corrige une question hors session (rien n'est enregistré)."""
    question = _get_question(db, question_id)
    return schemas.CheckResult(
        question_id=question.id,
        chosen_choice=payload.choice,
        is_correct=payload.choice == question.correct_choice,
        correct_choice=question.correct_choice,
        explanation=question.explanation,
    )


@app.post(
    "/sessions",
    response_model=schemas.SessionOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
def create_session(db: Db, payload: schemas.SessionCreate | None = None):
    """Tire des questions au hasard, dans la limite de celles disponibles.

    Sans filtre, une session de 100 questions est un examen complet : 30 questions de
    partie 5, 16 de partie 6 et 54 de partie 7, avec des textes entiers.

    Comme au vrai TOEIC, les questions sont classées par partie, et celles d'un même
    texte se suivent dans l'ordre.
    """
    payload = payload or schemas.SessionCreate()
    conditions = _filters(payload.part, payload.category, payload.difficulty)
    candidates = db.execute(
        select(Question.id, Question.part, Question.passage_id)
        .where(*conditions)
        .order_by(Question.id)
    ).all()
    if not candidates:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Aucune question ne correspond à ces critères."
        )

    picked = None
    if not conditions and payload.question_count == EXAM_QUESTION_COUNT:
        picked = _draw_exam(candidates)
    if picked is None:
        picked = random.sample(candidates, min(payload.question_count, len(candidates)))
    picked.sort(key=lambda r: (r.part, r.passage_id or 0, r.id if r.passage_id else 0))

    session = PracticeSession(
        items=[
            SessionItem(question_id=row.id, position=position)
            for position, row in enumerate(picked, start=1)
        ]
    )
    db.add(session)
    db.commit()
    return _session_out(session)


@app.get("/sessions/{session_id}", response_model=schemas.SessionOut, tags=["Sessions"])
def get_session(session_id: int, db: Db):
    return _session_out(_get_session(db, session_id))


@app.post(
    "/sessions/{session_id}/answers", response_model=schemas.CheckResult, tags=["Sessions"]
)
def answer_question(session_id: int, payload: schemas.AnswerRequest, db: Db):
    session = _get_session(db, session_id)
    item = next((i for i in session.items if i.question_id == payload.question_id), None)
    if item is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Cette question ne fait pas partie de la session."
        )
    if item.chosen_choice is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette question a déjà reçu une réponse.")

    item.chosen_choice = payload.choice
    db.commit()
    return schemas.CheckResult(
        question_id=item.question_id,
        chosen_choice=payload.choice,
        is_correct=item.is_correct,
        correct_choice=item.question.correct_choice,
        explanation=item.question.explanation,
    )


@app.get(
    "/sessions/{session_id}/results", response_model=schemas.SessionResults, tags=["Sessions"]
)
def get_results(session_id: int, db: Db):
    """Note de la session : 4,95 points par bonne réponse, 0 sinon ou sans réponse."""
    session = _get_session(db, session_id)
    answered = [item for item in session.items if item.chosen_choice is not None]
    correct = sum(item.is_correct for item in answered)
    return schemas.SessionResults(
        session_id=session.id,
        status=_session_status(session),
        total=len(session.items),
        answered=len(answered),
        correct=correct,
        score=_points(correct),
        max_score=_points(len(session.items)),
        by_part=_breakdown(answered, _part_label),
        by_category=_breakdown(answered, _category_label),
        items=[
            schemas.ResultItem(
                position=item.position,
                question_id=item.question_id,
                chosen_choice=item.chosen_choice,
                is_correct=item.is_correct,
                correct_choice=item.question.correct_choice if item.chosen_choice else None,
                explanation=item.question.explanation if item.chosen_choice else None,
            )
            for item in session.items
        ],
    )


@app.get("/stats", response_model=schemas.Stats, tags=["Statistiques"])
def get_stats(db: Db):
    """Taux de réussite global, toutes sessions confondues, pour repérer ses points faibles."""
    answered = db.scalars(select(SessionItem).where(SessionItem.chosen_choice.is_not(None))).all()
    correct = sum(item.is_correct for item in answered)
    return schemas.Stats(
        answered=len(answered),
        correct=correct,
        accuracy_percent=_percent(correct, len(answered)),
        by_part=_breakdown(answered, _part_label),
        by_category=_breakdown(answered, _category_label),
    )
