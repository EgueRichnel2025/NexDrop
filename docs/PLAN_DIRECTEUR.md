# NexDrop — Plan directeur complet

**Produit :** NexDrop
**Slogan :** Transfer without limits.
**Document :** Plan directeur de référence
**Version :** 1.0
**Plateforme initiale :** Windows 11 x64
**Ordre de priorité :** Backend serveur → moteur de transfert Rust → application desktop → Internet et mise en production.

> **Principe directeur : Local first. Cloud when necessary.**

Ce document rassemble toutes les phases prévues pour construire NexDrop, de la fondation technique jusqu'aux évolutions après la première version publique. Il remplace l'ancienne roadmap comme référence principale. Les phases sont numérotées pour permettre de suivre précisément l'avancement.

Les statuts indiquent uniquement ce qui a été vérifié dans le dépôt et sur l'environnement de développement. Une phase ne sera déclarée terminée qu'après validation de ses critères de sortie.

---

# Vue d'ensemble

| Domaine | Phases | Résultat attendu |
|---|---:|---|
| Cadrage et fondations | 0–2 | Architecture initiale, dépôt et socle backend |
| Backend serveur | 3–12 | API, données, comptes, appareils, transferts, plans, signalisation et sécurité |
| Moteur natif | 13–16 | Moteur Rust fiable, LAN, reprise et intégrité |
| Application desktop | 17–19 | Interface Windows et intégration des parcours |
| Transfert Internet et lancement | 20–23 | P2P, relais chiffré, validation, publication et exploitation |
| Évolutions ultérieures | 24 | Autres plateformes et offres avancées |

## État actuel

- **Phase 0 — Fondation du dépôt : partiellement réalisée.**
- **Phase 1 — Architecture et spécifications : partiellement réalisée.**
- **Phase 2 — Fondation du backend : terminée et vérifiée.**
- **Prochaine phase : Phase 4 — Comptes et authentification.**

Le frontend Tauri/React existe encore sous forme de projet initial. Il ne faut pas confondre cette présence avec une interface NexDrop terminée.

---

# A. Cadrage et fondations

## Phase 0 — Dépôt, environnement et outillage

**Objectif :** disposer d'un environnement de développement reproductible et d'un dépôt propre.

Travaux :
- Initialiser et organiser le dépôt GitHub NexDrop.
- Mettre en place Tauri 2, React, TypeScript, Vite et pnpm.
- Installer et vérifier Rust, Cargo, MSVC et Windows SDK.
- Installer Python 3.12 et uv pour le backend.
- Organiser les caches et les environnements sur le disque D:.
- Configurer les fichiers ignorés, les conventions Git et les validations.
- Maintenir les documentations produit et technique.

**Critères de sortie :** environnement reproductible, builds frontend et Rust validés, historique Git propre, structure de dépôt cohérente.

**Statut : PARTIELLEMENT RÉALISÉE.** Le dépôt, l'outillage principal et les premiers contrôles sont en place. L'identité complète de l'application desktop et son interface restent à construire.

## Phase 1 — Architecture produit et spécifications techniques

**Objectif :** décider ce que le système doit faire et définir les frontières entre ses composants avant de multiplier les fonctionnalités.

Travaux :
- Formaliser les parcours LAN sans compte et Internet avec compte.
- Définir les rôles de l'API, de PostgreSQL, du moteur Rust, de Tauri et du relais.
- Décrire les entités métier et leurs relations.
- Définir les états et transitions autorisés d'un transfert.
- Définir le manifeste des fichiers et dossiers.
- Définir les exigences de sécurité, de confidentialité et de consentement du destinataire.
- Étudier puis consigner les décisions d'architecture : découverte LAN, transport Internet, traversée NAT, identité des pairs, cryptographie, persistance locale et prestataire de paiement.
- Définir les conventions API, erreurs, logs, tests et migrations.

**Critères de sortie :** les contrats et décisions structurantes sont documentés ; aucun choix critique de protocole ou de sécurité n'est improvisé au milieu d'une fonctionnalité.

**Statut : PARTIELLEMENT RÉALISÉE.** Les principes et les frontières générales sont documentés. Plusieurs décisions détaillées restent à prendre.

## Phase 2 — Fondation du backend serveur

**Objectif :** disposer d'un service FastAPI démarrable, testable et raccordé à une vraie base PostgreSQL.

Travaux :
- Projet Python isolé avec uv et verrouillage des dépendances.
- FastAPI et Uvicorn.
- Configuration centralisée avec Pydantic Settings.
- SQLAlchemy asynchrone et Psycopg 3.
- Sessions de base de données et cycle de vie du moteur.
- PostgreSQL 17 local via Docker Compose.
- Secrets locaux dans `backend/.env`, exclus de Git.
- Contrôles de santé liveness et readiness.
- Configuration de la boucle asyncio compatible avec Psycopg sous Windows.
- Socle Alembic et première révision de suivi.
- Tests automatisés et documentation de démarrage.

**Critères de sortie :** connexion PostgreSQL réelle, endpoint readiness positif avec la base disponible, migrations exécutables, tests et contrôles qualité réussis.

**Statut : TERMINÉE.** Socle validé sur la machine Windows ; la révision initiale Alembic est appliquée.

---

# B. Backend serveur — plan prioritaire

## Phase 3 — Modèle de données et persistance métier

**Objectif :** concevoir le schéma relationnel NexDrop avant d'implémenter les fonctionnalités métier.

Travaux :
- Définir les utilisateurs et les informations de compte.
- Définir les appareils associés aux utilisateurs et leur identité.
- Définir les sessions et les mécanismes de révocation.
- Définir les transferts et leurs participants.
- Définir les événements et l'historique des transferts.
- Définir les invitations, codes et liens de transfert.
- Définir les offres, abonnements, paiements et écritures de quota.
- Définir clés primaires, clés étrangères, contraintes, index, unicité et suppressions.
- Définir les règles de conservation, d'expiration et d'anonymisation des données.
- Créer les modèles SQLAlchemy, les migrations Alembic et les tests de persistance.
- Vérifier les transactions, contraintes et accès concurrents.

**Critères de sortie :** schéma documenté, migrations reproductibles, contraintes testées, relations cohérentes et données persistées correctement.

**Statut : TERMINÉE.** Modèle relationnel V1 validé ; 13 modèles SQLAlchemy ; migrations `8d9e28ddd1c7` et `041602a30cb7` appliquées ; 31 tests réussis sur PostgreSQL réel, dont un test de concurrence à deux sessions ; aucune dérive Alembic. Les décisions ouvertes Pro, prestataire de paiement, conservation et identité cryptographique restent affectées à leurs phases fonctionnelles respectives.

## Phase 4 — Comptes et authentification

**Objectif :** permettre à un utilisateur de posséder un compte NexDrop et d'accéder de manière sécurisée aux fonctions Internet.

Travaux :
- Inscription et connexion.
- Vérification de l'adresse e-mail et récupération du compte.
- Stockage sécurisé des mots de passe avec un algorithme adapté.
- Émission, renouvellement, rotation et révocation des jetons de session.
- Déconnexion d'une session ou de toutes les sessions.
- Protection contre force brute, énumération de comptes et abus.
- Limitation de débit sur les endpoints sensibles.
- Tests des cas d'erreur et des scénarios de sécurité.

**Critères de sortie :** cycle de compte complet, sessions révocables, secrets non exposés et contrôles d'accès validés.

## Phase 5 — Appareils, identité et confiance

**Objectif :** gérer les ordinateurs et appareils qui utilisent NexDrop, sans rendre un compte obligatoire pour le LAN.

Travaux :
- Enregistrement d'un appareil pour un utilisateur authentifié.
- Identifiant stable, nom, plateforme et informations techniques minimales.
- Association et dissociation d'un appareil.
- Liste des appareils connus et dernière activité.
- Révocation d'un appareil perdu ou non reconnu.
- Gestion des clés ou justificatifs d'identité des appareils.
- Différencier appareil local non connecté à un compte et appareil enregistré.
- Préparer les mécanismes de confiance entre pairs.

**Critères de sortie :** les appareils Internet sont identifiables et révocables ; les transferts LAN restent possibles sans inscription.

## Phase 6 — Orchestration des transferts et consentement

**Objectif :** construire le cœur métier des transferts côté serveur, sans faire transiter les fichiers par l'API.

Travaux :
- Création d'un transfert et identification de son initiateur.
- Enregistrement des participants et destinataires.
- Gestion des invitations et de leur expiration.
- Acceptation ou refus explicite du destinataire.
- Transitions d'état contrôlées et atomiques.
- Annulation et expiration d'un transfert.
- Codes et liens de transfert avec durée de validité.
- Idempotence des opérations qui peuvent être répétées.
- Historique des changements d'état.
- Séparation stricte des métadonnées et du contenu des fichiers.

**Critères de sortie :** cycle de vie métier cohérent, consentement traçable et aucune donnée de fichier ne transite par l'API de contrôle.

## Phase 7 — Offres, droits et quotas

**Objectif :** faire respecter les règles commerciales depuis le backend, et non depuis l'interface.

Travaux :
- Définir les droits associés à Free, Pro et Business.
- Maintenir le LAN gratuit et illimité sans compte.
- Appliquer la limite Free de 10 Go par transfert Internet.
- Définir les limites Pro après décision produit.
- Vérifier les droits au moment de créer et d'exécuter un transfert.
- Comptabiliser les usages sans double comptage.
- Gérer les opérations concurrentes et les tentatives de contournement.
- Enregistrer les décisions de quota et leur justification.

**Critères de sortie :** les limites sont centralisées, atomiques, testées et impossibles à contourner par une simple modification du frontend.

## Phase 8 — Abonnements et paiements

**Objectif :** gérer le passage à Pro et les futurs contrats Business.

Travaux :
- Choisir le prestataire de paiement et documenter la décision.
- Créer et gérer les abonnements.
- Traiter activation, renouvellement, échec de paiement, annulation et expiration.
- Recevoir et vérifier les webhooks.
- Rendre le traitement des événements de paiement idempotent.
- Conserver les références et états nécessaires à la réconciliation.
- Synchroniser les abonnements avec les droits et quotas.
- Prévoir les factures et l'historique des opérations selon le prestataire retenu.

**Critères de sortie :** les changements de paiement et d'abonnement sont fiables, vérifiables et cohérents avec les droits effectifs du compte.

## Phase 9 — Signalisation et négociation des connexions Internet

**Objectif :** permettre à deux appareils autorisés de négocier une connexion directe sans envoyer le contenu des fichiers au backend.

Travaux :
- Émettre des tickets de connexion à durée courte.
- Vérifier l'identité et les droits des participants.
- Échanger les informations nécessaires à la négociation du canal.
- Gérer l'expiration, l'annulation et la révocation.
- Limiter les abus et les tentatives de connexion non autorisées.
- Intégrer le protocole de transport choisi dans une ADR.
- Séparer les messages temporaires de signalisation des données persistantes.

**Critères de sortie :** deux appareils autorisés peuvent négocier une connexion ; l'API ne devient pas un proxy de données.

## Phase 10 — Allocation et service relais

**Objectif :** fournir un chemin de secours lorsque la connexion directe est impossible.

Travaux :
- Définir l'architecture et le protocole du relais.
- Allouer et libérer des ressources de relais.
- Gérer tickets, autorisations, durée de vie et limites de débit.
- Transmettre uniquement des flux chiffrés de bout en bout.
- Ne jamais transmettre de clé de déchiffrement au relais.
- Gérer interruptions, saturation, expiration et abus.
- Mesurer capacité, disponibilité, trafic et coûts d'exploitation.

**Critères de sortie :** le relais fonctionne comme un transport opaque de secours ; les fichiers restent chiffrés de bout en bout.

## Phase 11 — Historique, notifications, audit et administration

**Objectif :** fournir les services transversaux nécessaires à l'exploitation et à la compréhension du produit.

Travaux :
- Historique serveur des transferts Internet.
- Événements et journaux d'audit.
- Notifications liées aux transferts, comptes et abonnements.
- Préférences de notification.
- Outils d'administration strictement autorisés.
- Recherche et diagnostic des incidents sans exposer les contenus privés.
- Journalisation structurée et corrélation des requêtes.
- Politiques de conservation et suppression des données.

**Critères de sortie :** opérations sensibles traçables, événements exploitables et données personnelles protégées.

## Phase 12 — Sécurisation, tests et préparation du backend à la production

**Objectif :** rendre le backend robuste avant de dépendre de lui depuis les clients desktop.

Travaux :
- Revue du modèle de menaces et des autorisations.
- Vérification des contrôles d'accès et des frontières entre comptes.
- Tests d'intégration sur PostgreSQL réel.
- Tests de concurrence et d'idempotence.
- Tests de charge sur les endpoints importants.
- Gestion des secrets et configuration de production.
- TLS, politiques CORS adaptées, en-têtes et limitation de débit.
- Sauvegardes PostgreSQL et tests de restauration.
- Conteneurisation de production et séparation des environnements.
- CI, contrôles de dépendances et analyse de vulnérabilités.
- Logs, métriques, alertes et procédures d'incident.
- Documentation d'exploitation et de déploiement.

**Critères de sortie :** backend déployable, surveillable, sauvegardé, restaurable et validé par sa suite de tests.

**JALON : BACKEND SERVEUR COMPLET.** Les phases 3 à 12 constituent le périmètre backend prioritaire. Le passage au moteur Rust ne signifie pas que le développement backend est définitivement terminé : les corrections et évolutions continueront avec les besoins d'intégration.

---

# C. Moteur natif et transferts locaux

## Phase 13 — Fondation du moteur de transfert Rust

**Objectif :** construire un moteur natif indépendant de l'interface Tauri.

Travaux :
- Définir les modèles de domaine, identifiants et erreurs.
- Définir les états et transitions des transferts.
- Créer les manifestes de fichiers et de dossiers.
- Parcourir les dossiers de manière sûre.
- Lire et écrire les fichiers par blocs de taille bornée.
- Préserver l'arborescence relative.
- Calculer les empreintes et vérifier l'intégrité.
- Gérer concurrence et mémoire de manière bornée.
- Préparer la persistance locale des transferts interrompus.
- Écrire des tests unitaires et d'intégration indépendants de l'interface.

**Critères de sortie :** moteur testable sans UI, lecture/écriture en flux, chemins sûrs et intégrité vérifiée.

## Phase 14 — Découverte LAN et appairage local

**Objectif :** permettre aux ordinateurs proches de se découvrir sans connexion à un compte.

Travaux :
- Choisir le mécanisme de découverte LAN et ses limites.
- Détecter les appareils disponibles sur le réseau local.
- Ajouter un code de connexion manuel.
- Générer et lire des QR codes de connexion.
- Vérifier l'identité du pair et établir un canal local.
- Permettre au destinataire d'accepter ou refuser.
- Gérer plusieurs interfaces réseau et les changements de réseau.
- Éviter d'exposer inutilement les appareils sur des réseaux non fiables.

**Critères de sortie :** deux ordinateurs Windows peuvent se découvrir et s'appairer sur un réseau local sans compte.

## Phase 15 — Transfert LAN complet

**Objectif :** réaliser les transferts locaux de bout en bout.

Travaux :
- Transférer un fichier, plusieurs fichiers et des dossiers.
- Envoyer des fichiers volumineux sans chargement complet en RAM.
- Écrire en blocs et vérifier les tailles et empreintes.
- Respecter le consentement et le dossier de destination du destinataire.
- Gérer les collisions de noms et les politiques d'écrasement.
- Afficher progression, vitesse, taille et état.
- Gérer plusieurs transferts avec concurrence contrôlée.
- Éviter tout passage par le backend pour les données LAN.

**Critères de sortie :** deux ordinateurs peuvent transférer directement des fichiers et dossiers sur LAN avec intégrité validée.

## Phase 16 — Reprise, fiabilité et performances

**Objectif :** rendre les transferts robustes face aux interruptions et aux grands volumes.

Travaux :
- Pause, reprise et annulation.
- Reprise après fermeture et redémarrage de l'application.
- Reprise après coupure ou changement de réseau.
- Détection des modifications du fichier source.
- Vérification des blocs déjà reçus.
- Gestion de l'espace disque insuffisant et des permissions.
- Écritures temporaires et finalisation sûre.
- Tests sur fichiers très volumineux et arborescences profondes.
- Mesure de mémoire, débit, CPU et nombre de connexions.
- Ajustement de la concurrence et de la taille des blocs.

**Critères de sortie :** aucune réussite déclarée sans intégrité vérifiée ; les interruptions ne produisent pas de corruption silencieuse.

---

# D. Application desktop Windows

## Phase 17 — Interface de base et système visuel

**Objectif :** construire l'application NexDrop utilisable, accessible et cohérente.

Travaux :
- Remplacer complètement l'écran de démarrage généré.
- Concevoir la navigation et la structure générale.
- Définir les composants réutilisables et les jetons visuels.
- Implémenter thèmes clair et sombre.
- Implémenter français et anglais.
- Créer les états vides, erreurs, chargements et notifications.
- Préparer les fenêtres de sélection de fichiers et dossiers.
- Définir les contrats TypeScript/Tauri.
- Vérifier l'accessibilité clavier et lecteur d'écran.

**Critères de sortie :** application desktop identifiable, cohérente, localisée et prête à intégrer des fonctionnalités réelles.

## Phase 18 — Parcours LAN dans l'interface

**Objectif :** rendre les transferts locaux accessibles à l'utilisateur final.

Travaux :
- Écran d'accueil et sélection de fichiers/dossiers.
- Affichage des appareils découverts.
- Connexion par code et QR.
- Écran de demande entrante et consentement du destinataire.
- Affichage de progression, vitesse, pause, reprise et annulation.
- Historique local et détails des transferts.
- Gestion des erreurs et récupération guidée.
- Intégration typée avec les commandes et événements Rust/Tauri.

**Critères de sortie :** les parcours LAN complets fonctionnent dans l'application, sans données fictives présentées comme réelles.

## Phase 19 — Comptes, appareils et fonctions Internet dans le desktop

**Objectif :** relier l'application desktop au backend serveur.

Travaux :
- Inscription, connexion et récupération du compte.
- Gestion sécurisée de la session côté client.
- Enregistrement et gestion des appareils.
- Création et réception de transferts Internet.
- Gestion des liens, codes et invitations.
- Historique serveur et notifications.
- Affichage des droits Free/Pro et de l'usage du quota.
- Gestion des déconnexions et de l'expiration des sessions.

**Critères de sortie :** les parcours d'identité et de coordination Internet sont utilisables depuis l'application desktop.

---

# E. Internet, sécurité globale et publication

## Phase 20 — Transfert Internet direct entre pairs

**Objectif :** transporter les fichiers directement entre appareils distants lorsque les conditions réseau le permettent.

Travaux :
- Intégrer le transport sélectionné dans les ADR.
- Réaliser la négociation à partir de la signalisation backend.
- Établir l'identité des pairs et le canal sécurisé.
- Gérer les traversées NAT et les restrictions réseau.
- Réutiliser manifestes, blocs, empreintes et états du moteur Rust.
- Tester les réseaux domestiques, professionnels et mobiles.
- Ne jamais faire de l'API le chemin normal des données fichier.

**Critères de sortie :** deux appareils authentifiés réalisent un transfert Internet direct lorsque le réseau l'autorise.

## Phase 21 — Relais de secours et intégration complète

**Objectif :** assurer les transferts Internet quand la connexion directe échoue.

Travaux :
- Intégrer l'allocation du relais au backend.
- Acheminer les flux chiffrés uniquement.
- Gérer bascule, reconnexion, expiration et fermeture.
- Maintenir progression, vérification et reprise.
- Appliquer les limites de plan et les contrôles anti-abus.
- Mesurer trafic relayé, débit, disponibilité et coûts.
- Tester la non-exposition du contenu au service relais.

**Critères de sortie :** le transfert direct est prioritaire et le relais prend le relais sans compromettre la confidentialité.

## Phase 22 — Validation globale et sécurité produit

**Objectif :** vérifier NexDrop comme un produit complet, pas seulement comme des modules isolés.

Travaux :
- Tests fonctionnels sur deux vrais ordinateurs Windows.
- Tests LAN et Internet sur plusieurs conditions réseau.
- Tests fichiers volumineux, dossiers profonds et nombreux fichiers.
- Tests d'interruption, reprise, annulation et intégrité.
- Revue cryptographique et du modèle de confiance.
- Tests des accès, autorisations, limites et scénarios d'abus.
- Tests de charge API et relais.
- Tests mémoire, débit, CPU et stabilité longue durée.
- Revue de confidentialité, conservation et suppression des données.
- Résolution des défauts bloquants.

**Critères de sortie :** critères d'acceptation fonctionnels, de sécurité et de performance satisfaits sur les environnements Windows ciblés.

## Phase 23 — Publication Windows et exploitation

**Objectif :** préparer et publier une première version stable de NexDrop.

Travaux :
- Construire l'installateur Windows.
- Préparer la signature de l'application et les mises à jour.
- Vérifier installation, mise à niveau, désinstallation et conservation des données.
- Définir environnements de production et de préproduction.
- Déployer API, PostgreSQL et relais selon l'architecture retenue.
- Configurer sauvegardes, surveillance, alertes et procédure d'incident.
- Rédiger documentation utilisateur et support.
- Organiser les versions, notes de publication et retours utilisateurs.
- Faire une recette finale avant publication.

**Critères de sortie :** version Windows installable, mise à jour contrôlée, backend exploité et support opérationnel.

---

# F. Évolutions après la première version

## Phase 24 — Extension multiplateforme et offres avancées

**Objectif :** faire évoluer le produit après stabilisation de la version Windows.

Périmètre possible :
- Support macOS et Linux.
- Applications mobiles complémentaires.
- Offre Business et gestion des organisations.
- Gestion des équipes et politiques administratives.
- Facturation et administration multi-utilisateurs.
- Intégrations supplémentaires selon les besoins validés.
- Amélioration continue des performances, de la sécurité et de l'expérience utilisateur.

**Critères de sortie :** chaque extension dispose de ses propres exigences, décisions d'architecture, tests et critères de publication. Aucune plateforme secondaire ne doit déstabiliser la version Windows.

---

# Règles d'exécution du plan

1. Respecter l'ordre des dépendances : backend prioritaire, puis moteur Rust, puis parcours desktop, puis intégration Internet complète.
2. Ne pas démarrer une phase dépendante tant que ses contrats et critères d'entrée ne sont pas suffisamment définis.
3. Pour chaque fonctionnalité, distinguer décision, hypothèse, implémentation et preuve de test.
4. Ne jamais faire transiter les octets des fichiers par l'API de contrôle comme chemin normal.
5. Ne jamais exiger un compte pour un transfert LAN.
6. Ne jamais enregistrer un transfert reçu sans consentement du destinataire.
7. Ne jamais charger un fichier volumineux entier en mémoire.
8. Ne jamais considérer un transfert terminé avant vérification de l'intégrité.
9. Ne jamais faire confiance au frontend pour imposer les quotas ou les droits.
10. Ne jamais transmettre de contenu déchiffré ou de clé au relais.
11. Créer des tests avec chaque unité significative, puis exécuter les validations globales.
12. Inspecter les différences Git avant chaque commit ; ne committer que du travail réel, cohérent et vérifié.
13. Pousser les commits validés vers GitHub et garder le dépôt propre.
14. Mettre à jour ce plan lorsqu'une phase ou un critère de sortie est effectivement validé.

## Prochaine action autorisée par ce plan

La Phase 3 — Modèle de données et persistance métier est terminée et validée. La prochaine phase de développement est la **Phase 4 — Comptes et authentification** : inscription, vérification d'adresse e-mail, connexion, stockage sécurisé des mots de passe, sessions révocables et rotation des tokens de renouvellement.
