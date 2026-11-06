# Provenance des questions

`data/questions.json` est généré par `scripts/build_questions.py` à partir des sources ci-dessous. Chaque question indique sa source dans le champ `source`.

Ces questions sont de style TOEIC. Ce ne sont pas des questions officielles : TOEIC est une marque d'ETS, qui n'est liée ni à ce projet ni à ces sources.

## TOEIC Question Ocean

- **Source :** <https://github.com/kdeppaei/toeic-question-ocean>, commit `a940bb8b479ef4d06af468015d757041c3d2e457`
- **Licence :** MIT, Copyright (c) 2026 Chun-Hsiung Luo
- **Utilisation :** questions des parties 5, 6 et 7. Les choix ont été mélangés, les catégories et difficultés converties, et les explications traduites en français (`data/explanations_fr.json`).
- **Exclusion :** les questions de `modules/part5-exercise-guides.js` ne sont pas reprises, car elles viennent d'un site tiers.

```text
MIT License

Copyright (c) 2026 Chun-Hsiung Luo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## toeic-vocab-tw

- **Source :** <https://huggingface.co/datasets/kknono668/toeic-vocab-tw>, révision `7b1f881c2474bcb96fa8eacfbb8f63754c8cccef`
- **Licence :** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **Modifications :** les phrases d'exemple ont été transformées en questions à trous de partie 5. Le mot retiré est la bonne réponse, et les trois autres choix sont d'autres mots du jeu de données. Ces questions ont été relues et les ambiguës écartées.
- **Licence des questions dérivées :** les questions dont le champ `source` vaut `toeic-vocab-tw (CC BY-SA 4.0)` sont distribuées sous la même licence CC BY-SA 4.0.
