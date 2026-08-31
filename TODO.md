# Points bloquants ou dépendants d'un tiers

Le POC local possède un mode de démonstration et n'a pas de blocage de code connu. Les points suivants bloquent uniquement les fonctions externes ou une future mise en production :

- [ ] **Fournir une clé `YOUTUBE_API_KEY`** : sans identifiant Google, l'endpoint renvoie volontairement un lien de recherche de démonstration au lieu de métadonnées vidéo réelles. La clé ne peut pas être créée dans le dépôt.
- [ ] **Fournir un jeton `LICHESS_API_TOKEN`** : l'explorateur officiel demande désormais une authentification et répond `401` sans jeton. Le client Bearer est implémenté ; en son absence, le workflow bascule proprement sur Stockfish.
- [ ] **Valider les droits avant l'analyse vidéo avancée** : le téléchargement et le stockage de frames de vidéos YouTube sont interdits sans accord écrit préalable selon les politiques YouTube. Le prototype vision doit utiliser des originaux FFE/licenciés ou obtenir cet accord.
- [ ] **Faire valider le corpus par un entraîneur FFE** : les dix fiches sont suffisantes pour la preuve technique, mais leur publication à des jeunes nécessite une validation pédagogique externe.

Ces éléments ne bloquent ni le lancement Docker, ni Stockfish, ni le mode de recherche locale documenté. Le jeton bloque uniquement les résultats Lichess réels.
