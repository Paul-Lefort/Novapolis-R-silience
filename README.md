# Novapolis — microservices simplifiés

Chaque algorithme est un microservice autonome composé de deux fichiers : `main.py` (API + validation + algorithme) et `Dockerfile` (construction du conteneur).

## Installation
Copiez les sept dossiers `dfs`, `bfs`, `dijkstra`, `bellman_ford`, `floyd_warshall`, `kruskal` et `prim` dans `NOVAPOLIS/microservices/`.

## API
- `GET /health`
- `POST /run` avec un corps JSON contenant `graph` (directed=false, nodes, edges avec source/target/weight, et `start` pour DFS/BFS/Dijkstra/Bellman-Ford).

Les services renvoient `steps`, `step_count` et `result`. Le frontend peut donc appeler le service une seule fois, conserver `steps`, puis afficher les états avec Précédent/Suivant sans WebSocket ni nouveau calcul.

Dépendances installées directement dans chaque Dockerfile : FastAPI, Uvicorn et Pydantic. Aucun `requirements.txt` n'est nécessaire.
