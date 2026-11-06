import re
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Question
from app.seed import DATA_FILE, seed_if_empty


@pytest.fixture
def db_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        seed_if_empty(db)
    yield factory
    engine.dispose()


@pytest.fixture
def client(db_factory):
    def override_get_db():
        with db_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def correct_choice(db_factory, question_id: int) -> str:
    with db_factory() as db:
        return db.get(Question, question_id).correct_choice


def wrong_choice(db_factory, question_id: int) -> str:
    return "B" if correct_choice(db_factory, question_id) == "A" else "A"


def test_seed_data_is_well_formed(db_factory):
    with db_factory() as db:
        questions = db.scalars(select(Question)).all()
    assert len(questions) >= 1000
    assert {q.part for q in questions} == {5, 6, 7}
    part_5_prompts = [q.prompt for q in questions if q.part == 5]
    assert len(set(part_5_prompts)) == len(part_5_prompts)
    for q in questions:
        assert sorted(q.options) == ["A", "B", "C", "D"]
        assert len(set(q.options.values())) == 4
        assert q.correct_choice in q.options
        assert q.explanation
        assert q.source
        assert (q.passage_id is None) == (q.part == 5)


def test_explanations_are_in_french_and_do_not_cite_shuffled_letters(db_factory):
    with db_factory() as db:
        explanations = db.scalars(select(Question.explanation)).all()
    chinese = re.compile(r"[一-鿿]")
    letter = re.compile(r"\b(?:réponse|choix|option|proposition) [A-D]\b|^[A-D]\b(?!['’])")
    assert not [text for text in explanations if chinese.search(text)]
    assert not [text for text in explanations if letter.search(text)]


def test_correct_answers_are_evenly_spread(db_factory):
    """La source met presque toujours la bonne réponse en A : l'import doit corriger ça."""
    with db_factory() as db:
        questions = db.scalars(select(Question)).all()
    for letter in "ABCD":
        share = sum(q.correct_choice == letter for q in questions) / len(questions)
        assert 0.2 < share < 0.3, (letter, share)


def test_excluded_third_party_questions_are_absent():
    content = DATA_FILE.read_text(encoding="utf-8")
    assert "P5-E0" not in content  # questions d'ESL Lounge présentes dans le dépôt source
    assert "The factory implemented ______ measures" not in content


def test_seed_is_idempotent(db_factory):
    with db_factory() as db:
        before = len(db.scalars(select(Question)).all())
        seed_if_empty(db)
        assert len(db.scalars(select(Question)).all()) == before


def test_question_endpoints_never_leak_the_answer(client):
    listed = client.get("/questions").json()["items"][0]
    single = client.get(f"/questions/{listed['id']}").json()
    session = client.post("/sessions").json()["questions"][0]["question"]
    for question in (listed, single, session):
        assert "correct_choice" not in question
        assert "explanation" not in question


def test_list_questions_filters_and_paginates(client):
    page = client.get("/questions", params={"part": 7, "limit": 2, "offset": 1}).json()
    assert len(page["items"]) == 2
    assert page["total"] > 2
    assert all(q["part"] == 7 and q["passage"] for q in page["items"])

    by_category = client.get("/questions", params={"category": "vocabulary"}).json()
    assert by_category["items"]
    assert all(q["category"] == "vocabulary" for q in by_category["items"])


def test_invalid_filter_is_rejected(client):
    assert client.get("/questions", params={"part": 1}).status_code == 422
    assert client.get("/questions", params={"difficulty": "expert"}).status_code == 422


def test_check_question(client, db_factory):
    good = correct_choice(db_factory, 1)
    result = client.post("/questions/1/check", json={"choice": good}).json()
    assert result["is_correct"] is True
    assert result["explanation"]

    bad = wrong_choice(db_factory, 1)
    assert client.post("/questions/1/check", json={"choice": bad}).json()["is_correct"] is False
    assert client.post("/questions/1/check", json={"choice": "E"}).status_code == 422
    assert client.post("/questions/9999/check", json={"choice": "A"}).status_code == 404


def test_session_respects_filters_and_has_no_duplicates(client):
    response = client.post("/sessions", json={"part": 5, "question_count": 5})
    assert response.status_code == 201
    session = response.json()
    questions = [item["question"] for item in session["questions"]]
    assert session["total"] == 5
    assert session["status"] == "in_progress"
    assert all(q["part"] == 5 for q in questions)
    assert len({q["id"] for q in questions}) == 5
    assert [item["position"] for item in session["questions"]] == [1, 2, 3, 4, 5]


def test_session_is_capped_at_available_questions(client):
    combinations = (
        {"part": part, "difficulty": difficulty}
        for part in (5, 6, 7)
        for difficulty in ("easy", "medium", "hard")
    )
    totals = ((f, client.get("/questions", params=f).json()["total"]) for f in combinations)
    filters, available = next((f, total) for f, total in totals if 0 < total < 100)
    session = client.post("/sessions", json={**filters, "question_count": 100}).json()
    assert session["total"] == available


def test_session_orders_by_part_and_groups_passages(client):
    session = client.post("/sessions", json={"question_count": 100}).json()
    questions = [item["question"] for item in session["questions"]]
    parts = [q["part"] for q in questions]
    assert parts == sorted(parts)

    for part in (6, 7):
        passage_ids = [q["passage"]["id"] for q in questions if q["part"] == part]
        assert passage_ids == sorted(passage_ids)


def test_partial_session_keeps_passage_questions_in_order(client):
    session = client.post("/sessions", json={"part": 6, "question_count": 60}).json()
    by_passage: dict[int, list[int]] = {}
    for item in session["questions"]:
        question = item["question"]
        by_passage.setdefault(question["passage"]["id"], []).append(question["id"])
    assert all(ids == sorted(ids) for ids in by_passage.values())


def test_full_exam_has_whole_passages_in_the_official_layout(client, db_factory):
    for _ in range(5):
        session = client.post("/sessions").json()
        questions = [item["question"] for item in session["questions"]]
        parts = [q["part"] for q in questions]
        assert (parts.count(5), parts.count(6), parts.count(7)) == (30, 16, 54)
        assert len({q["id"] for q in questions}) == 100

        with db_factory() as db:
            sizes = Counter(db.scalars(select(Question.passage_id)).all())
        drawn = Counter(q["passage"]["id"] for q in questions if q["passage"])
        assert drawn == {passage_id: sizes[passage_id] for passage_id in drawn}
        part_6_sizes = Counter(q["passage"]["id"] for q in questions if q["part"] == 6)
        assert set(part_6_sizes.values()) == {4}

def test_session_without_matching_question(client):
    response = client.post(
        "/sessions", json={"part": 5, "category": "comprehension"}
    )
    assert response.status_code == 404


def test_session_rejects_invalid_count(client):
    assert client.post("/sessions", json={"question_count": 0}).status_code == 422


def test_full_session_flow(client, db_factory):
    session = client.post("/sessions", json={"part": 5, "question_count": 3}).json()
    url = f"/sessions/{session['id']}"
    q1, q2, q3 = [item["question"]["id"] for item in session["questions"]]

    good = client.post(
        f"{url}/answers", json={"question_id": q1, "choice": correct_choice(db_factory, q1)}
    )
    assert good.status_code == 200
    assert good.json()["is_correct"] is True

    bad = client.post(
        f"{url}/answers", json={"question_id": q2, "choice": wrong_choice(db_factory, q2)}
    )
    assert bad.json()["is_correct"] is False

    # La correction de la question restante ne doit pas fuiter avant la réponse.
    partial = client.get(f"{url}/results").json()
    assert partial["status"] == "in_progress"
    assert partial["answered"] == 2
    assert partial["items"][2]["correct_choice"] is None
    assert partial["items"][2]["explanation"] is None

    client.post(
        f"{url}/answers", json={"question_id": q3, "choice": correct_choice(db_factory, q3)}
    )
    results = client.get(f"{url}/results").json()
    assert results["status"] == "completed"
    assert results["correct"] == 2
    assert results["score"] == 9.9
    assert results["max_score"] == 14.85
    assert results["by_part"][0] == {
        "label": "Part 5",
        "answered": 3,
        "correct": 2,
        "accuracy_percent": 66.7,
    }
    assert client.get(url).json()["status"] == "completed"


def test_unanswered_questions_count_against_score(client, db_factory):
    session = client.post("/sessions", json={"part": 5, "question_count": 4}).json()
    url = f"/sessions/{session['id']}"
    question_id = session["questions"][0]["question"]["id"]
    client.post(
        f"{url}/answers",
        json={"question_id": question_id, "choice": correct_choice(db_factory, question_id)},
    )
    results = client.get(f"{url}/results").json()
    assert results["score"] == 4.95
    assert results["max_score"] == 19.8


@pytest.mark.parametrize(
    ("choose", "expected_correct", "expected_score"),
    [(correct_choice, 100, 495.0), (wrong_choice, 0, 0.0)],
)
def test_full_exam_is_scored_out_of_495(
    client, db_factory, choose, expected_correct, expected_score
):
    session = client.post("/sessions").json()
    assert session["total"] == 100
    parts = [item["question"]["part"] for item in session["questions"]]
    assert (parts.count(5), parts.count(6), parts.count(7)) == (30, 16, 54)

    url = f"/sessions/{session['id']}"
    for item in session["questions"]:
        question_id = item["question"]["id"]
        client.post(
            f"{url}/answers",
            json={"question_id": question_id, "choice": choose(db_factory, question_id)},
        )

    results = client.get(f"{url}/results").json()
    assert results["status"] == "completed"
    assert results["correct"] == expected_correct
    assert results["score"] == expected_score
    assert results["max_score"] == 495.0


def test_cannot_answer_twice(client):
    session = client.post("/sessions", json={"question_count": 1}).json()
    url = f"/sessions/{session['id']}/answers"
    payload = {"question_id": session["questions"][0]["question"]["id"], "choice": "A"}
    several = {**payload, "choice": ["A", "B"]}
    assert client.post(url, json=several).status_code == 422
    assert client.post(url, json=payload).status_code == 200
    assert client.post(url, json=payload).status_code == 409


def test_cannot_answer_question_outside_session(client):
    session = client.post("/sessions", json={"part": 5, "question_count": 1}).json()
    part_7_id = client.get("/questions", params={"part": 7}).json()["items"][0]["id"]
    response = client.post(
        f"/sessions/{session['id']}/answers", json={"question_id": part_7_id, "choice": "A"}
    )
    assert response.status_code == 404


def test_unknown_session(client):
    assert client.get("/sessions/9999").status_code == 404
    assert client.get("/sessions/9999/results").status_code == 404
    response = client.post("/sessions/9999/answers", json={"question_id": 1, "choice": "A"})
    assert response.status_code == 404


def test_stats_aggregate_across_sessions(client, db_factory):
    empty = client.get("/stats").json()
    assert empty == {
        "answered": 0,
        "correct": 0,
        "accuracy_percent": 0.0,
        "by_part": [],
        "by_category": [],
    }

    for choose in (correct_choice, wrong_choice):
        session = client.post("/sessions", json={"part": 5, "question_count": 1}).json()
        question_id = session["questions"][0]["question"]["id"]
        client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": question_id, "choice": choose(db_factory, question_id)},
        )

    stats = client.get("/stats").json()
    assert stats["answered"] == 2
    assert stats["correct"] == 1
    assert stats["accuracy_percent"] == 50.0
    assert stats["by_part"][0]["label"] == "Part 5"
