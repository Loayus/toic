# API QCM TOEIC

API REST pour s'entraîner au TOEIC Reading (parties 5, 6 et 7), avec FastAPI et SQLite. L'examen complet compte 100 questions, notées sur 495. La partie Listening n'est volontairement pas couverte.

> La base contient plus de 1000 questions **de style TOEIC** sous licence ouverte. Ce ne sont pas des questions officielles d'ETS. Voir [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Démarrage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Documentation interactive : <http://127.0.0.1:8000/docs>
- La base `toeic.db` est créée et remplie au premier lancement.
- Pour utiliser une autre base SQLite, définissez `TOEIC_DATABASE_URL`.

## Routes

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/questions` | Liste les questions (filtres : `part`, `category`, `difficulty`, `limit`, `offset`) |
| `GET` | `/questions/{id}` | Affiche une question |
| `POST` | `/questions/{id}/check` | Corrige une réponse sans l'enregistrer |
| `POST` | `/sessions` | Lance une session : 100 questions par défaut |
| `GET` | `/sessions/{id}` | Affiche une session et son avancement |
| `POST` | `/sessions/{id}/answers` | Enregistre une réponse et renvoie la correction |
| `GET` | `/sessions/{id}/results` | Affiche la note et la correction des questions répondues |
| `GET` | `/stats` | Affiche le taux de réussite global, par partie et par catégorie |

Valeurs des filtres :

- `part` : `5`, `6` ou `7`
- `category` : `grammar`, `vocabulary` ou `comprehension`
- `difficulty` : `easy`, `medium` ou `hard`

## Exemple

```bash
# Lancer un examen complet de 100 questions
curl -X POST localhost:8000/sessions

# Ou une session de 5 questions de la partie 5
curl -X POST localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"part": 5, "question_count": 5}'

# Répondre à une question
curl -X POST localhost:8000/sessions/1/answers \
  -H 'Content-Type: application/json' \
  -d '{"question_id": 3, "choice": "A"}'

# Voir le résultat
curl localhost:8000/sessions/1/results
```

## Règles

- Sans filtre, une session de 100 questions est un examen complet : 30 questions de partie 5, 16 de partie 6 et 54 de partie 7, avec des textes entiers.
- Une autre session contient au maximum `question_count` questions tirées une à une : moins si le filtre en trouve moins, et un texte peut n'y apparaître qu'avec une partie de ses questions.
- Toutes les corrections sont en français.
- Chaque question accepte une seule réponse (A, B, C ou D), qui ne peut pas être modifiée : une seconde tentative renvoie `409`.
- Chaque bonne réponse vaut 4,95 points. Une réponse fausse ou absente vaut 0 point.
- `score` est la note obtenue et `max_score` la note maximale de la session : 495 pour 100 questions, 49,5 pour 10 questions.
- Cette note est linéaire. Le vrai TOEIC convertit les bonnes réponses avec son propre barème, donc la note ne prédit pas exactement un score officiel.

## Tests

```bash
pytest
```

## Mettre à jour les questions

Les questions se trouvent dans `data/questions.json`, généré par `scripts/build_questions.py` à partir des sources et des traductions de `data/explanations_fr.json`. Elles ne sont chargées que si la base est vide : après une modification, supprimez `toeic.db` (cela efface aussi l'historique des sessions).
