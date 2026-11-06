# API QCM TOEIC

API REST pour s'entraîner au TOEIC Reading (parties 5, 6 et 7), avec FastAPI et SQLite. L'examen complet compte 100 questions, notées sur 495. La partie Listening n'est volontairement pas couverte.

> Les questions sont **fictives** et ont été écrites pour le développement. Elles ne proviennent pas d'un vrai test TOEIC.

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

- Une session contient au maximum `question_count` questions : moins si le filtre en trouve moins.
- Chaque question accepte une seule réponse (A, B, C ou D), qui ne peut pas être modifiée : une seconde tentative renvoie `409`.
- Chaque bonne réponse vaut 4,95 points. Une réponse fausse ou absente vaut 0 point.
- `score` est la note obtenue et `max_score` la note maximale de la session : 495 pour 100 questions, 49,5 pour 10 questions.
- Cette note est linéaire. Le vrai TOEIC convertit les bonnes réponses avec son propre barème, donc la note ne prédit pas exactement un score officiel.

## Tests

```bash
pytest
```

## Remplacer les données fictives

Les questions se trouvent dans `app/seed.py`. Elles ne sont chargées que si la base est vide : après une modification, supprimez `toeic.db` (cela efface aussi l'historique des sessions).
