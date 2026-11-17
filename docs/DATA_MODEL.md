# NexDrop — Modèle de données et persistance métier

**Document :** Conception du modèle relationnel du backend
**Version :** 1.0 — Base V1 validée et implémentée
**Phase :** 3 — Modèle de données et persistance métier
**Base cible :** PostgreSQL 17
**ORM :** SQLAlchemy 2 asynchrone
**Révision Alembic courante :** `041602a30cb7` (13 tables métier et invariants V1)

> **Statut : BASE V1 VALIDÉE ET IMPLÉMENTÉE.** Les choix de périmètre V1 confirmés sont un expéditeur et un destinataire par transfert Internet, et un plafond Free de 10 GB décimaux (10 000 000 000 octets) par transfert. Les 13 tables SQLAlchemy et leurs migrations sont appliquées. Les décisions produit encore ouvertes sont signalées plus bas et ne doivent pas être inventées.

---

## 1. Objectifs et principes de conception

Le modèle doit soutenir le produit défini dans l'architecture et le plan directeur :

1. Les transferts LAN sont gratuits, illimités et possibles sans compte. Ils restent locaux et ne créent aucune donnée de transfert dans le backend.
2. Les transferts Internet nécessitent des comptes et sont coordonnés par le backend.
3. L'API est le **plan de contrôle**. Elle authentifie, autorise, coordonne et conserve les métadonnées ; elle ne transporte pas les octets des fichiers.
4. Le destinataire doit accepter explicitement une demande avant le début de la réception.
5. Le serveur ne doit pas stocker le contenu des fichiers, les chemins locaux ou la liste des noms de fichiers.
6. Les opérations sensibles doivent être transactionnelles, idempotentes lorsque nécessaire et auditables.
7. Les règles commerciales sont vérifiées par le backend et non uniquement par l'interface.
8. Les données personnelles doivent pouvoir être supprimées ou anonymisées selon une politique de conservation définie.

### Périmètre

Le modèle couvre les concepts prévus en Phase 3 : utilisateurs, appareils, sessions, transferts, participants, invitations, événements, offres, abonnements, paiements et mesure d'utilisation.

Il ne crée pas encore les fonctionnalités des phases suivantes : inscription/connexion API, émission de tokens, enregistrement d'appareils par endpoint, orchestration API, paiement réel, signalisation réseau ou relais.

---

## 2. Frontière essentielle : plan de contrôle et plan de données

    NEXDROP — PLAN DE CONTRÔLE
    +-------------------------------------------+
    | FastAPI                                   |
    | Authentification / autorisations          |
    | Utilisateurs / appareils / sessions       |
    | Invitations / consentement / états        |
    | Offres / abonnements / mesure d'utilisation|
    +----------------------+--------------------+
                           |
                       PostgreSQL
                           |
              Métadonnées et coordination seulement
                           |
       +-------------------+-------------------+
       |                                       |
    APPAREIL A                              APPAREIL B
    Expéditeur                              Destinataire
       +------ connexion directe chiffrée ----+
                          |
                 octets des fichiers
              (jamais dans les tables API)

### Ce qui est conservé

- Identifiants des comptes et appareils.
- Sessions et empreintes des secrets de renouvellement.
- Métadonnées minimales d'un transfert Internet : taille totale déclarée, nombre d'éléments, empreinte globale éventuelle, participants et état.
- Invitations, expiration et consommation.
- Événements de cycle de vie.
- Informations d'offre, d'abonnement, de paiement et de mesure d'utilisation nécessaires au service.

### Ce qui n'est pas conservé dans PostgreSQL

- Octets des fichiers.
- Noms de fichiers et de dossiers.
- Chemins absolus ou relatifs sur les ordinateurs.
- Contenu d'un manifeste détaillé.
- Clés privées, secrets de session en clair, tokens d'accès en clair ou codes d'invitation en clair.
- Chemins de destination choisis par le destinataire.

Le serveur peut conserver un nombre d'éléments, une taille totale et une empreinte globale du manifeste. Ces informations suffisent à coordonner et contrôler les limites déclarées sans enregistrer la structure privée des fichiers.

---

## 3. Vue relationnelle proposée

    USERS 1---N DEVICES
    USERS 1---N SESSIONS 1---N SESSION_REFRESH_TOKENS
    USERS 1---N TRANSFERS (initiés)
    DEVICES 1---N TRANSFERS (appareil initiateur)
    TRANSFERS 1---N TRANSFER_PARTICIPANTS
    USERS 1---N TRANSFER_PARTICIPANTS
    DEVICES 1---N TRANSFER_PARTICIPANTS
    TRANSFERS 1---N TRANSFER_INVITATIONS
    TRANSFER_INVITATIONS 1---N TRANSFER_INVITATION_REDEMPTIONS
    TRANSFER_PARTICIPANTS 1---N TRANSFER_INVITATION_REDEMPTIONS
    TRANSFERS 1---N TRANSFER_EVENTS
    USERS 1---N TRANSFER_EVENTS (acteur)
    TRANSFERS 1---N TRANSFER_USAGE_RECORDS
    USERS 1---N SUBSCRIPTIONS N---1 PLANS
    USERS 1---N PAYMENTS
    SUBSCRIPTIONS 1---N PAYMENTS

Cette vue présente les relations fonctionnelles. Les colonnes, contraintes exactes et clés composites seront fixées lors de la réalisation des modèles SQLAlchemy.

---

## 4. Entités proposées

### 4.1 USERS — Comptes NexDrop

**Rôle :** représenter une identité utilisateur nécessaire aux transferts Internet.

Champs envisagés :

| Champ | Type PostgreSQL indicatif | Règle |
|---|---|---|
| id | UUID | Clé primaire, générée côté application |
| email | VARCHAR(320) | Adresse de présentation |
| email_normalized | VARCHAR(320) | Valeur canonique, unique |
| password_hash | TEXT, nullable | Hash uniquement, jamais de mot de passe en clair |
| display_name | VARCHAR(80), nullable | Nom d'affichage facultatif |
| status | VARCHAR(20) | pending, active, suspended, deleted |
| email_verified_at | TIMESTAMPTZ, nullable | Vérification de l'adresse |
| locale | VARCHAR(10) | Préférence de langue, par exemple fr ou en |
| created_at | TIMESTAMPTZ | Création UTC |
| updated_at | TIMESTAMPTZ | Dernière modification |
| deleted_at | TIMESTAMPTZ, nullable | Suppression logique/anonymisation |

**Contraintes :** unicité de email_normalized, contrôle des états, index sur l'adresse normalisée et le statut si les requêtes le justifient.

**Décision de sécurité :** le mot de passe est nullable pour ne pas bloquer une éventuelle méthode d'authentification externe future. Aucune connexion par fournisseur externe n'est incluse tant qu'elle n'est pas décidée.

### 4.2 DEVICES — Appareils enregistrés

**Rôle :** représenter une installation NexDrop associée à un compte.

Champs envisagés : id UUID ; user_id UUID ; installation_id UUID aléatoire propre à l'installation ; name VARCHAR(100) ; platform VARCHAR(20) ; app_version VARCHAR(40) nullable ; status active/revoked ; created_at ; last_seen_at nullable ; revoked_at nullable.

**Contraintes :** unicité de (user_id, installation_id) et clé unique composite (id, user_id) pour garantir qu'un appareil référencé appartient bien à l'utilisateur associé.

**Point non figé :** les clés cryptographiques d'identité d'appareil ne sont pas définies ici. Leur algorithme, format, rotation et révocation doivent faire l'objet d'une décision d'architecture avant d'ajouter les colonnes ou une table de clés.

Un appareil LAN non connecté à un compte reste une identité locale gérée par le client Rust ; il ne doit pas être forcé dans cette table.

### 4.3 SESSIONS — Sessions d'authentification

**Rôle :** représenter une session de connexion logique, et non stocker directement un token d'accès.

Champs envisagés : id UUID ; user_id UUID ; device_id UUID nullable ; created_at ; last_used_at nullable ; expires_at ; revoked_at nullable ; revocation_reason VARCHAR(40) nullable.

La clé étrangère composite (device_id, user_id) vers devices(id, user_id) empêchera d'associer une session à l'appareil d'un autre compte. Une session peut ne pas avoir de device_id pour permettre des clients non desktop futurs, sous réserve de la politique d'authentification.

### 4.4 SESSION_REFRESH_TOKENS — Rotation des tokens de renouvellement

**Rôle :** gérer la rotation et la détection de réutilisation d'un ancien token.

Champs envisagés : id UUID ; session_id UUID ; token_hash BYTEA unique ; issued_at ; expires_at ; consumed_at nullable ; revoked_at nullable ; replaced_by_id UUID nullable, référence vers le token suivant.

**Règles :** seul le hash du token opaque est stocké. La valeur brute n'est retournée qu'une fois au client. La rotation consomme l'ancien token et crée le nouveau dans une seule transaction. La réutilisation d'un token déjà consommé doit déclencher la révocation de la session concernée selon la politique de la Phase 4.

Un index unique partiel doit empêcher plusieurs tokens non consommés et non révoqués pour une même session. La clé de remplacement est composite avec `session_id` : un token ne peut jamais pointer vers un token d'une autre session. Les access tokens de courte durée ne sont pas persistés en base dans le modèle proposé.

### 4.5 PLANS — Catalogue d'offres

**Rôle :** centraliser les droits commerciaux appliqués par le backend.

Champs envisagés : id UUID ; code VARCHAR(30) unique (free, pro, etc.) ; name VARCHAR(80) ; max_transfer_bytes BIGINT nullable ; is_active BOOLEAN ; created_at ; updated_at.

**Règle produit connue :** le LAN reste gratuit et illimité sans compte. Pour Internet, Free est limité à 10 GB par transfert. Les droits et plafonds Pro et Business restent à fixer avant activation de ces offres.

Le catalogue ne doit pas contenir de prix inventé. Les prix, devises et identifiants du prestataire de paiement seront ajoutés en fonction du prestataire choisi en Phase 8.

Une valeur NULL de max_transfer_bytes signifie uniquement « plafond non limité » pour une offre explicitement validée ; elle ne doit jamais représenter un plafond encore inconnu. Une offre Pro ne sera pas activée tant que ses droits n'auront pas été décidés.

Le transfert conservera une photographie du code d'offre et du plafond appliqué à sa création, afin de rendre une décision d'autorisation explicable même si l'offre évolue plus tard.

### 4.6 TRANSFERS — Transferts Internet

**Rôle :** conserver l'état de coordination d'un transfert Internet. Aucun transfert LAN n'est enregistré par l'API.

Champs envisagés :

| Champ | Type indicatif | Règle |
|---|---|---|
| id | UUID | Clé primaire |
| created_by_user_id | UUID | Compte initiateur |
| created_by_device_id | UUID, nullable | Appareil initiateur |
| status | VARCHAR(24) | État contrôlé par le domaine |
| total_bytes | BIGINT | Taille totale déclarée, agrégée |
| item_count | INTEGER | Nombre d'éléments, sans leurs noms |
| manifest_digest | BYTEA, nullable | Empreinte globale éventuelle du manifeste |
| plan_code_snapshot | VARCHAR(30) | Offre utilisée à l'autorisation |
| max_transfer_bytes_snapshot | BIGINT, nullable | Plafond appliqué à la création |
| created_at | TIMESTAMPTZ | Création |
| expires_at | TIMESTAMPTZ | Expiration métier |
| accepted_at | TIMESTAMPTZ, nullable | Acceptation initiale |
| started_at | TIMESTAMPTZ, nullable | Début du transfert |
| completed_at | TIMESTAMPTZ, nullable | Fin vérifiée |
| cancelled_at | TIMESTAMPTZ, nullable | Annulation |
| failed_at | TIMESTAMPTZ, nullable | Échec |
| updated_at | TIMESTAMPTZ | Dernière modification |
| version | INTEGER | Contrôle optimiste des mises à jour concurrentes |

**États proposés :**

- awaiting_receiver : en attente de réponse du destinataire ;
- accepted : consentement obtenu ;
- connecting : négociation du canal ;
- transferring : transfert des données en cours ;
- verifying : vérification d'intégrité ;
- completed : transfert terminé et intégrité validée ;
- declined : destinataire ayant refusé ;
- cancelled : annulation par une partie autorisée ;
- expired : invitation ou transfert expiré ;
- failed : échec définitif.

L'état initial created peut être un état interne très bref ; la proposition est de créer le transfert et ses participants dans une transaction et de le rendre visible directement en awaiting_receiver.

**Contraintes :** total_bytes >= 0, item_count > 0, taille inférieure ou égale au plafond snapshot lorsqu'il existe, expiration postérieure à la création, états contrôlés, relations utilisateur/appareil cohérentes, index sur (created_by_user_id, created_at) et (status, expires_at) pour les tâches de traitement.

La transition completed n'est autorisée qu'après validation du protocole de transfert et de l'intégrité par les pairs. Les contraintes PostgreSQL vérifient que expires_at > created_at, que la taille déclarée ne dépasse pas max_transfer_bytes_snapshot, et que les états accepted, connecting, transferring, verifying et completed ont les horodatages requis. completed exige completed_at, et cette date ne peut exister pour un autre état. Les transitions restent également validées par le service métier.

### 4.7 TRANSFER_PARTICIPANTS — Participants et consentement

**Rôle :** représenter chaque utilisateur impliqué dans un transfert.

Champs envisagés : id UUID ; transfer_id UUID ; user_id UUID ; device_id UUID nullable jusqu'à la sélection de l'appareil ; role sender/recipient ; response_status pending/accepted/declined/revoked ; joined_at ; responded_at nullable ; last_seen_at nullable.

**Contraintes :** un utilisateur ne peut apparaître qu'une fois dans un transfert ; un index unique partiel garantit au plus un participant sender par transfert et un second index unique partiel limite à un participant recipient en V1 ; le couple (device_id, user_id) doit correspondre à un appareil appartenant à ce compte.

**Périmètre V1 proposé : un expéditeur et un destinataire par transfert.** Cela rend le consentement, les états globaux et les invitations non ambigus. Le modèle pourra être étendu à plusieurs destinataires dans une évolution ultérieure, avec une règle d'état par participant et une politique explicite de diffusion.

Le service doit garantir qu'il existe exactement un expéditeur et exactement un destinataire avant de démarrer la négociation. L'expéditeur doit correspondre à transfers.created_by_user_id. Ces invariants seront appliqués dans les transactions de création et de consommation d'invitation et couverts par des tests d'intégration.

Le consentement du destinataire est enregistré dans response_status et responded_at. PostgreSQL refuse un destinataire déjà accepté, refusé ou révoqué sans responded_at. Le chemin de destination du destinataire n'est jamais enregistré sur le serveur.

### 4.8 TRANSFER_INVITATIONS — Codes et liens de transfert

**Rôle :** représenter un moyen d'accès temporaire à un transfert.

Champs envisagés : id UUID ; transfer_id UUID ; created_by_user_id UUID ; kind code/link ; token_digest BYTEA unique ; expires_at ; max_uses INTEGER ; use_count INTEGER ; revoked_at nullable ; created_at.

**Sécurité :** aucune valeur brute de code ou de lien n'est conservée. Les liens doivent être générés avec une entropie cryptographique élevée et leur empreinte peut être conservée. Les codes courts sont plus sensibles aux attaques par dictionnaire : ils exigent un HMAC avec secret serveur, une durée de vie courte, une limitation stricte des tentatives et une protection contre l'énumération.

La consommation doit être atomique : vérification de l'expiration, de la révocation et du nombre maximal d'utilisations, incrément, création du participant et événement associés dans une transaction unique. En V1, PostgreSQL impose max_uses = 1 et la rédemption associe uniquement un participant dont le rôle est recipient au transfert correspondant.

### 4.9 TRANSFER_INVITATION_REDEMPTIONS — Consommation des invitations

**Rôle :** fournir une trace idempotente de la consommation d'un code ou d'un lien.

Champs envisagés : id UUID ; invitation_id UUID ; participant_id UUID ; redeemed_at.

**Contraintes :** unicité de (invitation_id, participant_id) pour éviter une double consommation par le même participant ; un retry ne doit pas créer deux participants ou compter deux fois une utilisation.

Cette table pourra être omise si l'examen démontre que les invariants sont garantis plus simplement par les participants et une mise à jour atomique de l'invitation. Le choix sera arrêté avant la migration.

### 4.10 TRANSFER_EVENTS — Historique et audit du transfert

**Rôle :** conserver un journal append-only des transitions et opérations importantes.

Champs envisagés : id UUID ; transfer_id UUID ; actor_user_id UUID nullable pour les événements système ou après anonymisation ; actor_device_id UUID nullable ; event_type VARCHAR(40) ; from_status et to_status VARCHAR(24) nullables ; event_data JSONB ; created_at TIMESTAMPTZ.

**Règles :** les événements sont ajoutés, jamais modifiés par les opérations ordinaires. Aucun secret, nom de fichier, chemin, token ou contenu de manifeste ne doit être placé dans event_data. Les événements de transition sont créés dans la même transaction que la mise à jour de l'état du transfert.

Les clés étrangères vers l'acteur doivent permettre l'anonymisation d'un compte sans effacer l'historique d'un transfert conservé pour audit.

### 4.11 TRANSFER_USAGE_RECORDS — Mesure de l'utilisation réelle

**Rôle :** enregistrer une mesure idempotente du volume associé à un participant après un transfert.

Champs envisagés : id UUID ; transfer_id UUID ; participant_id UUID ; user_id UUID ; bytes_transferred BIGINT ; recorded_at TIMESTAMPTZ.

**Contraintes :** bytes_transferred >= 0, une seule ligne par (transfer_id, participant_id), et aucune écriture avant la fin validée du transfert.

Cette table sert à la mesure et à l'audit. Elle **ne définit pas** un quota mensuel, une enveloppe de données ou une facturation à l'octet : aucune de ces règles commerciales n'a encore été décidée. L'usage est enregistré une seule fois, et non à chaque retry réseau.

### 4.12 SUBSCRIPTIONS — Abonnements

**Rôle :** représenter les droits payants associés à un compte.

Champs envisagés : id UUID ; user_id UUID ; plan_id UUID ; status pending/active/past_due/cancelled/expired ; provider nullable ; provider_subscription_id nullable ; current_period_start ; current_period_end ; cancel_at_period_end BOOLEAN ; created_at ; updated_at ; cancelled_at nullable.

**Règles :** le plan Free est le plan par défaut lorsque l'utilisateur ne dispose d'aucun abonnement payant actif ; il n'est donc pas nécessaire de créer une souscription Free pour chaque compte. Une contrainte unique partielle empêchera plusieurs abonnements simultanément actifs ou en retard de paiement pour le même utilisateur, sauf décision commerciale contraire.

Les transitions d'abonnement et la réconciliation avec le prestataire relèvent de la Phase 8.

### 4.13 PAYMENTS — Paiements

**Rôle :** conserver les références et résultats de paiements sans stocker de données bancaires sensibles.

Champs envisagés : id UUID ; user_id UUID ; subscription_id UUID nullable ; provider ; provider_payment_id ; amount_minor BIGINT ; currency CHAR(3) ; status pending/succeeded/failed/refunded/partially_refunded ; created_at ; paid_at nullable ; refunded_at nullable.

**Contraintes :** unicité de (provider, provider_payment_id), montant positif ou nul selon la politique du prestataire, devise validée, aucun numéro de carte ou secret de paiement dans la base.

Le prestataire de paiement et les règles de facturation ne sont pas sélectionnés dans cette phase. Les webhooks seront traités et rendus idempotents en Phase 8.

---

## 5. Principales relations et cardinalités

| Relation | Cardinalité | Règle principale |
|---|---|---|
| User → Device | 1 à N | Un appareil enregistré appartient à un compte |
| User → Session | 1 à N | Un compte peut avoir plusieurs sessions |
| Session → RefreshToken | 1 à N | Historique de rotation et révocation |
| User → Transfer initié | 1 à N | Un compte peut initier plusieurs transferts Internet |
| Transfer → Participant | 1 à 2 en V1 | Un expéditeur et un destinataire ; extension multi-destinataires ultérieure |
| Transfer → Invitation | 1 à N | Plusieurs codes/liens temporaires possibles |
| Invitation → Redemption | 1 à N | Consommation contrôlée et idempotente |
| Transfer → Event | 1 à N | Historique append-only |
| Transfer → UsageRecord | 1 à N | Mesure par participant, après achèvement |
| User → Subscription | 1 à N | Historique d'abonnements |
| Plan → Subscription | 1 à N | Une souscription référence une offre |
| User → Payment | 1 à N | Historique de paiements |
| Subscription → Payment | 1 à N | Paiements associés à l'abonnement |

## 6. États et invariants métier

### 6.1 Cycle de vie d'un transfert

    awaiting_receiver
          |
          +----> declined
          |
          v
      accepted
          |
          v
      connecting
          |
          v
     transferring
          |
          v
       verifying
          |
          v
      completed

    Depuis les états non terminaux :
      -> cancelled / expired / failed selon les règles d'autorisation.

Les transitions doivent être définies dans une machine à états côté domaine. Une requête ne peut pas modifier librement la colonne status. Les transitions concurrentes doivent verrouiller la ligne du transfert ou utiliser une version optimiste ; la mise à jour d'état et l'événement associé sont atomiques.

### 6.2 Invariants à garantir

1. Un transfert backend est un transfert Internet ; le LAN anonyme ne crée pas de ligne serveur.
2. Chaque transfert V1 a exactement un expéditeur et un destinataire avant le démarrage de la négociation ; la transaction de création ou la rédemption du lien garantit cet invariant.
3. Un participant ne peut pas répondre à la place d'un autre utilisateur.
4. Une demande entrante n'est pas acceptée implicitement.
5. Le destinataire peut refuser ; un transfert refusé ne peut pas être démarré.
6. Un transfert terminé a passé l'étape de vérification d'intégrité.
7. Les invitations expirées, révoquées ou épuisées ne peuvent pas être consommées.
8. Une invitation ne peut pas créer deux fois le même participant.
9. Les transitions et les événements d'audit sont enregistrés dans une même transaction.
10. Les appareils rattachés à une session ou à un participant appartiennent au même utilisateur.
11. Le plafond de transfert est vérifié sur la taille totale déclarée de tous les éléments, pas seulement sur chaque fichier séparément.
12. Les règles de droits sont contrôlées côté backend ; l'interface n'est jamais l'autorité.
13. Les octets des fichiers et les chemins privés ne sont pas enregistrés dans la base.

**Limite importante à traiter dans le protocole :** lors d'un transfert direct de pair à pair, le backend ne voit pas le flux de données. Il peut contrôler la taille totale déclarée et délivrer une autorisation qui lie le transfert à son manifeste, mais il ne peut pas mesurer indépendamment chaque octet d'un canal direct. Le moteur et le protocole devront empêcher le dépassement du manifeste accepté, et les reçus de fin devront être conçus dans les phases de transfert. Il ne faut pas prétendre que le serveur mesure directement les octets d'un flux P2P qu'il ne transporte pas.

---

## 7. Contraintes, index et conventions PostgreSQL

### Types et conventions

- Identifiants : UUID générés côté application ; pas d'extension PostgreSQL obligatoire pour les générer.
- Dates : TIMESTAMPTZ, stockées et manipulées en UTC.
- Tailles : BIGINT en octets ; jamais un flottant pour une taille de fichier.
- Empreintes et digests : BYTEA avec longueur/format contrôlé par la couche domaine.
- Événements : JSONB limité à des données non sensibles et à une liste blanche.
- États : VARCHAR avec contraintes CHECK plutôt que types ENUM PostgreSQL lors de la première version, pour faciliter les évolutions contrôlées.
- Schéma : tables au pluriel et noms snake_case ; contraintes nommées selon la convention SQLAlchemy déjà présente dans db/base.py.

### Index attendus

- users(email_normalized) unique.
- devices(user_id, installation_id) unique ; devices(user_id, status) pour les appareils actifs.
- Clé étrangère composite (created_by_device_id, created_by_user_id) de transfers vers devices(id, user_id).
- Clés étrangères composites (device_id, user_id) depuis sessions et transfer_participants vers devices(id, user_id).
- Clé étrangère composite (actor_device_id, actor_user_id) pour les événements attribués à un appareil ; une rédemption et un relevé d'utilisation doivent également rester cohérents avec le participant référencé.
- sessions(user_id, expires_at) et sessions(device_id).
- session_refresh_tokens(token_hash) unique ; index partiel pour le token courant d'une session.
- transfers(created_by_user_id, created_at DESC) ; transfers(status, expires_at).
- transfer_participants(transfer_id, user_id) unique ; index user_id pour retrouver les transferts d'un compte.
- Index unique partiel d'un seul expéditeur et d'un seul destinataire par transfert en V1.
- transfer_invitations(token_digest) unique ; index des invitations actives par transfert et expiration.
- transfer_events(transfer_id, created_at).
- transfer_usage_records(transfer_id, participant_id) unique ; une clé composite doit garantir la cohérence du user_id avec le participant.
- subscriptions(user_id, status) et unicité partielle d'une souscription active par utilisateur.
- payments(provider, provider_payment_id) unique ; payments(user_id, created_at DESC).
- Unicité de (provider, provider_subscription_id) pour les identifiants d'abonnement externes lorsqu'ils sont présents.

Les index définitifs seront confirmés par les requêtes réelles des phases 4 à 11. Éviter de multiplier les index qui ralentissent les écritures sans bénéfice mesuré.

### Clés étrangères et suppression

- Ne pas utiliser ON DELETE CASCADE sur les transferts et événements d'audit sans analyse : la suppression d'un compte ne doit pas effacer silencieusement des historiques nécessaires.
- Utiliser RESTRICT par défaut sur les relations métier importantes ; réserver SET NULL aux références d'acteurs qui doivent survivre à une anonymisation.
- Les utilisateurs sont d'abord désactivés/anonymisés ; l'effacement définitif dépendra de la politique de conservation et des obligations applicables.
- Les appareils révoqués et sessions expirées peuvent être purgés selon une politique explicite ; les tokens sont supprimés ou invalidés.
- Les offres utilisées historiquement ne sont pas supprimées : elles sont désactivées.

---

## 8. Transactions et concurrence

Les opérations suivantes devront être atomiques.

**Création d'un transfert Internet**
1. Charger le compte, ses droits effectifs et son appareil.
2. Vérifier l'état du compte et les autorisations.
3. Vérifier total_bytes contre le plafond effectif.
4. Créer le transfert avec l'instantané des droits appliqués.
5. Créer le participant expéditeur et, si le destinataire est déjà identifié, son participant recipient.
6. Créer une invitation si le destinataire doit rejoindre le transfert par code ou lien.
7. Ajouter l'événement transfer_created.
8. Valider une seule transaction.

Lorsqu'un destinataire rejoint par invitation, sa rédemption crée le participant recipient et son événement dans une transaction atomique ; le transfert ne peut pas passer à accepted avant cette étape.

**Réponse du destinataire**
1. Verrouiller le transfert et le participant concerné.
2. Vérifier que le demandeur est bien le destinataire.
3. Vérifier l'état et l'expiration.
4. Enregistrer acceptation ou refus et son horodatage.
5. Mettre à jour l'état global si les conditions le permettent.
6. Ajouter l'événement correspondant dans la même transaction.

**Consommation d'un code ou lien**
- Effectuer une mise à jour conditionnelle atomique qui vérifie expiration, révocation et nombre d'utilisations.
- Créer le participant et la rédemption de façon idempotente.
- En cas de retry, retourner le résultat déjà établi plutôt que de consommer une seconde fois.

**Rotation d'un refresh token**
- Verrouiller la session et le token courant.
- Marquer l'ancien token comme consommé.
- Créer le suivant et relier les deux enregistrements.
- Révoquer la session si un ancien token consommé est réutilisé, conformément à la politique de la Phase 4.

**Mesure d'utilisation**
- Insérer une ligne unique par participant et transfert à l'issue de la vérification.
- Les retries doivent rencontrer la contrainte d'unicité et ne pas compter deux fois.

---

## 9. Politique de confidentialité et conservation — proposition

1. Ne jamais journaliser les mots de passe, tokens, codes d'invitation, URLs secrètes ou secrets de paiement.
2. Ne pas stocker de noms de fichiers, chemins ou contenu de manifeste détaillé dans le backend.
3. Conserver uniquement les métadonnées de transfert nécessaires à la coordination, au support et à l'historique demandé.
4. Définir une durée de conservation pour invitations, sessions, événements et transferts expirés avant la mise en production.
5. Prévoir une procédure d'export, de suppression et d'anonymisation des données personnelles.
6. Conserver les références de paiement sans données de carte ou de compte bancaire.
7. Restreindre l'accès administratif aux métadonnées nécessaires et auditer chaque action privilégiée.

Les durées précises ne sont volontairement pas inventées dans ce document. Elles doivent être validées avec les besoins opérationnels, le coût de stockage et les obligations applicables avant la Phase 12.

---

## 10. Décisions produit et architecture encore ouvertes

Le schéma V1 est en place. Ces points restent ouverts et devront être tranchés avant d’activer les fonctionnalités correspondantes ou de préparer la production :

| Sujet | Proposition de départ | Statut |
|---|---|---|
| Unité du plafond Free de 10 GB | 10 000 000 000 octets (GB décimal) | À confirmer |
| Portée du plafond | Taille totale de tous les fichiers d'un transfert | Proposition à confirmer |
| Nombre de destinataires V1 | Un destinataire par transfert ; multi-destinataires reportés | Proposition à confirmer |
| Codes de transfert | Code court à durée courte, rate-limit strict et HMAC serveur | ADR sécurité requise |
| Liens de transfert | Token aléatoire à forte entropie, seul son digest est stocké | Proposition |
| Durée d'expiration des invitations | Valeur à définir selon le parcours utilisateur | À décider |
| Conservation des transferts/événements | Politique de rétention à définir | À décider |
| Appareil et identité cryptographique | Schéma de clés après ADR sur identité et handshake | ADR requise |
| Offre Pro | Plafonds et droits non inventés | À décider avant activation |
| Offre Business | Hors périmètre initial | Phase 24 |
| Paiement | Prestataire non choisi ; schéma provider-neutral | Phase 8 |
| Quota cumulé périodique | Aucun quota mensuel confirmé ; ne pas en inventer | À décider si besoin |
| Attribution de l'usage P2P | Reçus signés et validation par le protocole à concevoir | Phase 20–21 |

### Règle Free confirmée

Le plafond Free appliqué par le backend est de `10_000_000_000` octets (10 GB décimaux) pour l’ensemble d’un transfert Internet. La valeur est enregistrée sur l’offre `free` et copiée dans `max_transfer_bytes_snapshot` lors de la création d’un transfert. Les comparaisons utilisent toujours les octets ; l’interface pourra afficher « 10 Go ».

## 11. Séquence d'implémentation réalisée de la Phase 3

Travaux effectivement réalisés après validation de la base V1 :

### 3.1 — Conventions et fondation ORM

- Types UUID générés côté application et dates `TIMESTAMPTZ` en UTC.
- Conventions de nommage des tables, index, contraintes et clés étrangères.
- Modèles séparés dans les modules `identity.py`, `transfers.py` et `billing.py`.
- Import explicite de tous les modèles dans la métadonnée utilisée par Alembic.

### 3.2 — Identités et sessions

- Modèles `users`, `devices`, `sessions` et `session_refresh_tokens`.
- Unicité de l'e-mail normalisé et propriété des appareils vérifiée par clés composites.
- Hash SHA-256 des refresh tokens, un token courant par session et chaîne de rotation liée à la même session.

### 3.3 — Transferts et consentement

- Modèles `transfers`, `transfer_participants`, `transfer_invitations`, `transfer_invitation_redemptions` et `transfer_events`.
- Un expéditeur et un destinataire au maximum par transfert V1 ; la logique applicative devra garantir leur présence avant la négociation.
- Invitations à usage unique et rédemption réservée au participant destinataire.
- Contraintes PostgreSQL sur taille, expiration, consentement, état et horodatages.
- Versionnement optimiste SQLAlchemy pour détecter les modifications concurrentes.

### 3.4 — Abonnements et mesure d'utilisation

- Modèles `plans`, `subscriptions`, `payments` et `transfer_usage_records`.
- Offre Free seedée à 10 000 000 000 octets par transfert Internet.
- Un seul abonnement effectif par utilisateur et références de paiement sans données bancaires.
- Mesures d'usage uniques par transfert et participant.

### 3.5 — Migrations et validation

- Révision `8d9e28ddd1c7` créée et appliquée pour les 13 tables et l'offre Free.
- Révision `041602a30cb7` créée et appliquée pour les invariants additionnels.
- Downgrade jusqu'à `base`, puis upgrade complet rejoué avec succès sur `nexdrop_test`.
- Tests de contraintes, confidentialité et concurrence exécutés sur PostgreSQL réel.
- `alembic check`, Ruff, formatage, compilation Python et readiness API validés.

Les décisions encore ouvertes de la section 10 sont réservées aux phases fonctionnelles correspondantes ; elles ne doivent pas être remplacées par des hypothèses arbitraires.

---

## 12. Critères de sortie de la Phase 3

Les critères de sortie appliqués à la Phase 3 étaient :

- Le présent modèle est validé et les décisions bloquantes sont consignées.
- Les modèles SQLAlchemy couvrent les entités retenues et sont importés dans Base.metadata.
- Les contraintes, clés étrangères et index essentiels existent dans PostgreSQL.
- La migration Alembic est reproductible depuis la révision initiale.
- Les tests prouvent les règles d'unicité, d'appartenance appareil/utilisateur, de consentement, d'expiration et de transitions.
- Les opérations critiques sont atomiques et idempotentes selon les cas.
- Aucune donnée privée de fichier ou aucun secret brut n'est stocké.
- Les données de développement existantes ne sont ni supprimées ni écrasées par les tests.
- Les validations automatisées passent et les commits sont publiés.

---

## 13. État de réalisation

| Élément | État |
|---|---|
| Inspection du backend et de PostgreSQL | Vérifiée |
| Base relationnelle V1 | Validée : 1 expéditeur, 1 destinataire, Free 10 GB |
| Modèles SQLAlchemy | 13 tables enregistrées dans `Base.metadata` |
| Migration initiale métier | `8d9e28ddd1c7` — appliquée |
| Migration des invariants V1 | `041602a30cb7` — appliquée |
| PostgreSQL de développement | 13 tables, offre Free seedée |
| Base PostgreSQL de test | `nexdrop_test`, distincte de la base de développement |
| Tests automatisés | 31 tests réussis sur PostgreSQL réel |
| Concurrence optimiste | Vérifiée avec deux sessions SQLAlchemy |
| Dérive Alembic | Aucune opération supplémentaire détectée |

**Statut de la Phase 3 : TERMINÉE.** Les décisions commerciales ou protocolaires encore ouvertes sont suivies dans la section 10 et seront traitées dans leurs phases respectives.
