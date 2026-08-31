# Rapport de réalisation — Coach d'ouvertures FFE

Date de finalisation : 31 août 2026  
Nature : POC étudiant, simple, local et démontrable

## 1. Résultat obtenu

Le projet demandé est fonctionnel sous Docker Compose. Il fournit une interface
Angular avec échiquier interactif et une API FastAPI orchestrée par LangGraph.
À partir d'une position FEN, l'agent tente de récupérer la théorie auprès de
Lichess, utilise Stockfish en sortie de théorie ou si Lichess est indisponible,
recherche un contexte pédagogique dans Milvus et propose des ressources vidéo.

Le second livrable est une étude de faisabilité séparée. Le système avancé
d'analyse de vidéos et de recherche par FEN/timestamp y est conçu, mais n'a pas
été développé, conformément à l'énoncé.

## 2. Architecture réalisée

Le POC contient les composants suivants :

- `frontend` : Angular et `ngx-chess-board` ;
- `backend` : FastAPI, validation FEN, LangGraph et services métier ;
- `stockfish` : binaire installé dans l'image du backend ;
- `milvus` : recherche vectorielle du corpus pédagogique ;
- `mongodb` : cache des résultats vidéo ;
- `etcd` et `minio` : dépendances techniques internes de Milvus Standalone.

MinIO n'est pas une fonctionnalité ajoutée au produit. Milvus Standalone
l'utilise comme stockage objet et utilise etcd pour ses métadonnées. Aucun port
MinIO ou etcd n'est publié et aucun code applicatif ne les appelle directement.
Ce choix conserve un vrai service Milvus, explicitement attendu par l'énoncé,
sans ajouter une couche fonctionnelle inutile.

Le navigateur accède à Angular sur le port `4200`. Nginx sert l'application et
relaie `/api/` vers FastAPI. Le backend est également publié sur le port `8000`
pour Swagger et les démonstrations directes.

## 3. Backend FastAPI et logique échiquéenne

Le backend est organisé en trois couches :

- les routes HTTP dans `backend/app/api/` ;
- les services Lichess, Stockfish, Milvus et vidéos dans
  `backend/app/services/` ;
- le workflow dans `backend/app/workflows/`.

Les positions sont validées avec `python-chess`. Une FEN incorrecte produit une
réponse HTTP 422 explicite. Les appels externes possèdent un timeout configurable
et les pannes sont converties en réponses contrôlées ou en avertissements de
l'agent.

Routes réalisées :

| Méthode | Route | Fonction |
|---|---|---|
| `GET` | `/api/v1/healthcheck` | vérification du backend et de sa configuration |
| `GET` | `/api/v1/moves/{fen}` | coups théoriques de l'explorateur Lichess |
| `GET` | `/api/v1/evaluate/{fen}` | meilleur coup et évaluation Stockfish |
| `POST` | `/api/v1/vector-search` | recherche sémantique Milvus |
| `POST` | `/vector-search` | alias conforme au chemin de l'énoncé |
| `GET` | `/api/v1/videos/{opening}` | vidéos YouTube, cache ou mode démo |
| `POST` | `/api/v1/agent/analyze` | analyse complète par LangGraph |

## 4. Workflow LangGraph

Le graphe reste volontairement déterministe et lisible :

1. `identify_position` interroge Lichess avec la FEN ;
2. si des coups existent, la route `theory` est choisie ;
3. sinon `evaluate_with_stockfish` calcule une évaluation ;
4. `retrieve_context` interroge Milvus ;
5. `find_videos` cherche ou récupère les vidéos en cache ;
6. `format_answer` produit la réponse structurée et sa trace.

Le choix de ne pas ajouter un LLM distant est volontaire pour ce POC : aucun
budget ni clé supplémentaire n'est nécessaire, la réponse est reproductible et
chaque recommandation reste traçable vers un outil échiquéen spécialisé.

## 5. Intégration Lichess et Stockfish

Le service Lichess appelle l'hôte officiel actuel
`https://explorer.lichess.org/masters`. Il envoie un `User-Agent`, accepte un
jeton Bearer via `LICHESS_API_TOKEN`, trie les informations utiles et retourne
les coups avec leur popularité.

Pendant la validation, l'explorateur a répondu HTTP 401 sans jeton. Le code est
prêt pour le jeton, mais aucun secret n'est inventé ni écrit dans le dépôt. En
son absence, le graphe affiche un avertissement puis utilise Stockfish. Ce point
est listé dans `TODO.md`.

Stockfish est installé dans l'image backend. Pour une position hors théorie, il
retourne l'évaluation en centipions ou un mat, le meilleur coup en UCI et la
profondeur utilisée. Le test réel sur la finale de rois a retourné le meilleur
coup `e1f1` à la profondeur 12.

## 6. RAG Wikichess et Milvus

Un corpus pédagogique court de dix ouvertures a été préparé dans
`backend/data/wikichess_openings.json`. Chaque entrée contient un titre, un texte
concis et une URL source. Pour ce volume étudiant, une entrée constitue un chunk
cohérent ; un découpage plus fin aurait dégradé le contexte.

Le script `backend/scripts/seed_milvus.py` :

1. charge le corpus ;
2. génère des vecteurs de dimension 384 avec le modèle multilingue
   `paraphrase-multilingual-MiniLM-L12-v2` ;
3. crée la collection Milvus ;
4. insère les dix chunks.

Le chargement réel a réussi : `10 chunks indexés dans Milvus`. Une requête
« défense sicilienne plans des noirs » a utilisé le backend `milvus` et placé
« Défense sicilienne » en premier résultat.

Un repli lexical local est conservé et clairement nommé `local-fallback`. Il
permet une démonstration dégradée si Milvus n'est pas encore prêt, sans prétendre
qu'il s'agit alors d'une recherche vectorielle.

## 7. Vidéos YouTube et MongoDB

Le service vidéo utilise l'API YouTube lorsque `YOUTUBE_API_KEY` est fournie. Les
métadonnées obtenues sont mises en cache dans MongoDB afin de limiter les appels
et de rendre les résultats suivants plus rapides.

Sans clé, le POC renvoie un lien de recherche YouTube pertinent et un
avertissement visible `catalogue-demo`. Ce mode ne fabrique pas de métadonnées et
ne masque pas l'absence d'intégration réelle. La clé externe est inscrite dans
`TODO.md`.

## 8. Interface Angular

L'interface comporte :

- un échiquier jouable `ngx-chess-board` ;
- la FEN courante synchronisée après chaque coup ;
- une action d'analyse ;
- l'affichage de la branche choisie, de l'ouverture, des coups, de l'évaluation,
  du contexte et des vidéos ;
- des états de chargement, des messages d'erreur et des avertissements ;
- une mise en page responsive pour ordinateur et écran étroit.

La version `ngx-chess-board` 3.0.0 publiée au moment du développement ne
contenait pas le paquet compilé attendu. La version stable 2.2.3 a donc été
retenue avec Angular 13, conformément à ses peer dependencies. Node 16 est figé
dans le Dockerfile pour rendre le build reproductible.

Le build Angular Docker a réussi. Le bundle principal fait environ 412 kB brut
et 110 kB en transfert estimé.

## 9. Docker Compose et configuration

La pile utilise des images et versions figées. Les paramètres applicatifs sont
centralisés dans `.env.example`. Quatre volumes nommés rendent persistantes les
données MongoDB, Milvus, etcd et MinIO.

Lors du premier lancement, le proxy HTTP injecté par l'environnement Docker
interceptait les communications gRPC internes de Milvus et répondait 502. La
solution a été de neutraliser les variables de proxy uniquement dans Milvus,
etcd et MinIO, qui n'ont aucun appel Internet à effectuer. La pile complète est
ensuite passée à l'état sain.

État final vérifié :

- backend : sain ;
- frontend : sain ;
- MongoDB : sain ;
- Milvus : sain ;
- etcd : sain ;
- MinIO : sain.

## 10. Étude vidéo et MCP

Le document `docs/etude-faisabilite-video-mcp.md` couvre :

- les bénéfices attendus et les cas d'usage ;
- les limites de reconnaissance, de position, de timestamp et de droits ;
- un schéma d'architecture MCP ;
- le pipeline vidéo vers détection d'échiquier puis board-to-FEN ;
- un contrat d'outil MCP ;
- le stockage exact et la recherche approchée ;
- la sécurité, les droits et la conformité YouTube ;
- les coûts de construction et d'exploitation ;
- les alternatives, métriques, jalons et critères de décision.

La recommandation est un `go` conditionnel : commencer avec des vidéos FFE ou
explicitement licenciées, effectuer un pilote limité et ne généraliser qu'après
mesure de la précision FEN et de la qualité des timestamps.

## 11. Vérifications effectuées

| Vérification | Résultat |
|---|---|
| `uv run pytest -q` | 7 tests réussis |
| `uv run ruff check .` | aucune erreur |
| `docker compose config --quiet` | configuration valide |
| build image backend | réussi |
| build Angular dans Docker | réussi |
| démarrage `docker compose --wait` | six services sains |
| healthcheck FastAPI | HTTP 200 |
| page Angular | HTTP 200 |
| chargement Milvus | 10 chunks |
| recherche vectorielle réelle | backend `milvus`, Sicilienne classée première |
| branche Stockfish réelle | réponse structurée, profondeur 12 |
| branche Lichess sans secret | repli contrôlé, jeton signalé manquant |

Le seul avertissement Python est une dépréciation future interne à LangGraph,
sans impact sur le POC. L'audit npm signale 48 vulnérabilités dans l'ancienne
chaîne Angular transitive (5 faibles, 13 modérées, 29 hautes, 1 critique). Elles
ne bloquent pas la démonstration locale, mais Angular et la bibliothèque
d'échiquier devront être migrés avant toute mise en production.

## 12. Limites et suite

Les points réellement dépendants d'un tiers sont volontairement regroupés dans
`TODO.md` : jeton Lichess, clé YouTube, droits sur les vidéos avancées et
validation pédagogique du corpus. Aucun blocage de code connu n'empêche le
lancement local ou la démonstration de Stockfish et Milvus.

Le projet a été réalisé sans utiliser de commande Git, conformément à la
consigne reçue.
