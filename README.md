# 🕒 Odoo Attendance Sync System — Django + Odoo 18

> **Full-stack employee attendance (pointage) management and synchronization system built with Django, Odoo 18, and PostgreSQL.**

---

# 🇫🇷 Français

## 📋 Présentation

**Odoo Attendance Sync System** est une solution complète de gestion des présences et des pointages des employés, basée sur une architecture **Django + Odoo 18 + PostgreSQL**.

Le système sépare la gestion de la logique métier et de la collecte des pointages côté **Django**, de la gestion RH, de l'affichage et de l'administration côté **Odoo**.

Django reçoit ou génère les événements de pointage, les enregistre localement, détermine automatiquement leur état (`IN` / `OUT`) et synchronise ensuite les données avec Odoo via **XML-RPC** et des endpoints **JSON**.

Odoo centralise les informations RH et fournit les interfaces de consultation et de gestion des pointages grâce au module personnalisé **SMARTfront**.

---

## 🏗️ Architecture

Le projet repose sur trois services Docker principaux :

| Service       | Rôle                                          |   Port |
| ------------- | --------------------------------------------- | -----: |
| `postgres_db` | Base de données PostgreSQL 15 partagée        | `5432` |
| `odoo_app`    | Odoo 18 + module SMARTfront                   | `8069` |
| `django_app`  | API Django, logique métier et synchronisation | `8000` |

### Architecture générale

```text
                 ┌───────────────────────┐
                 │   Pointage / Machine  │
                 │   Web / API / Manuel  │
                 └───────────┬───────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       Django        │
                  │                     │
                  │ API + Business Logic│
                  │ Local Attendance DB │
                  └──────────┬──────────┘
                             │
                             │ XML-RPC / JSON
                             ▼
                  ┌─────────────────────┐
                  │       Odoo 18       │
                  │                     │
                  │ HR + SMARTfront     │
                  │ Pointage Records     │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     PostgreSQL      │
                  │     Persistence     │
                  └─────────────────────┘
```

---

# 🔄 Flux de fonctionnement

Le fonctionnement de bout en bout est le suivant :

1. Un événement de pointage arrive via une machine, l'API, une interface web ou une saisie manuelle.
2. Django identifie l'employé grâce à son **PIN**.
3. La logique métier détermine automatiquement si l'événement correspond à une entrée (`IN`) ou une sortie (`OUT`).
4. Le pointage est enregistré dans Django avec `synced_to_odoo=False`.
5. Le système de synchronisation recherche les enregistrements non synchronisés.
6. Django transmet les données à Odoo via XML-RPC ou endpoint JSON.
7. Odoo crée ou met à jour les informations correspondantes.
8. Les pointages deviennent disponibles dans les interfaces Odoo.
9. L'état de synchronisation est mis à jour côté Django.

```text
Pointage
   │
   ▼
Django API / Machine
   │
   ▼
Employee resolution by PIN
   │
   ▼
Determine IN / OUT
   │
   ▼
Local Pointage
synced_to_odoo = False
   │
   ▼
Synchronization
   │
   ├──────────────► XML-RPC
   │
   └──────────────► JSON Endpoint
                         │
                         ▼
                    Odoo 18
                         │
                         ▼
                   hr.pointage
```

---

# 🧩 Composants du projet

## 🐍 Django

Répertoire principal :

```text
django/pointage_machine/
```

Django constitue le cœur de la logique de collecte et de traitement des pointages.

### 📦 Modèles

#### `Employee`

Représente les employés enregistrés côté Django.

Principales informations :

* `pin`
* `name`
* Identifiant Odoo associé lorsque disponible

#### `Pointage`

Représente un événement de pointage.

Principaux champs :

* `employee`
* `check_time`
* `state`
* `source`
* `anomaly`
* `synced_to_odoo`
* `external_id`
* `odoo_employee_id`
* `odoo_field`

Les états principaux sont :

```text
IN
OUT
```

#### `Leave`

Permet de gérer les informations simples liées aux congés/absences.

---

# ⚙️ Logique métier

Le fichier :

```text
attendance/pointage_service.py
```

contient la logique principale de traitement des pointages.

Il est responsable notamment de :

* Créer les événements de pointage.
* Identifier l'employé.
* Déterminer automatiquement `IN` ou `OUT`.
* Gérer les pauses déjeuner.
* Gérer les journées ignorées/skippées.
* Fermer automatiquement certains pointages ouverts.
* Maintenir la cohérence des opérations dans une transaction atomique.

L'objectif est de garder les **API/views aussi légères que possible**, la logique métier étant centralisée dans le service.

---

# 🔗 Intégration Odoo

Le fichier principal côté Django est :

```text
attendance/odoo_service.py
```

Il fournit le client d'intégration Odoo.

Fonctionnalités principales :

* Authentification Odoo.
* Recherche d'employés.
* Création d'employés.
* Recherche de pointages.
* Création de pointages.
* Mise à jour des données.
* Vérification des enregistrements synchronisés.
* Communication via XML-RPC.

Un outil de synchronisation permet également d'envoyer les enregistrements Django non encore synchronisés vers Odoo.

---

# 🌐 API / Views Django

L'API Django fournit notamment :

* ❤️ Health check.
* 📋 Liste des pointages.
* 🏠 Dashboard / page d'accueil.
* 🔌 Endpoints liés aux pointages.
* 🔄 Outils de synchronisation.
* 🧪 Commandes de test et de diagnostic.

Les vues restent volontairement légères et délèguent le traitement à la couche de services.

---

# 🏢 Module Odoo — SMARTfront

Le module personnalisé est situé dans :

```text
addons/SMARTfront/
```

Il fournit la partie Odoo du système.

## 👤 Extension de `hr.employee`

Le modèle `hr.employee` est étendu avec notamment :

* `pin`
* `django_id`

Le PIN permet d'établir la correspondance entre les employés Django et Odoo.

---

## 🕒 Modèle `hr.pointage`

Le module introduit le modèle :

```text
hr.pointage
```

Il représente les enregistrements de pointage dans Odoo.

Principaux champs :

* `employee`
* `date`
* `check_in`
* `check_out`
* `state`
* `note`
* `django_id`

Le champ `django_id` permet d'identifier la source Django et d'éviter les doublons lors de la synchronisation.

---

## ⚙️ Configuration SMARTfront

Le modèle :

```text
smartfront.config
```

centralise certaines options d'intégration, notamment :

* `api_key`
* `webhook_url`
* `sync_interval`
* `auto_validate`

---

# 🌐 Endpoint Odoo

Le module expose notamment :

```text
/api/odoo/pointage/create
```

Cet endpoint permet à Django de transmettre des données de pointage à Odoo au format JSON.

---

# 🖥️ Interface Odoo

Le module SMARTfront fournit :

* Menus de gestion des pointages.
* Vues backend.
* Vues des employés.
* Pages dédiées aux pointages.
* Templates website pour les employés.
* Pages destinées aux responsables / managers.
* Affichage des informations synchronisées depuis Django.

---

# 🔄 Synchronisation Django → Odoo

La synchronisation est basée sur deux mécanismes principaux :

### XML-RPC

Utilisé par le service Django pour communiquer directement avec les modèles Odoo.

```text
Django
   │
   │ XML-RPC
   ▼
Odoo ORM
   │
   ▼
hr.employee
hr.pointage
```

### JSON API

Odoo expose également un endpoint permettant de recevoir des pointages :

```text
Django
   │
   │ HTTP / JSON
   ▼
/api/odoo/pointage/create
   │
   ▼
SMARTfront
```

---

# 🧪 État actuel du projet

| Étape | Fonctionnalité                      | État             |
| ----- | ----------------------------------- | ---------------- |
| 1     | Modèles Employee / Pointage / Leave | ✅ Terminé        |
| 2     | Logique `process_pointage`          | ✅ Terminé        |
| 3     | API / Views                         | ✅ Terminé        |
| 4     | Intégration Odoo                    | 🟢 Fonctionnelle |
| 5     | Tests automatisés                   | ⚠️ Partiel       |
| 6     | Durcissement production             | ⚠️ À améliorer   |

### 1. Modèles

Les modèles principaux sont implémentés avec les champs nécessaires, notamment :

* `odoo_employee_id`
* `odoo_field`
* `synced_to_odoo`
* `external_id`

### 2. Logique métier

La logique de traitement des pointages est fonctionnelle :

* IN / OUT
* Pauses
* Journées ignorées
* Fermeture automatique
* Transactions atomiques

### 3. API

Les API et vues utilisent la logique métier centralisée et évitent autant que possible la duplication.

La saisie peut provenir :

* d'une machine,
* d'un utilisateur,
* d'un PIN manuel,
* d'une API.

### 4. Intégration Odoo

Le chemin principal de synchronisation est fonctionnel :

* Correspondance des employés.
* Création des employés si nécessaire.
* Mapping des champs.
* Synchronisation des IN / OUT.
* Création des `hr.pointage`.
* Vérification des données synchronisées.

Des améliorations restent possibles pour :

* Synchronisation périodique automatique.
* Meilleur système de logs.
* Transactions batch plus robustes.
* Tests automatisés de l'intégration.

### 5. Tests

Les tests manuels peuvent être effectués depuis :

* Django shell.
* Commandes de synchronisation.
* Outils de diagnostic.

Les tests automatisés restent à développer pour couvrir notamment :

* Journées ignorées.
* Plusieurs employés.
* Pointages multiples.
* Cas `IN` / `OUT` inhabituels.
* Synchronisation répétée.
* Erreurs de communication avec Odoo.

---

# ⚠️ Limitations actuelles

Le projet est fonctionnel mais certains aspects nécessitent encore un durcissement avant une utilisation production.

### 🔐 Sécurité API

Certains endpoints publics utilisent actuellement :

```text
auth=none
```

Une authentification et une autorisation plus robustes doivent être mises en place avant un déploiement exposé sur Internet.

### 🧪 Tests

La couverture de tests automatisés est encore limitée.

### 📊 Logging

Le système pourrait bénéficier d'un système de logs plus structuré pour faciliter le diagnostic des problèmes de synchronisation.

### 🔄 Synchronisation

Une synchronisation périodique/automatique peut encore être améliorée afin de réduire les interventions manuelles.

### 🛡️ Production Hardening

Avant une utilisation en production, il est recommandé d'ajouter notamment :

* Rate limiting.
* Authentification forte des API.
* Validation stricte des données.
* Gestion centralisée des erreurs.
* Monitoring.
* Logs structurés.
* Gestion robuste des retries.
* Vérification des secrets et credentials.
* Nettoyage des caches et fichiers temporaires.

---

# 📝 Notes de développement

Le repository contient à la fois du code actif et plusieurs éléments utilisés pendant le développement :

* Scripts utilitaires.
* Scripts exploratoires.
* Snapshots `.txt`.
* Fichiers de diagnostic.
* Artefacts de référence.

Les dossiers générés tels que :

```text
__pycache__/
venv/
```

ne font pas partie de la documentation fonctionnelle du projet et sont volontairement exclus de la structure principale.

---

# 🚀 Installation rapide

## Prérequis

* Docker
* Docker Compose
* Git

---

## 1. Démarrer les services

Depuis la racine du projet :

```bash
docker-compose up -d
```

Les trois services seront lancés :

```text
postgres_db
odoo_app
django_app
```

---

## 2. Accéder aux applications

### Odoo

```text
http://localhost:8069
```

### Django

```text
http://localhost:8000
```

> ⚠️ Les identifiants d'administration ne doivent pas être conservés en dur dans la documentation ou dans le repository pour un environnement de production.

---

## 3. Initialiser Django

Depuis le conteneur Django :

```bash
python manage.py migrate
```

---

## 4. Tester la connexion Odoo

```bash
python manage.py test_odoo
```

---

## 5. Vérifier l'état de synchronisation

```bash
python sync_tool.py status
```

---

## 6. Synchroniser les pointages

```bash
python sync_tool.py sync
```

Cette commande pousse les enregistrements Django dont :

```text
synced_to_odoo = False
```

vers Odoo.

---

# ⚙️ Configuration

La configuration principale utilise les variables d'environnement.

Les paramètres Django/Odoo incluent notamment :

```text
ODOO_URL
ODOO_DB
ODOO_USERNAME
ODOO_PASSWORD
```

La configuration Docker est principalement définie dans :

```text
.env
docker-compose.yml
odoo.conf
```

### `odoo.conf`

Configure notamment :

* Connexion à PostgreSQL.
* Chemin des addons.
* Logging.
* Port XML-RPC.
* Paramètres du serveur Odoo.

---

# 📁 Structure du projet

```text
odooproject/
│
├── docker-compose.yml
├── odoo.conf
├── .env
├── deploy.sh
│
├── addons/
│   └── SMARTfront/
│       ├── controllers/
│       ├── models/
│       ├── views/
│       ├── security/
│       └── data/
│
└── django/
    └── pointage_machine/
        │
        ├── attendance/
        │   ├── models/
        │   ├── views/
        │   ├── services/
        │   ├── management/
        │   └── ...
        │
        ├── pointage_machine/
        │   ├── settings.py
        │   └── urls.py
        │
        ├── staticfiles/
        └── manage.py
```

---

# 📌 Technologies utilisées

* 🐍 Python
* Django
* Odoo 18
* PostgreSQL 15
* Docker
* Docker Compose
* XML-RPC
* REST / JSON
* Odoo ORM
* HTML / CSS / JavaScript

---

# 📄 Licence

Le module Odoo **SMARTfront** est distribué sous licence :

**LGPL-3**

La partie Django suit les conditions de licence définies par le projet.

---

# 🇬🇧 English

# 🕒 Odoo Attendance Sync System — Django + Odoo 18

> **Full-stack employee attendance and synchronization system built with Django, Odoo 18, and PostgreSQL.**

---

## 📋 Overview

**Odoo Attendance Sync System** is a full-stack employee attendance management solution based on a **Django + Odoo 18 + PostgreSQL** architecture.

The system separates attendance capture and business logic from HR management and back-office functionality.

**Django** receives or creates attendance events, stores them locally, determines whether each event is an `IN` or `OUT` event, and synchronizes the resulting records with Odoo using **XML-RPC** and **JSON endpoints**.

**Odoo 18** acts as the HR and back-office platform, providing employee records, attendance records, menus, security, and user-facing interfaces through the custom **SMARTfront** addon.

---

## 🏗️ Architecture

The system consists of three main Docker services:

| Service       | Role                                           |   Port |
| ------------- | ---------------------------------------------- | -----: |
| `postgres_db` | Shared PostgreSQL 15 database                  | `5432` |
| `odoo_app`    | Odoo 18 + SMARTfront addon                     | `8069` |
| `django_app`  | Django API, business logic and synchronization | `8000` |

### General Architecture

```text
                 ┌───────────────────────┐
                 │ Attendance / Machine  │
                 │ Web / API / Manual    │
                 └───────────┬───────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       Django        │
                  │                     │
                  │ API + Business Logic│
                  │ Local Attendance DB │
                  └──────────┬──────────┘
                             │
                             │ XML-RPC / JSON
                             ▼
                  ┌─────────────────────┐
                  │       Odoo 18       │
                  │                     │
                  │ HR + SMARTfront     │
                  │ Attendance Records  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     PostgreSQL      │
                  │     Persistence     │
                  └─────────────────────┘
```

---

# 🔄 End-to-End Flow

The complete attendance flow is:

1. An attendance event arrives from a machine, API, web interface, or manual entry.
2. Django resolves the employee using their **PIN**.
3. Business logic determines whether the event is an `IN` or `OUT`.
4. The attendance record is stored locally with `synced_to_odoo=False`.
5. The synchronization system finds unsynchronized records.
6. Django sends the attendance data to Odoo using XML-RPC or JSON.
7. Odoo creates or updates the corresponding records.
8. Attendance information becomes available through the Odoo interface.
9. Django updates the synchronization state.

```text
Attendance Event
      │
      ▼
Django API / Machine
      │
      ▼
Employee resolution by PIN
      │
      ▼
Determine IN / OUT
      │
      ▼
Local Pointage
synced_to_odoo = False
      │
      ▼
Synchronization
      │
      ├──────────────► XML-RPC
      │
      └──────────────► JSON Endpoint
                            │
                            ▼
                       Odoo 18
                            │
                            ▼
                       hr.pointage
```

---

# 🧩 Project Components

## 🐍 Django

Main directory:

```text
django/pointage_machine/
```

Django provides the main attendance processing and synchronization logic.

### 📦 Models

#### `Employee`

Represents employees stored on the Django side.

Main information includes:

* `pin`
* `name`
* Odoo employee reference when available

#### `Pointage`

Represents an attendance event.

Main fields include:

* `employee`
* `check_time`
* `state`
* `source`
* `anomaly`
* `synced_to_odoo`
* `external_id`
* `odoo_employee_id`
* `odoo_field`

Main states:

```text
IN
OUT
```

#### `Leave`

Provides basic leave/absence tracking.

---

# ⚙️ Business Logic

The main business logic is implemented in:

```text
attendance/pointage_service.py
```

It is responsible for:

* Creating attendance records.
* Resolving employees.
* Determining `IN` / `OUT`.
* Handling lunch breaks.
* Handling skipped days.
* Automatically closing open attendance periods when required.
* Maintaining transactional consistency.

The API/views are intentionally kept thin and delegate processing to the service layer.

---

# 🔗 Odoo Integration

The main Django integration service is:

```text
attendance/odoo_service.py
```

It provides the Odoo communication layer.

Main capabilities include:

* Odoo authentication.
* Employee search.
* Employee creation.
* Attendance search.
* Attendance creation.
* Data updates.
* Synchronization verification.
* XML-RPC communication.

A synchronization utility is also available to push unsynchronized Django records to Odoo.

---

# 🌐 Django API / Views

The Django API provides functionality such as:

* ❤️ Health check.
* 📋 Attendance listing.
* 🏠 Dashboard / home page.
* 🔌 Attendance endpoints.
* 🔄 Synchronization tools.
* 🧪 Testing and diagnostic commands.

The views delegate business processing to the service layer to avoid duplicated logic.

---

# 🏢 Odoo Addon — SMARTfront

The custom Odoo module is located at:

```text
addons/SMARTfront/
```

It provides the Odoo-side functionality of the system.

## 👤 `hr.employee` Extension

The standard Odoo employee model is extended with fields including:

* `pin`
* `django_id`

The PIN establishes the mapping between Django and Odoo employees.

---

## 🕒 `hr.pointage`

The addon introduces:

```text
hr.pointage
```

This model represents attendance records inside Odoo.

Main fields include:

* `employee`
* `date`
* `check_in`
* `check_out`
* `state`
* `note`
* `django_id`

The `django_id` field identifies the originating Django record and helps prevent duplicate synchronization.

---

## ⚙️ SMARTfront Configuration

The:

```text
smartfront.config
```

model stores integration-related settings such as:

* `api_key`
* `webhook_url`
* `sync_interval`
* `auto_validate`

---

# 🌐 Odoo API Endpoint

The addon exposes:

```text
/api/odoo/pointage/create
```

This endpoint allows Django to send attendance data to Odoo using JSON.

---

# 🖥️ Odoo User Interface

SMARTfront provides:

* Attendance management menus.
* Backend views.
* Employee views.
* Attendance pages.
* Employee website templates.
* Manager / DG pages.
* Display of synchronized Django attendance data.

---

# 🔄 Django → Odoo Synchronization

The system uses two main integration mechanisms.

### XML-RPC

The Django service can communicate directly with the Odoo ORM:

```text
Django
   │
   │ XML-RPC
   ▼
Odoo ORM
   │
   ▼
hr.employee
hr.pointage
```

### JSON API

Odoo also provides a JSON endpoint:

```text
Django
   │
   │ HTTP / JSON
   ▼
/api/odoo/pointage/create
   │
   ▼
SMARTfront
```

---

# 🧪 Current Project Status

| Step | Feature                            | Status         |
| ---- | ---------------------------------- | -------------- |
| 1    | Employee / Pointage / Leave models | ✅ Done         |
| 2    | `process_pointage` business logic  | ✅ Done         |
| 3    | API / Views                        | ✅ Done         |
| 4    | Odoo integration                   | 🟢 Functional  |
| 5    | Automated testing                  | ⚠️ Partial     |
| 6    | Production hardening               | ⚠️ In progress |

### 1. Models

The core models are implemented with the required fields, including:

* `odoo_employee_id`
* `odoo_field`
* `synced_to_odoo`
* `external_id`

### 2. Business Logic

The attendance processing logic is implemented, including:

* IN / OUT handling.
* Lunch breaks.
* Skipped days.
* Automatic closing.
* Atomic transactions.

### 3. API

The API and views rely on centralized business logic and avoid unnecessary duplication.

Attendance can originate from:

* A machine.
* A user.
* Manual PIN entry.
* An API.

### 4. Odoo Integration

The main synchronization path is functional:

* Employee mapping.
* Employee creation when required.
* Field mapping.
* IN / OUT synchronization.
* `hr.pointage` creation.
* Synchronization verification.

Possible future improvements include:

* Automatic periodic synchronization.
* Improved logging.
* More robust batch transactions.
* Automated integration tests.

### 5. Testing

Manual validation can currently be performed through:

* Django shell.
* Synchronization commands.
* Diagnostic utilities.

Automated tests still need to cover areas such as:

* Skipped days.
* Multiple employees.
* Multiple attendance events.
* Unusual IN / OUT sequences.
* Repeated synchronization.
* Odoo communication failures.

---

# ⚠️ Current Limitations

The project has a functional core but still requires additional hardening before production deployment.

### 🔐 API Security

Some endpoints currently use:

```text
auth=none
```

Stronger authentication and authorization should be implemented before exposing these endpoints publicly.

### 🧪 Automated Testing

Automated test coverage is currently limited.

### 📊 Logging

A more structured logging system would improve synchronization monitoring and troubleshooting.

### 🔄 Synchronization

Automatic periodic synchronization can be further improved to reduce manual intervention.

### 🛡️ Production Hardening

Recommended improvements include:

* API rate limiting.
* Strong API authentication.
* Strict input validation.
* Centralized error handling.
* Monitoring.
* Structured logging.
* Retry mechanisms.
* Secure secret management.
* Cleanup of caches and temporary files.

---

# 📝 Development Notes

The repository contains both active project code and development/reference artifacts, including:

* Utility scripts.
* Exploratory scripts.
* `.txt` snapshots.
* Diagnostic files.
* Reference artifacts.

Generated directories such as:

```text
__pycache__/
venv/
```

are intentionally excluded from the main project documentation.

---

# 🚀 Quick Start

## Prerequisites

* Docker
* Docker Compose
* Git

---

## 1. Start the services

From the project root:

```bash
docker-compose up -d
```

The following services will start:

```text
postgres_db
odoo_app
django_app
```

---

## 2. Access the applications

### Odoo

```text
http://localhost:8069
```

### Django

```text
http://localhost:8000
```

> ⚠️ Administrative credentials should never be hard-coded in documentation or committed to the repository for production deployments.

---

## 3. Run Django migrations

Inside the Django container:

```bash
python manage.py migrate
```

---

## 4. Test Odoo connectivity

```bash
python manage.py test_odoo
```

---

## 5. Check synchronization status

```bash
python sync_tool.py status
```

---

## 6. Synchronize attendance records

```bash
python sync_tool.py sync
```

This command pushes Django records where:

```text
synced_to_odoo = False
```

to Odoo.

---

# ⚙️ Configuration

The project primarily uses environment variables for configuration.

Django/Odoo settings include:

```text
ODOO_URL
ODOO_DB
ODOO_USERNAME
ODOO_PASSWORD
```

Main configuration files:

```text
.env
docker-compose.yml
odoo.conf
```

### `odoo.conf`

Controls settings such as:

* PostgreSQL connection.
* Addons path.
* Logging.
* XML-RPC port.
* Odoo server configuration.

---

# 📁 Project Structure

```text
odooproject/
│
├── docker-compose.yml
├── odoo.conf
├── .env
├── deploy.sh
│
├── addons/
│   └── SMARTfront/
│       ├── controllers/
│       ├── models/
│       ├── views/
│       ├── security/
│       └── data/
│
└── django/
    └── pointage_machine/
        │
        ├── attendance/
        │   ├── models/
        │   ├── views/
        │   ├── services/
        │   ├── management/
        │   └── ...
        │
        ├── pointage_machine/
        │   ├── settings.py
        │   └── urls.py
        │
        ├── staticfiles/
        └── manage.py
```

---

# 📌 Technologies

* 🐍 Python
* Django
* Odoo 18
* PostgreSQL 15
* Docker
* Docker Compose
* XML-RPC
* REST / JSON
* Odoo ORM
* HTML / CSS / JavaScript

---

# 📄 License

The **SMARTfront** Odoo module is released under the:

**LGPL-3 License**

The Django component follows the project's applicable licensing terms.
