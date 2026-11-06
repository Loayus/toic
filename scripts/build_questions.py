"""Construit data/questions.json à partir des sources sous licence ouverte.

Usage : python -I scripts/build_questions.py DOSSIER_OCEAN FICHIER_VOCAB [--candidates]

Sources (voir THIRD_PARTY_NOTICES.md) :
- kdeppaei/toeic-question-ocean, commit a940bb8 (MIT)
- kknono668/toeic-vocab-tw, révision 7b1f881 (CC BY-SA 4.0)

Les fichiers JavaScript de la première source sont lus comme des données par un
analyseur de littéraux : leur code n'est jamais exécuté. Le fichier
part5-exercise-guides.js en est volontairement exclu, car il reprend des questions
d'un site tiers que la licence MIT du dépôt ne couvre pas.
"""

import collections
import json
import pathlib
import random
import re
import sys

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "questions.json"
# Corrections de la première source, traduites en français (identifiant -> explication).
TRANSLATIONS = OUTPUT.with_name("explanations_fr.json")
OCEAN_SOURCE = "TOEIC Question Ocean (MIT)"
VOCAB_SOURCE = "toeic-vocab-tw (CC BY-SA 4.0)"
VOCAB_QUESTION_COUNT = 200

# Questions générées écartées après relecture : un autre choix convenait aussi.
REVIEWED_CANDIDATES = 260
REJECTED_VOCAB_IDS = {
    f"V-{word}"
    for word in """
    ability admin appears attendees bathrooms branding business cautiously cheap clarifying
    commitment committee completing conditions decline delegate delegation desirable encountered
    facility fantastic fascinating grand gratitude indirectly initiative innovative kept lighter
    listed memorable motive noise observed organic partners pending preferring presented promptly
    purchased safer silently specialized specifically stating strange supporter television
    unstable upcoming visitors wise worthwhile young
    """.split()
}

VOCABULARY_CATEGORIES = {
    "商務字彙", "固定搭配", "動詞搭配", "介系詞搭配", "名詞搭配", "形容詞語意",
    "語意副詞", "語意連接詞", "名詞選擇", "片語介系詞", "原因片語",
}
DIFFICULTIES = {"400": "easy", "600": "medium", "800": "hard"}
# Dans ces fichiers, une difficulté absente vaut « 800 » (valeur par défaut de la source).
DEFAULT_HARD_FILES = {"question-bank-v29.js", "question-bank-v210.js", "question-bank-v30.js"}


class NotLiteral(Exception):
    pass


class Expression:
    """Expression non littérale (identifiant, appel...), conservée comme simple texte."""

    def __init__(self, text: str):
        self.text = text


class LiteralParser:
    NUMBER = re.compile(r"-?\d+(\.\d+)?\b")
    NAME = re.compile(r"[A-Za-z_$][\w$.]*")
    KEY = re.compile(r"[A-Za-z_$][\w$]*")

    def __init__(self, text: str, start: int = 0):
        self.text = text
        self.pos = start

    def skip_space(self) -> None:
        while True:
            while self.pos < len(self.text) and self.text[self.pos].isspace():
                self.pos += 1
            if self.text.startswith("//", self.pos):
                end = self.text.find("\n", self.pos)
                self.pos = len(self.text) if end < 0 else end
            elif self.text.startswith("/*", self.pos):
                self.pos = self.text.index("*/", self.pos) + 2
            else:
                return

    def string(self) -> str:
        quote = self.text[self.pos]
        self.pos += 1
        chars = []
        while True:
            char = self.text[self.pos]
            if char == "\\":
                following = self.text[self.pos + 1]
                if following == "u":
                    chars.append(chr(int(self.text[self.pos + 2 : self.pos + 6], 16)))
                    self.pos += 6
                else:
                    chars.append({"n": "\n", "t": "\t", "r": "\r"}.get(following, following))
                    self.pos += 2
            elif char == quote:
                self.pos += 1
                return "".join(chars)
            elif char == "\n" and quote != "`":
                raise NotLiteral
            else:
                chars.append(char)
                self.pos += 1

    def value(self):
        self.skip_space()
        char = self.text[self.pos]
        if char in "\"'`":
            result = self.string()
        elif char == "[":
            result = self.array()
        elif char == "{":
            result = self.object()
        elif match := self.NUMBER.match(self.text, self.pos):
            self.pos = match.end()
            result = float(match[0]) if match[1] else int(match[0])
        elif match := self.NAME.match(self.text, self.pos):
            self.pos = match.end()
            constants = {"true": True, "false": False, "null": None}
            result = constants[match[0]] if match[0] in constants else Expression(match[0])
        else:
            raise NotLiteral
        self.skip_space()
        if self.pos < len(self.text) and self.text[self.pos] not in ",]}":
            raise NotLiteral  # opérateur, appel, fonction fléchée...
        return result

    def separator(self, closing: str) -> None:
        self.skip_space()
        if self.text[self.pos] == ",":
            self.pos += 1
        elif self.text[self.pos] != closing:
            raise NotLiteral

    def array(self) -> list:
        self.pos += 1
        items = []
        while True:
            self.skip_space()
            if self.text[self.pos] == "]":
                self.pos += 1
                return items
            if self.text.startswith("...", self.pos):
                self.pos += 3
                self.value()
            else:
                items.append(self.value())
            self.separator("]")

    def object(self) -> dict:
        self.pos += 1
        data = {}
        while True:
            self.skip_space()
            if self.text[self.pos] == "}":
                self.pos += 1
                return data
            if self.text.startswith("...", self.pos):
                self.pos += 3
                self.value()
            else:
                data.update(self.entry())
            self.separator("}")

    def entry(self) -> dict:
        if self.text[self.pos] in "\"'":
            key = self.string()
        else:
            match = self.KEY.match(self.text, self.pos)
            if not match:
                raise NotLiteral
            key = match[0]
            self.pos = match.end()
        self.skip_space()
        if self.text[self.pos] == ":":
            self.pos += 1
            return {key: self.value()}
        if self.text[self.pos] in ",}":
            return {key: Expression(key)}
        raise NotLiteral


def find_literals(text: str) -> list:
    """Plus grands littéraux du texte, en ignorant les chaînes et le code qui les entoure."""
    position, found = 0, []
    while position < len(text):
        char = text[position]
        parser = LiteralParser(text, position)
        try:
            if char in "[{":
                found.append(parser.array() if char == "[" else parser.object())
                position = parser.pos
                continue
            if char in "\"'`":
                parser.string()
                position = parser.pos
                continue
        except (NotLiteral, IndexError, ValueError):
            pass
        position += 1
    return found


def collect_questions(node, inherited: dict, sink: list, filename: str) -> None:
    if isinstance(node, dict):
        context = dict(inherited)
        for key in ("part", "passage", "groupId", "category", "difficulty", "id"):
            if isinstance(node.get(key), (str, int)) and not isinstance(node.get(key), bool):
                context[key] = node[key]
        if (
            isinstance(node.get("prompt"), str)
            and isinstance(node.get("choices"), list)
            and isinstance(node.get("answer"), int)
        ):
            fields = {k: v for k, v in node.items() if not isinstance(v, Expression)}
            sink.append({**context, **fields, "file": filename})
        for value in node.values():
            if isinstance(value, (dict, list)):
                collect_questions(value, context, sink, filename)
    elif isinstance(node, list):
        # Forme compacte : [id, difficulté, catégorie, énoncé, choix, réponse, explication]
        if (
            len(node) >= 6
            and all(isinstance(value, str) for value in node[:4])
            and isinstance(node[4], list)
            and isinstance(node[5], int)
        ):
            sink.append(
                {
                    **inherited,
                    "id": node[0],
                    "difficulty": node[1],
                    "category": node[2],
                    "prompt": node[3],
                    "choices": node[4],
                    "answer": node[5],
                    "explanation": node[6] if len(node) > 6 else "",
                    "file": filename,
                }
            )
            return
        for value in node:
            collect_questions(value, inherited, sink, filename)


def part_of(question: dict) -> int | None:
    if question.get("part"):
        return int(question["part"])
    for value in (question.get("id"), question.get("groupId")):
        if match := re.match(r"P(\d)", str(value or "")):
            return int(match[1])
    return None


def category_of(question: dict, part: int) -> str:
    if part == 7:
        return "comprehension"
    if part == 6:
        words = sum(len(choice.split()) for choice in question["choices"]) / 4
        is_blank = re.search(r"blank|___|\(\d\)", question["prompt"], re.IGNORECASE)
        if words > 4 or not is_blank:
            return "comprehension"  # insertion de phrase ou question sur le texte
        return "vocabulary" if re.search("語意|句意|字彙", question["explanation"]) else "grammar"
    return "vocabulary" if question.get("category") in VOCABULARY_CATEGORIES else "grammar"


def difficulty_of(question: dict) -> str:
    level = question.get("difficulty")
    if level is None:
        return "hard" if question["file"] in DEFAULT_HARD_FILES else "medium"
    return DIFFICULTIES[str(level)]


def shuffled(question_id: str, choices: list[str], answer: int) -> tuple[dict, str]:
    """La source met presque toujours la bonne réponse en A : on mélange de façon stable."""
    order = list(range(4))
    random.Random(question_id).shuffle(order)
    options = {letter: choices[index] for letter, index in zip("ABCD", order)}
    return options, "ABCD"[order.index(answer)]


def load_ocean(root: pathlib.Path) -> list[dict]:
    names = re.findall(r'src="\./(question-bank[^"?]*\.js)', (root / "index.html").read_text())
    raw: list[dict] = []
    for name in names:
        for literal in find_literals((root / name).read_text()):
            collect_questions(literal, {}, raw, name)

    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    questions, seen = [], set()
    group_sizes: collections.Counter = collections.Counter()
    for item in raw:
        part = part_of(item)
        key = (item.get("id"), item.get("groupId"), item["prompt"])
        if part not in (5, 6, 7) or key in seen:
            continue
        seen.add(key)
        group_sizes[item.get("groupId")] += 1
        # Certains jeux n'ont d'identifiant que pour le groupe : numéro dans le groupe.
        question_id = item.get("id") or f"{item['groupId']}-Q{group_sizes[item['groupId']]}"
        explanation = item.get("explanation") or ""
        options, correct = shuffled(question_id, item["choices"], item["answer"])
        questions.append(
            {
                "source_id": question_id,
                "part": part,
                "category": category_of({**item, "explanation": explanation}, part),
                "difficulty": difficulty_of(item),
                "prompt": item["prompt"],
                "options": options,
                "correct_choice": correct,
                "explanation": translations[question_id],
                "passage": item.get("passage") or None,
                "source": OCEAN_SOURCE,
            }
        )
    return questions


def ending(word: str) -> str:
    for suffix in ("ing", "ed", "ly", "s"):
        if word.endswith(suffix):
            return suffix
    return ""


def vocab_candidates(path: pathlib.Path) -> list[dict]:
    entries = [
        entry
        for entry in json.loads(path.read_text())
        if entry["star_rating"] >= 4
        and re.fullmatch(r"[a-z]{4,}", entry["english_word"])
        and len(entry["parts_of_speech"]) == 1
        and entry["parts_of_speech"][0] in {"noun", "verb", "adjective", "adverb"}
    ]
    pool = collections.defaultdict(list)
    for entry in entries:
        word = entry["english_word"]
        pool[(entry["parts_of_speech"][0], ending(word))].append((word, entry["category"]))

    rng = random.Random(20261106)
    rng.shuffle(entries)
    candidates, used_examples = [], set()
    for entry in entries:
        word, pos = entry["english_word"], entry["parts_of_speech"][0]
        rivals = [w for w, category in pool[(pos, ending(word))]
                  if category != entry["category"] and w != word]
        for example in entry["examples"]:
            sentence = example["english"].strip()
            pattern = re.compile(rf"\b{word}\b")
            if (
                len(pattern.findall(sentence)) != 1
                or sentence.startswith(word)
                or not sentence.endswith(".")
                or not 8 <= len(sentence.split()) <= 22
                or sentence in used_examples
                or len(rivals) < 3
            ):
                continue
            lowered = sentence.lower()
            distractors = rng.sample([w for w in rivals if w not in lowered], 3)
            used_examples.add(sentence)
            question_id = f"V-{word}"
            options, correct = shuffled(question_id, [word, *distractors], 0)
            score = entry["toeic_score_range"]
            candidates.append(
                {
                    "source_id": question_id,
                    "part": 5,
                    "category": "vocabulary",
                    "difficulty": "easy" if score.startswith("400") else
                    "medium" if score.startswith("600") else "hard",
                    "prompt": pattern.sub("_____", sentence),
                    "options": options,
                    "correct_choice": correct,
                    "explanation": f"Le mot attendu est « {word} ». Phrase complète : « {sentence} »",
                    "passage": None,
                    "source": VOCAB_SOURCE,
                }
            )
            break
    return candidates


def main() -> None:
    ocean = load_ocean(pathlib.Path(sys.argv[1]))
    candidates = vocab_candidates(pathlib.Path(sys.argv[2]))
    if "--candidates" in sys.argv:
        for q in candidates[:REVIEWED_CANDIDATES]:
            o = q["options"]
            print(f"{q['source_id']}|{q['correct_choice']}|{q['prompt']}|{o['A']}/{o['B']}/{o['C']}/{o['D']}")
        print(f"ocean={len(ocean)} candidats={len(candidates)}", file=sys.stderr)
        return

    # Seuls les candidats relus peuvent entrer dans la base.
    vocabulary = [
        q for q in candidates[:REVIEWED_CANDIDATES] if q["source_id"] not in REJECTED_VOCAB_IDS
    ]
    questions = ocean + vocabulary[:VOCAB_QUESTION_COUNT]
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(questions, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(questions)} questions écrites dans {OUTPUT}")
    print(sorted(collections.Counter(q["part"] for q in questions).items()))
    print(sorted(collections.Counter(q["correct_choice"] for q in questions).items()))
    print(sorted(collections.Counter(q["category"] for q in questions).items()))
    print(sorted(collections.Counter(q["difficulty"] for q in questions).items()))


if __name__ == "__main__":
    main()
