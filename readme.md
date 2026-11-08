# 🌐 Novapolis Résilience - Planification des Secours et Conception d'un Réseau Urbain Résilient

**Projet intégrateur (ING-APP1-BDML) en Algorithmique et Théorie des Graphes.**

Ce projet fournit une application complète (**API FastAPI + Interface Web Cartographique + CLI**) pour analyser le réseau de la métropole de Novapolis, évaluer l'accessibilité des sites sensibles, calculer des itinéraires de secours optimaux sous contraintes de pannes, et concevoir un réseau de fibre optique résilient.a

## 📑 Table des Matières

- [🌐 Novapolis Résilience - Planification des Secours et Conception d'un Réseau Urbain Résilient](#-novapolis-résilience---planification-des-secours-et-conception-dun-réseau-urbain-résilient)
  - [📑 Table des Matières](#-table-des-matières)
  - [👥 Auteurs \& Réalisation](#-auteurs--réalisation)
  - [🏗️ Architecture \& Structure du Projet](#️-architecture--structure-du-projet)
  - [🛠️ Technologies \& Librairies Principales](#️-technologies--librairies-principales)
  - [🚀 Prérequis et Installation (Docker \& Local)](#-prérequis-et-installation-docker--local)
    - [Option 1 : Démarrage rapide avec Docker Compose (Recommandé)](#option-1--démarrage-rapide-avec-docker-compose-recommandé)
    - [Option 2 : Installation Manuelle (Environnement Local Python)](#option-2--installation-manuelle-environnement-local-python)
  - [🗄️ Génération des Données](#️-génération-des-données)
  - [🖥️ Présentation de l'Interface Web Interactive](#️-présentation-de-linterface-web-interactive)
  - [💻 Utilisation de l'Interface en Ligne de Commande (CLI)](#-utilisation-de-linterface-en-ligne-de-commande-cli)
    - [1. Diagnostic global d'accessibilité (Module 1)](#1-diagnostic-global-daccessibilité-module-1)
    - [2. Calcul d'un itinéraire de secours sous contraintes (Module 2)](#2-calcul-dun-itinéraire-de-secours-sous-contraintes-module-2)
    - [3. Analyse des arbres couvrants minimaux multiples (Module 4.4)](#3-analyse-des-arbres-couvrants-minimaux-multiples-module-44)
    - [4. Vérification des circuits absorbants (Module 3)](#4-vérification-des-circuits-absorbants-module-3)
  - [🌐 Lancement du Serveur Web et de l'API](#-lancement-du-serveur-web-et-de-lapi)
  - [⚙️ Détails des Modules Algorithmiques](#️-détails-des-modules-algorithmiques)
  - [🧪 Exécution des Tests Unitaires](#-exécution-des-tests-unitaires)
    - [1. En environnement local :](#1-en-environnement-local-)
    - [2. Via Docker Compose :](#2-via-docker-compose-)

## 👥 Auteurs & Réalisation

Ce projet a été conçu et développé dans le cadre du cursus **ING-APP-BDML1 (2026–2027)** par :

* **Paul LEFORT**
* **Ludovic GERMAIN**


## 🏗️ Architecture & Structure du Projet

L'architecture logicielle sépare strictement la lecture des données, les algorithmes mathématiques, les services métier, les routeurs d'exposition API et l'interface web interactive :

```text
novapolis/
│
├── app/                          # Cœur de l'application Backend (FastAPI)
│   ├── algorithme/               # Implémentation des algorithmes de graphes & résilience
│   │   ├── helper.py             # Centralisation de la lecture CSV et conversion JSON/NetworkX
│   │   ├── resilience_service.py # Logique métier (diagnostics, scénarios, ACM multiples)
│   │   ├── traversal.py          # Parcours faits main (BFS, DFS, composantes, cycles)
│   │   ├── shortest_paths.py     # Plus courts chemins (Dijkstra, Bellman-Ford, Floyd-Warshall)
│   │   ├── dijkstra.py           # Wrapper algo Dijkstra
│   │   ├── bellman_ford.py       # Wrapper algo Bellman-Ford
│   │   ├── floyd_warshall.py     # Wrapper algo Floyd-Warshall
│   │   ├── bfs.py                # Wrapper algo BFS
│   │   ├── dfs.py                # Wrapper algo DFS
│   │   ├── kruskal.py            # Wrapper algo Kruskal
│   │   └── prim.py               # Wrapper algo Prim
│   │
│   ├── routers/                  # Contrôleurs et routes API REST
│   │   ├── api.py                # Routeur principal des graphes et fichiers bruts
│   │   ├── resilience.py         # Routeur de résilience et scénarios d'intervention
│   │   ├── fibre.py              # Routeur de gestion de la fibre et pannes de tronçons
│   │   ├── benchmark.py          # Routeur de mesures de performance (complexité)
│   │   ├── imports.py            # Routeur d'importation de fichiers personnalisés
│   │   ├── download.py           # Routeur de téléchargement et génération de réseaux
│   │   └── pages.py              # Routeur d'affichage des templates HTML
│   │
│   ├── generation/               # Scripts de génération aléatoire des fichiers CSV
│   │   ├── genererSite.py        # Génération des nœuds/sites
│   │   ├── genererRoute.py       # Génération des tracés routiers
│   │   ├── genererFibre.py       # Génération des liaisons fibre optique
│   │   └── reseau.py             # Assemblage global du réseau
│   │
│   ├── config.py                 # Variables d'environnement et configuration
│   ├── main.py                   # Point d'entrée de l'application FastAPI
│   └── templating.py             # Configuration du moteur de templates Jinja2
│
├── static/                       # Ressources statiques Frontend
│   ├── css/                      # Feuilles de style (style.css)
│   └── js/                       # Logique client modulaire (ES6)
│       ├── features/             # Modules métiers (algos, circuits, fibre, intervention, etc.)
│       ├── map/                  # Gestion de la carte interactive et surbrillances
│       ├── ui/                   # Composants d'interface (sidebar, modales, résultats)
│       ├── api.js                # Client HTTP pour communiquer avec FastAPI
│       └── state.js              # Gestion de l'état global de l'interface
│
├── templates/                    # Vues HTML (Jinja2)
│   ├── index.html                # Page principale de l'application
│   └── partials/                 # Composants HTML réutilisables (onglets, modales)
│
├── test/                         # Suite de tests unitaires modulaires (pytest)
│   ├── conftest.py               # Fixtures et données de test partagées
│   ├── test_unitaire.py          # Suite globale de tests unitaires
│   ├── test_helper.py            # Tests des utilitaires et du chargement CSV
│   ├── test_bfs.py / test_dfs.py # Tests des parcours de graphes
│   ├── test_dijkstra.py          # Tests de l'algorithme Dijkstra
│   ├── test_bellman_ford.py      # Tests de l'algorithme Bellman-Ford
│   ├── test_floyd_warshall.py    # Tests de l'algorithme Floyd-Warshall
│   └── test_kruskal.py / prim.py # Tests des arbres couvrants minimaux
│
├── cli.py                        # Interface en ligne de commande (CLI) complète
├── Dockerfile                    # Image Docker de l'application
├── docker-compose.yml            # Orchestration des conteneurs
├── requirements.txt              # Dépendances Python
├── .env.example                  # Modèle de configuration d'environnement
└── README.md                     # Documentation du projet
```

## 🛠️ Technologies & Librairies Principales

Le projet s'appuie sur un écosystème Python moderne (défini dans `requirements.txt`) :

* **FastAPI** : Framework web asynchrone haute performance pour l'API REST.
* **Uvicorn** : Serveur ASGI rapide pour l'exécution de l'application.
* **NetworkX** : Manipulation, modélisation et validation des structures de graphes.
* **Jinja2** : Moteur de templates pour le rendu dynamique des vues HTML.
* **Pydantic** : Validation des données et gestion des schémas d'entrée/sortie.
* **Pytest** : Framework de tests unitaires et fonctionnels.
* **Docker & Docker Compose** : Conteneurisation et déploiement reproductible.

## 🚀 Prérequis et Installation (Docker & Local)

### Option 1 : Démarrage rapide avec Docker Compose (Recommandé)

Assurez-vous d'avoir installé **Docker** et **Docker Compose** sur votre machine.

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/Paul-Lefort/Novapolis-R-silience
   ```

2. **Configurer l'environnement** :
   Copiez le fichier d'exemple pour créer votre fichier de configuration local :
   ```bash
   cp .env.example .env
   ```

3. **Construire et démarrer les conteneurs** :
   ```bash
   docker-compose up --build -d
   ```

4. **Accéder à l'application** :
   * **Interface Web :** `http://localhost:8000/`
   * **Documentation interactive de l'API (Swagger) :** `http://localhost:8000/docs`

### Option 2 : Installation Manuelle (Environnement Local Python)

1. **Vérifier la version de Python** : Assurez-vous d'avoir installé **Python 3.10** ou une version ultérieure.

2. **Créer et activer un environnement virtuel** :
   ```bash
   python -m venv venv
   
   # Sur Linux / macOS :
   source venv/bin/activate
   
   # Sur Windows :
   venv\Scripts\activate
   ```

3. **Installer les dépendances requises** :
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## 🗄️ Génération des Données

Avant d'exécuter des analyses, le réseau doit être présent sur le disque (fichiers `sites.csv`, `routes.csv`, `fibre.csv`). Vous pouvez générer un réseau réaliste (par défaut 120 sites et 305 connexions, modulable jusqu'à 2000 sites) directement depuis le bouton **"Générer un jeu de données"** en haut à droite de l'interface web, via l'API ou via la commande suivante :

```bash
python -c "from app.generation.genererSite import generer_csv_sites; from app.generation.genererRoute import generer_csv_routes; from app.generation.genererFibre import generer_csv_fibre; generer_csv_sites('sites.csv', 150); generer_csv_routes('sites.csv', 'routes.csv', 210); generer_csv_fibre('sites.csv', 'fibre.csv', 180)"
```

## 🖥️ Présentation de l'Interface Web Interactive

L'interface graphique propose une carte interactive zoomable accompagnée d'un panneau latéral regroupant l'ensemble des outils d'analyse :

* **Double Vue Cartographique & Légende Dynamique :**
  * **Réseau Routier (Graphe orienté) :** Visualisation des casernes, des routes ouvertes (bleu), des routes saturées (rouge), des axes en travaux/maintenance (pointillés orange) ainsi que du sens de circulation des liaisons.
  * **Réseau Fibre Optique (Graphe non orienté) :** Visualisation de la fibre active (vert) et de la fibre en cours de déploiement (pointillés gris).
* **Algorithmes de Cheminement :** Sélection interactive d'un sommet de départ et d'arrivée directement sur la carte pour calculer et tracer le plus court chemin (Dijkstra, Bellman-Ford, Floyd-Warshall, BFS/DFS).
* **Planification des Interventions :** Simulation de fermeture manuelle d'axes routiers et comparaison des itinéraires de secours selon différents critères (durée normale, heure de pointe, distance).
* **Conception Réseau Fibre (ACM) :** Calcul de l'Arbre Couvrant Minimal via **Kruskal (Union-Find)** ou **Prim**, comparaison des performances, détection des coûts égaux (ACM multiples) et simulation de panne sur un tronçon $(U, V)$ pour identifier le lien de secours optimal.
* **Résilience et Scénarios :** Évaluation comparative automatisée sur un échantillon de demandes (par défaut 30 sites sensibles) confrontant la *situation normale*, la *fermeture d'un axe routier critique* et la *panne d'un tronçon de fibre*.
* **Circuits Absorbants :** Exécution d'un jeu de tests dédiés validant le comportement de Bellman-Ford et Floyd-Warshall face à des graphes contenant des circuits de poids négatif.
* **Diagnostic & Accessibilité :** Rapport global sur la topologie (nombre de sites et connexions), couverture depuis les casernes, composantes connexes et mise en surbrillance des zones hors portée.
* **Import / Export & Benchmarks :** Téléchargement des jeux de données CSV, importation de graphes personnalisés et mesure des temps d'exécution algorithmiques.

## 💻 Utilisation de l'Interface en Ligne de Commande (CLI)

Le script `cli.py` permet d'exécuter l'ensemble des modules algorithmiques directement depuis votre terminal sans lancer le serveur web.

### 1. Diagnostic global d'accessibilité (Module 1)
Permet d'analyser les sites accessibles depuis les casernes, les composantes de fibre et les cycles orientés :
```bash
python cli.py diagnostic --view routier
```

### 2. Calcul d'un itinéraire de secours sous contraintes (Module 2)
Permet de calculer un plus court chemin entre deux sommets (ex: de la caserne `1` au site `14`) en choisissant l'algorithme et le critère de coût (`temps_normal`, `temps_pointe`, ou `distance`), avec possibilité de fermer des axes manuellement :
```bash
python cli.py intervention --start 1 --target 14 --algo dijkstra --critere temps_normal --arcs "3->16,16->3"
```

### 3. Analyse des arbres couvrants minimaux multiples (Module 4.4)
Permet d'étudier les coûts égaux et d'identifier les arêtes interchangeables dans le réseau de fibre :
```bash
python cli.py fibre-ties
```

### 4. Vérification des circuits absorbants (Module 3)
Exécute la suite de tests artificiels validant le comportement de Bellman-Ford et Floyd-Warshall face à des poids négatifs :
```bash
python cli.py test-cycles
```

## 🌐 Lancement du Serveur Web et de l'API

Si vous utilisez une installation locale (hors Docker), démarrez l'application interactive et l'API REST avec support des logs Uvicorn :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Une fois le serveur lancé :
* **Interface graphique :** Ouvrez `http://localhost:8000/` dans votre navigateur.
* **Documentation interactive (Swagger) :** Accédez à `http://localhost:8000/docs`.

## ⚙️ Détails des Modules Algorithmiques

* **Module 1 (BFS / DFS) :** Utilisé pour l'accessibilité multi-sources, la connexité de la fibre, la recherche du chemin minimisant le nombre d'arcs, et la détection des cycles par coloration à 3 états.
* **Module 2 (Dijkstra, Bellman-Ford, Floyd-Warshall) :** Calcul des plus courts chemins de secours avant/après perturbation. Évaluation rigoureuse des retards absolus et relatifs.
* **Module 3 (Circuits absorbants) :** Gestion de l'état `moins_infini` pour empêcher l'affichage de valeurs aberrantes en présence de boucles de poids négatif accessibles.
* **Module 4 (Kruskal & Prim) :** Calcul d'Arbres Couvrants Minimaux (ACM) sur le graphe non orienté de la fibre, gestion des forêts de raccordement et simulation de pannes de tronçons avec calcul de secours optimal.
* **Module 5 (Résilience et Benchmarks) :** Comparaison de scénarios de perturbation (situation normale vs axe fermé vs panne de fibre) mesurant l'augmentation des temps de trajet et l'enclavement des zones sensibles. Les benchmarks mesurent les performances réelles sur 5 répétitions en excluant les phases d'E/S disque.

## 🧪 Exécution des Tests Unitaires

Le projet dispose d'une suite complète de tests unitaires modulaires (basée sur **Pytest**) pour garantir la fiabilité des algorithmes et services métier. Chaque composant possède des tests isolés intégrant des méthodes de cycle de vie (`setup_method` / `teardown_method`) ainsi que des fixtures partagées (`conftest.py`).

### 1. En environnement local :
Pour exécuter **tous les tests** en un seul coup avec un affichage détaillé et la visualisation des logs de cycle de vie :
```bash
pytest -v -s
```

Pour exécuter les tests d'un fichier ou d'un algorithme spécifique (par exemple `test_unitaire.py` ou `test_dijkstra.py`) :
```bash
pytest test/test_unitaire.py -v -s
# ou
pytest tests/test_dijkstra.py -v -s
```

### 2. Via Docker Compose :
Vous pouvez exécuter les tests directement dans l'environnement isolé du conteneur :
```bash
docker-compose exec web pytest 
```
*(Note : si les conteneurs ne sont pas lancés, utilisez `docker-compose run --rm web pytest -v -s`, en adaptant `web` au nom du service défini dans votre `docker-compose.yml`).*