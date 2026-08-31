# Coach d'ouvertures FFE — POC étudiant

Ce dépôt contient un POC d'agent d'entraînement aux ouvertures d'échecs. L'utilisateur joue sur un échiquier Angular, puis l'agent :

1. valide la position FEN ;
2. consulte l'explorateur Lichess pour les coups théoriques ;
3. bascule sur Stockfish si la position n'est plus dans la théorie ;
4. ajoute du contexte issu d'un petit corpus Wikichess indexé dans Milvus ;
5. propose des vidéos YouTube et met les résultats en cache dans MongoDB.

Le workflow est orchestré avec LangGraph. Le POC reste utilisable sans clé YouTube et pendant le démarrage de Milvus grâce à des modes de démonstration explicitement signalés.

## Démarrage rapide

Prérequis : Docker et Docker Compose.

```bash
cp .env.example .env
docker compose up --build --detach --wait
docker compose exec backend python scripts/seed_milvus.py
```

Le premier chargement des données vectorielles télécharge le modèle d'embeddings léger (environ quelques minutes selon la connexion).

Accès :

- interface : <http://localhost:4200> ;
- documentation Swagger : <http://localhost:8000/docs> ;
- healthcheck : <http://localhost:8000/api/v1/healthcheck>.

Pour activer les résultats Lichess et YouTube réels, renseigner `LICHESS_API_TOKEN`
et/ou `YOUTUBE_API_KEY` dans `.env`, puis relancer le backend :

```bash
docker compose up --detach backend
```

Sans jeton Lichess, l'agent bascule explicitement sur Stockfish. Sans clé YouTube,
un lien de recherche de démonstration est retourné avec un avertissement visible.

## Démonstration suggérée

1. Avec `LICHESS_API_TOKEN`, ouvrir l'interface et analyser la position initiale : la branche `theory` doit proposer les coups Lichess.
2. Jouer `e4`, `e5`, `Cf3`, `Cc6`, `Fb5` et analyser : le nom de l'ouverture espagnole et son contexte doivent apparaître.
3. Charger une position hors ouverture, par exemple `8/8/8/8/8/4k3/8/4K3 w - - 0 1` : la branche `engine` doit afficher l'évaluation Stockfish.
4. Couper Milvus pour montrer le repli local explicite, puis le redémarrer.

## API principale

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/v1/healthcheck` | état de l'API et configuration |
| `GET` | `/api/v1/moves/{fen}` | coups théoriques Lichess |
| `GET` | `/api/v1/evaluate/{fen}` | analyse Stockfish |
| `POST` | `/api/v1/vector-search` | contexte d'ouverture |
| `POST` | `/vector-search` | alias demandé dans l'énoncé |
| `GET` | `/api/v1/videos/{opening}` | vidéos YouTube ou mode démo |
| `POST` | `/api/v1/agent/analyze` | workflow LangGraph complet |

Exemple recommandé, car la FEN dans un chemin doit sinon être encodée :

```bash
curl -X POST http://localhost:8000/api/v1/agent/analyze \
  -H 'Content-Type: application/json' \
  -d '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}'
```

## Développement et tests

Le projet Python utilise `uv`.

```bash
cd backend
uv sync --group dev
uv run ruff check .
uv run pytest -q
```

Compilation de l'interface dans sa version Node reproductible :

```bash
docker compose build frontend
```

Vérification de la configuration :

```bash
docker compose config --quiet
docker compose ps
```

## Organisation

```text
backend/
  app/api/          routes et injection de dépendances
  app/services/     Lichess, Stockfish, Milvus, MongoDB, YouTube
  app/workflows/    graphe LangGraph
  data/             corpus pédagogique de 10 ouvertures
  scripts/          chargement Milvus
  tests/            tests unitaires et API
frontend/           application Angular et ngx-chess-board
docs/               étude stratégique du système vidéo MCP
docker-compose.yml  orchestration et volumes persistants
```

## Limites du POC

- Le corpus est volontairement petit et doit être validé par un entraîneur.
- Les résultats Lichess et YouTube dépendent de services externes et de leurs identifiants.
- etcd et MinIO sont uniquement les dépendances internes standard de Milvus Standalone ; leurs ports ne sont pas exposés et l'application ne les appelle jamais directement.
- La recherche vidéo par position et timestamp est uniquement conçue dans l'étude, conformément à l'énoncé.
- Angular 13 est conservé pour la compatibilité avec la bibliothèque pédagogique `ngx-chess-board` 2.2.3 ; une migration ou un remplacement est recommandé avant une mise en production.

Voir [l'étude de faisabilité](docs/etude-faisabilite-video-mcp.md), [le rapport](rapport.md), [la checklist](checklist.md) et [les points bloquants](TODO.md).
