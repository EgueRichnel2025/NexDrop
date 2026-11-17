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
