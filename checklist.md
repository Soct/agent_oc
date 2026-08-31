# Checklist de la fiche d'auto-évaluation

Légende : `[x]` vérifié dans le POC ; `[ ]` dépend d'un secret ou d'une
validation externe. Les nuances sont conservées pour ne pas déclarer comme
validé ce qui n'a pas pu l'être réellement.

## Système LangGraph, FastAPI, Milvus et MongoDB

- [x] **Graphe LangGraph correctement structuré** — nœuds distincts pour
  Lichess, Stockfish, Milvus, vidéos et formatage, avec branche conditionnelle.
- [x] **Traitement d'une FEN et choix de la source** — validation par
  `python-chess`, théorie si Lichess renvoie des coups, moteur sinon.
- [x] **Bonnes pratiques Python** — typage, schémas Pydantic, configuration,
  fonctions asynchrones ; `ruff` ne retourne aucune erreur.
- [x] **Séparation logique métier/API** — routes, services et workflow sont dans
  des modules différents.
- [x] **Données Wikichess prétraitées et découpées** — dix chunks pédagogiques
  courts, accompagnés de leur source.
- [x] **Embeddings appropriés stockés dans Milvus** — modèle multilingue léger,
  dimension 384 ; dix vecteurs chargés réellement.
- [x] **Recherche vectorielle pertinente** — « défense sicilienne plans des
  noirs » classe « Défense sicilienne » en premier via le backend `milvus`.
- [x] **Base vectorielle connectée à LangGraph** — le nœud
  `retrieve_context` appelle le service Milvus avant le formatage.
- [x] **Réponses de l'agent techniquement pertinentes** — sources, trace,
  évaluation et avertissements sont explicites.
- [ ] **Validation pédagogique finale des réponses** — une revue par un
  entraîneur FFE reste nécessaire avant usage avec des jeunes.
- [ ] **Intégration Lichess réelle retournant les coups théoriques** — le client,
  la route, le timeout et le test du chemin via doublure sont opérationnels ;
  l'API actuelle exige `LICHESS_API_TOKEN`, non fourni dans le projet.
- [x] **Intégration Stockfish** — le moteur évalue les positions hors théorie,
  conformément à la mission. La fiche parle de « positions théoriques », mais
  l'énoncé principal demande Stockfish lorsque la partie s'écarte de la théorie.
- [ ] **API YouTube retournant des vidéos réelles** — l'appel et le cache MongoDB
  sont implémentés, mais nécessitent `YOUTUBE_API_KEY`. Le mode démo est explicite.
- [x] **Choix d'outils pertinents** — Lichess pour la théorie, Stockfish pour
  l'évaluation, Milvus pour le contexte et YouTube pour la ressource vidéo.
- [x] **Timeouts et erreurs d'API gérés** — timeout configurable, exceptions
  contrôlées, avertissements et replis documentés.

## Docker Compose

- [x] **Tous les services démarrent** — frontend, backend, MongoDB, Milvus, etcd
  et MinIO ont passé leur healthcheck ensemble.
- [x] **Communication entre services** — FastAPI interroge réellement Milvus et
  Nginx relaie l'API depuis le frontend.
- [x] **Volumes persistants** — volumes nommés pour MongoDB, Milvus, etcd et
  MinIO.
- [x] **Variables d'environnement** — fichier `.env.example` et valeurs injectées
  dans Compose ; aucun secret codé en dur.
- [x] **Application accessible depuis l'extérieur** — Angular sur `localhost:4200`,
  FastAPI et Swagger sur `localhost:8000`.

Note d'architecture : etcd et MinIO sont les dépendances internes de Milvus
Standalone. Leurs ports ne sont pas publiés et ils n'ajoutent aucune fonction
visible par l'utilisateur.

## Interface Angular

- [x] **Échiquier intégré** — composant `ngx-chess-board` jouable.
- [x] **Positions FEN synchronisées** — la FEN est mise à jour après les coups et
  envoyée à l'agent.
- [x] **Recommandations affichées clairement** — branche, ouverture, coups,
  Stockfish, contexte et vidéos sont séparés.
- [x] **États de chargement et erreurs** — bouton désactivé pendant l'appel,
  indicateur de chargement, erreurs et avertissements visibles.
- [x] **Expérience utilisateur du POC** — interface responsive, lisible et build
  Angular validé. Une campagne utilisateur reste hors périmètre du POC.

## Étude de faisabilité vidéo/MCP

- [x] **Bénéfices du système d'analyse vidéo identifiés** — accès au passage
  exact, gain de temps, réutilisation du catalogue et pédagogie contextualisée.
- [x] **Limites techniques et métier évaluées** — précision visuelle, orientation,
  occlusions, coût, droits YouTube, faux positifs et maintenance.
- [x] **Architecture cohérente et réalisable** — ingestion, extraction, vision,
  board-to-FEN, index exact/vectoriel, API et serveur MCP sont schématisés.
- [x] **Estimations de coûts** — hypothèses explicites pour construction,
  exploitation, GPU et stockage.
- [x] **Alternatives et roadmap** — liens textuels, chapitrage manuel, catalogue
  FFE, pilote puis industrialisation conditionnelle.
- [x] **Livrables présentables et démontrables** — README de démarrage, API
  Swagger, scénario de démonstration, rapport, checklist et étude stratégique.

## Bilan

Les éléments non cochés ne sont pas des défauts cachés du code : ils nécessitent
des secrets externes ou une expertise humaine. Ils sont repris dans `TODO.md`.
