# Coach d'ouvertures FFE

POC d’un agent de coaching des ouvertures d’échecs. L’utilisateur joue sur un échiquier Angular basé sur [`ngx-chess-board`](https://github.com/OpenClassrooms-Student-Center/material-chessboard), puis l’agent analyse la position et construit une réponse pédagogique :

1. valide la position FEN ;
2. consulte l’explorateur Lichess pour reconnaître une position théorique ;
3. propose les coups théoriques et des parties de référence ;
4. utilise Stockfish lorsque la position est hors théorie ou que Lichess est indisponible ;
5. récupère un contexte d’ouverture depuis Milvus, avec recherche locale de secours ;
6. propose des ressources vidéo YouTube, avec cache MongoDB et catalogue de démonstration.

Le workflow de l’agent est orchestré avec LangGraph. Il enchaîne l’identification de la position, le choix entre théorie et moteur, la récupération de contexte, la recherche de vidéos et la mise en forme de la réponse. Le projet reste démontrable sans clé YouTube, sans jeton Lichess et pendant l’indisponibilité temporaire de Milvus.

## Fonctionnement de l’agent

```text
Position FEN
    ↓
Identification via Lichess
    ├─ position théorique → coups suggérés et parties de référence
    └─ position hors théorie → évaluation Stockfish et meilleur coup
    ↓
Contexte d’ouverture (Milvus, puis recherche locale si nécessaire)
    ↓
Ressources vidéo (YouTube, cache MongoDB ou catalogue démo)
    ↓
Réponse pédagogique avec résumé, avertissements et trace du workflow
```

L’agent renvoie notamment la route choisie (`theory` ou `engine`), un résumé en français, les coups suggérés, l’évaluation éventuelle, le contexte, les vidéos, les avertissements et la trace des étapes exécutées.

## Prérequis

- Docker et Docker Compose ;
- `uv` pour le développement backend ;
- Node.js 16 et npm si le frontend doit être compilé hors Docker.

## Démarrage recommandé

À la racine du dépôt :

```bash
cp .env.example .env
docker compose up --build --detach --wait
docker compose exec backend python scripts/seed_milvus.py
```

Le chargement initial du modèle d’embeddings peut prendre quelques minutes et nécessite un accès réseau. La commande `seed_milvus.py` recrée la collection configurée puis indexe le corpus présent dans `backend/data/wikichess_openings.json`.

Accès par défaut :

- interface : <http://localhost:4200> ;
- API : <http://localhost:8000> ;
- documentation Swagger : <http://localhost:8000/docs> ;
- healthcheck : <http://localhost:8000/api/v1/healthcheck>.

Les ports sont modifiables avec `BACKEND_PORT` et `FRONTEND_PORT` dans `.env`.

## Configuration

Le fichier `.env.example` contient les valeurs par défaut. Les variables les plus importantes sont :

| Variable | Rôle |
| --- | --- |
| `LICHESS_API_TOKEN` | active les résultats réels de l’explorateur Lichess ; sans jeton, l’analyse bascule vers Stockfish |
| `YOUTUBE_API_KEY` | active la recherche YouTube réelle ; sans clé, un lien de recherche de démonstration est renvoyé |
| `STOCKFISH_DEPTH` | profondeur d’analyse Stockfish, 12 par défaut |
| `MONGODB_URL` / `MONGODB_DATABASE` | configuration du cache vidéo |
| `MILVUS_URI` / `MILVUS_COLLECTION` | configuration de la recherche vectorielle |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSION` | modèle et dimension des embeddings utilisés pour Milvus |
| `CORS_ORIGINS` | origines autorisées par l’API |

Après modification de `.env`, redémarrer le backend :

```bash
docker compose up --detach backend
```

## API

Toutes les routes versionnées sont préfixées par `/api/v1`.

| Méthode | Route | Fonction |
| --- | --- | --- |
| `GET` | `/api/v1/healthcheck` | état de l’application et de ses dépendances |
| `GET` | `/api/v1/moves/{fen}` | coups théoriques et parties Lichess pour une FEN |
| `GET` | `/api/v1/evaluate/{fen}` | évaluation Stockfish d’une FEN |
| `POST` | `/api/v1/vector-search` | recherche de contexte dans Milvus ou en local |
| `POST` | `/vector-search` | alias non versionné de la recherche de contexte |
| `GET` | `/api/v1/videos/{opening}` | ressources vidéo, cache MongoDB ou catalogue démo |
| `POST` | `/api/v1/agent/analyze` | exécution complète de l’agent et réponse pédagogique |

Exemple d’analyse complète :

```bash
curl -X POST http://localhost:8000/api/v1/agent/analyze \
  -H 'Content-Type: application/json' \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'
```

Exemple de recherche de contexte :

```bash
curl -X POST http://localhost:8000/api/v1/vector-search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Défense sicilienne","limit":3}'
```

## Développement et tests

### Backend

```bash
cd backend
uv sync --group dev
uv run ruff check .
uv run pytest -q
```

Le backend nécessite Python `>=3.12,<3.14`. Le conteneur installe Stockfish et lance Uvicorn sur le port 8000.

### Frontend

```bash
cd frontend
npm ci
npm run build
```

Le frontend utilise Angular 13 et `ngx-chess-board` `2.2.3`. L’image Docker compile l’application puis la sert avec Nginx ; Nginx relaie `/api/` vers le service backend. Le raisonnement et l’orchestration de l’agent restent côté backend.

## Arborescence

```text
backend/
  app/api/          routes et dépendances FastAPI
  app/services/     Lichess, Stockfish, Milvus, MongoDB et YouTube
  app/workflows/    workflow LangGraph d’analyse
  data/             corpus d’ouvertures Wikichess
  scripts/          indexation du corpus Milvus
  tests/            tests backend
frontend/           application Angular et échiquier ngx-chess-board
docker-compose.yml  backend, frontend, MongoDB et Milvus
.env.example        configuration locale documentée
```

## Limites connues

- Les résultats Lichess réels nécessitent un `LICHESS_API_TOKEN`.
- Les vidéos YouTube réelles nécessitent une `YOUTUBE_API_KEY`; sinon le service renvoie un lien de recherche de démonstration.
- Si Milvus est vide ou indisponible, la recherche bascule automatiquement sur le corpus local.
- Le corpus d’ouvertures doit encore être validé sur le plan pédagogique avant une utilisation de production.
- L’analyse vidéo avancée et l’extraction de positions depuis des vidéos nécessitent des contenus dont les droits sont autorisés ; cette fonctionnalité n’est pas implémentée dans le POC actuel.

## Références

- [Dépôt de l’échiquier Angular](https://github.com/OpenClassrooms-Student-Center/material-chessboard)
- [API Lichess](https://lichess.org/api)
- [API YouTube Data](https://developers.google.com/youtube/v3?hl=fr)
- [Données Wikichess utilisées](https://ficgs.com/wikichess_1.html)
- [FEN](https://www.chess.com/terms/fen-chess)
- [Étude vidéo MCP](livrable/rapport-etude-video-mcp.md)
