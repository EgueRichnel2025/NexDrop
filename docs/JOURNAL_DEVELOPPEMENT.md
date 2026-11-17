# NexDrop — Journal de développement

Ce journal conserve une trace chronologique des travaux réellement effectués sur NexDrop.
Il complète le plan directeur : les décisions validées restent dans les documents de référence,
tandis que ce fichier décrit les changements, validations, limites et commits de chaque session.

## Règles de tenue du journal

- Ajouter une entrée à chaque session de développement significative.
- Consigner les décisions prises, fichiers créés/modifiés, migrations, tests et résultats.
- Ne jamais inscrire de secret, jeton, mot de passe, clé API ou valeur de `.env`.
- Distinguer explicitement les tâches terminées, en cours et reportées.
- Référencer les commits Git lorsqu'ils existent ; ne jamais inventer de commit.
- Mettre à jour ce journal avant de terminer chaque session.

---

## 2026-11-17 — Initialisation du journal et démarrage de la phase 4

### Contexte
- Phase 3 (modèle de données et persistance) est terminée.
- Base existante : 13 tables métier, migrations Alembic jusqu'à `041602a30cb7`.
- Phase 4 : comptes et authentification.
- Fournisseur d'e-mails transactionnels retenu : Brevo.
- Connexion sociale retenue : Google OpenID Connect.
- Les transferts LAN doivent rester utilisables sans compte.

### État initial vérifié
- Branche : `main`, synchronisée avec `origin/main` au dernier contrôle.
- Tests backend sans configuration de base PostgreSQL de test : `12 passed, 19 skipped`.
- Les 19 tests ignorés sont les tests d'intégration PostgreSQL ; ils ne constituent pas une validation complète de la base.
- Des fichiers non suivis sous `design/` étaient déjà présents avant cette session et doivent être préservés.

### Décisions de conception
- Hachage des mots de passe avec Argon2id.
- Jetons d'accès signés, à durée de vie courte.
- Jetons de renouvellement opaques, aléatoires, stockés sous forme de hash SHA-256 et à usage unique.
- Brevo sera appelé côté serveur ; les clés resteront dans les variables d'environnement locales.
- Google sera intégré via OpenID Connect ; les jetons Google seront validés côté serveur.
- Aucun secret réel ne sera ajouté au dépôt.

### Travaux de cette session
- Création du journal de développement.
- Inspection de l'architecture backend et des modèles `User`, `Session` et `SessionRefreshToken`.
- Préparation de la fondation technique d'authentification.

### Validations
- Baseline : `12 passed, 19 skipped`.
- Les tests PostgreSQL complets devront être relancés avec `NEXDROP_TEST_DATABASE_URL` pointant exclusivement vers `nexdrop_test`.

### À faire
- Ajouter les dépendances de sécurité et de transport HTTP.
- Implémenter les primitives de sécurité et leurs tests unitaires.
- Étudier et implémenter les adaptateurs Brevo et Google dans les étapes suivantes.
- Ajouter les migrations et endpoints d'inscription, vérification, connexion, rotation, révocation et récupération.
- Mettre à jour ce journal à chaque session.

### Commit
- Aucun commit créé dans cette session à ce stade.


## 2026-11-17 — Étape 4.1 : primitives de sécurité

### Modifications réalisées
- Ajout de `argon2-cffi`, `PyJWT[crypto]` et `httpx` aux dépendances runtime de `backend/pyproject.toml`.
- Mise à jour de `backend/uv.lock`.
- Création de `backend/src/nexdrop_api/auth/passwords.py` :
  - hachage Argon2id ;
  - vérification de mot de passe ;
  - détection des hashes à renouveler ;
  - bornes d'entrée : 12 caractères minimum et 1024 octets UTF-8 maximum.
- Création de `backend/src/nexdrop_api/auth/tokens.py` :
  - JWT HS256 avec validation stricte de l'algorithme, signature, issuer, audience, dates et type ;
  - secret de signature d'au moins 32 octets ;
  - durée de vie positive ;
  - génération de refresh tokens opaques à forte entropie ;
  - empreinte SHA-256 destinée au stockage, jamais le jeton brut.
- Ajout de `backend/tests/test_auth_primitives.py` couvrant les scénarios normaux et les erreurs.

### Validations exécutées
- `uv lock` : réussi.
- `uv sync` : réussi.
- `uv run ruff check .` : réussi.
- `uv run ruff format --check .` : réussi (32 fichiers).
- `uv run pytest -q` : **21 passed, 19 skipped**.
- Les 19 tests ignorés sont les tests d'intégration PostgreSQL, car `NEXDROP_TEST_DATABASE_URL` n'était pas défini dans cet environnement de test.
- Aucune clé Brevo ou Google n'a été ajoutée.

### État
- Primitives de sécurité : terminées et testées.
- Endpoints d'authentification, intégration Brevo, Google OAuth, migrations et gestion des sessions : à faire dans les prochaines étapes.

### Commit
- À renseigner après validation et publication Git de cette étape.

- Commit de l'étape : `6b3b689 feat(auth): add secure password and token primitives`.
