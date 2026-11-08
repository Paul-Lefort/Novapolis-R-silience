# Novapolis Résilience - Planification des Secours et Conception d'un Réseau Urbain Résilient

Projet intégrateur (ING-APP1-BDML) en Algorithmique et Théorie des Graphes.  
Ce projet fournit une application complète (API FastAPI + Interface web + CLI) pour analyser le réseau de la métropole de Novapolis, évaluer l'accessibilité des sites sensibles, calculer des itinéraires de secours optimaux sous contraintes de pannes, et concevoir un réseau de fibre optique résilient.

---

## Table des Matières

1. [Structure du Projet](#-structure-du-projet)
2. [Prérequis et Installation](#-prérequis-et-installation)
3. [Génération des Données](#-génération-des-données)
4. [Utilisation de l'Interface en Ligne de Commande (CLI)](#-utilisation-de-linterface-en-ligne-de-commande-cli)
5. [Lancement du Serveur Web et de l'API](#-lancement-du-serveur-web-et-de-lapi)
6. [Détails des Modules Algorithmiques](#-détails-des-modules-algorithmiques)
7. [Exécution des Tests Unitaires](#-exécution-des-tests-unitaires)

---

## Structure du Projet

L'architecture logicielle sépare strictement la lecture des données, les algorithmes, les services métier et les routeurs d'exposition :

```text
novapolis/
│
├── app/
│   ├── algorithme/
│   │   ├── helper.py          # Centralisation de la lecture CSV et conversion JSON/NetworkX
│   │   ├── resilience_service.py # Logique métier (diagnostics, scénarios, ACM multiples)
│   │   ├── traversal.py       # Parcours faits main (BFS, DFS, composantes, cycles)
│   │   ├── shortest_paths.py  # Plus courts chemins (Dijkstra, Bellman-Ford, Floyd-Warshall)
│   │   ├── dijkstra.py        # Wrapper algo
│   │   ├── bellman_ford.py    # Wrapper algo
│   │   ├── floyd_warshall.py  # Wrapper algo
│   │   ├── bfs.py             # Wrapper algo
│   │   ├── dfs.py             # Wrapper algo
│   │   ├── kruskal.py         # Wrapper algo
│   │   └── prim.py            # Wrapper algo
│   │
│   ├── routers/
│   │   ├── api.py             # Routeur principal des graphes et fichiers bruts
│   │   ├── resilience.py      # Routeur de résilience et scénarios d'intervention
│   │   ├── fibre.py           # Routeur de gestion de la fibre et pannes de tronçons
│   │   ├── benchmark.py       # Routeur de mesures de performance (complexité)
│   │   ├── imports.py         # Routeur d'importation de fichiers personnalisés
│   │   ├── download.py        # Routeur de téléchargement et génération de réseaux
│   │   └── pages.py           # Routeur d'affichage des templates HTML
│   │
│   └── generation/            # Scripts de génération aléatoire des fichiers CSV (sites, routes, fibre)
│
├── tests/                     # Suite de tests unitaires modulaires (pytest)
│   ├── conftest.py            # Fixtures et données de test partagées
│   ├── test_helper.py         # Tests des utilitaires et du chargement CSV
│   ├── test_bfs.py            # Tests de l'algorithme BFS
│   ├── test_dfs.py            # Tests de l'algorithme DFS
│   ├── test_dijkstra.py       # Tests de l'algorithme Dijkstra
│   ├── test_bellman_ford.py   # Tests de l'algorithme Bellman-Ford
│   ├── test_floyd_warshall.py # Tests de l'algorithme Floyd-Warshall
│   ├── test_kruskal.py        # Tests de l'algorithme Kruskal
│   └── test_prim.py           # Tests de l'algorithme Prim
│
├── cli.py                     # Interface en ligne de commande (CLI) complète
├── requirements.txt           # Dépendances Python
└── README.md                  # Documentation du projet
```

---

## Prérequis et Installation

1. Assurez-vous d'avoir installé **Python 3.10** ou une version ultérieure.
2. Clonez le dépôt et installez les dépendances requises :

```bash
pip install -r requirements.txt
```

---

## Génération des Données

Avant d'exécuter des analyses, le réseau doit être présent sur le disque (fichiers `sites.csv`, `routes.csv`, `fibre.csv`). Vous pouvez générer un réseau réaliste (par défaut 120 sites, modulable jusqu'à 2000) via l'API ou le script de génération :

```bash
python -c "from app.generation.genererSite import generer_csv_sites; from app.generation.genererRoute import generer_csv_routes; from app.generation.genererFibre import generer_csv_fibre; generer_csv_sites('sites.csv', 150); generer_csv_routes('sites.csv', 'routes.csv', 210); generer_csv_fibre('sites.csv', 'fibre.csv', 180)"
```

---

## Utilisation de l'Interface en Ligne de Commande (CLI)

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

---

## Lancement du Serveur Web et de l'API

Pour démarrer l'application interactive et l'API REST avec support des logs Uvicorn :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Une fois le serveur lancé :
- **Interface graphique :** Ouvrez `http://localhost:8000/` dans votre navigateur.
- **Documentation interactive (Swagger) :** Accédez à `http://localhost:8000/docs`.

---

## Détails des Modules Algorithmiques

- **Module 1 (BFS / DFS) :** Utilisé pour l'accessibilité multi-sources, la connexité de la fibre, la recherche du chemin minimisant le nombre d'arcs, et la détection des cycles par coloration à 3 états.
- **Module 2 (Dijkstra, Bellman-Ford, Floyd-Warshall) :** Calcul des plus courts chemins de secours avant/après perturbation. Évaluation rigoureuse des retards absolus et relatifs.
- **Module 3 (Circuits absorbants) :** Gestion de l'état `moins_infini` pour empêcher l'affichage de valeurs aberrantes en présence de boucles de poids négatif accessibles.
- **Module 4 (Kruskal & Prim) :** Calcul d'Arbres Couvrants Minimaux (ACM) sur le graphe non orienté de la fibre, gestion des forêts de raccordement et simulation de pannes de tronçons avec calcul de secours optimal.
- **Module 5 (Résilience et Benchmarks) :** Comparaison de scénarios de perturbation (situation normale vs axe fermé vs panne de fibre) mesurant l'augmentation des temps de trajet et l'enclavement des zones sensibles. Les benchmarks mesurent les performances réelles sur 5 répétitions en excluant les phases d'E/S disque.

---

## Exécution des Tests Unitaires

Le projet dispose d'une suite complète de tests unitaires modulaires localisée dans le dossier `tests/`. Chaque composant et algorithme possède son propre fichier de test isolé, intégrant des méthodes de cycle de vie (`setup_method` / `teardown_method`).

Pour exécuter **tous les tests** en un seul coup avec un affichage détaillé et la visualisation des logs de cycle de vie :
```bash
pytest -v -s
```

Pour exécuter les tests d'un module ou d'un algorithme spécifique (par exemple Dijkstra) :
```bash
pytest tests/test_dijkstra.py -v -s
```