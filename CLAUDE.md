# CLAUDE.md

Guide pour Claude Code (claude.ai/code) lorsqu'il travaille sur ce dépôt.

## Projet

**INTELCORP** — outil de renseignement sur les entreprises (Company Intelligence v2).
Application web Dash en un seul fichier : `intelcorp_v2.py`.

Fonctionnalités :
- Recherche d'entreprises en direct via l'API OpenCorporates (filtre par pays).
- Analyse IA d'une entreprise via Groq (`llama-3.3-70b-versatile`).
- Vérification des sanctions (entreprises et personnes) via l'API OpenSanctions.
- Rapport final : sanctions, signaux d'alerte, réputation, verdict.

L'interface et les textes sont en **français**.

## Lancer le projet

```bash
pip install -r requirements.txt
export GROQ_API_KEY="gsk_..."
python3 intelcorp_v2.py   # → http://127.0.0.1:8051 (mode debug)
```

Production (Heroku / plateforme compatible `Procfile`) :

```bash
gunicorn intelcorp_v2:server --bind 0.0.0.0:$PORT
```

## Structure de `intelcorp_v2.py`

- `FLAGS`, `NAMES` : drapeaux et noms des pays (codes ISO à 2 lettres).
- `CUSTOM_CSS` : CSS global injecté via `app.index_string` (thème sombre, variables CSS `--bg`, `--mono`, etc.).
- `live_search()` : recherche OpenCorporates.
- `ai_research()` : appel au modèle Groq.
- `check_sanctions()` / `check_persons()` : requêtes OpenSanctions.
- `app.layout` : mise en page Dash.
- Callbacks : `update_live` (résultats de recherche en direct) et `analyze` (rapport détaillé).
- `server = app.server` : point d'entrée WSGI pour gunicorn.

## Conventions

- Garder l'application dans un seul fichier, sauf demande contraire.
- Les clés API passent uniquement par des variables d'environnement (`GROQ_API_KEY`) ; ne jamais les écrire dans le code.
- Les appels HTTP externes utilisent un `timeout` et sont protégés par `try/except` pour que l'interface ne plante pas.
- Pas de tests automatisés pour l'instant : vérifier en lançant l'application.
