import csv
import random

from app.generation.reseau import construire_graphe, haversine_km, lire_sites, orienter


def generer_csv_routes(sites_filepath="sites.csv", routes_filepath="routes.csv", nombre_routes=None):
    """Réseau routier : liaisons courtes, sans croisement, temps basés sur la distance réelle."""
    try:
        sites = lire_sites(sites_filepath)
    except FileNotFoundError:
        print(f"[ERREUR] Le fichier '{sites_filepath}' est introuvable.")
        return
    if len(sites) < 2:
        return

    DG = orienter(construire_graphe(sites, nombre_routes, jitter=0.15))

    routes = []
    for u, v in DG.edges():
        km = haversine_km(sites[u], sites[v])
        vitesse = random.uniform(30, 70)  # km/h
        temps_normal = max(1, round(km / vitesse * 60))
        temps_pointe = max(temps_normal, round(temps_normal * random.uniform(1.2, 2.5)))
        statut = random.choices(["ouvert", "saturé", "travaux"], weights=[80, 12, 8])[0]
        routes.append({
            "u": u, "v": v, "distance_km": round(km, 2),
            "temps_normal": temps_normal, "temps_pointe": temps_pointe, "statut": statut,
        })

    champs = ["u", "v", "distance_km", "temps_normal", "temps_pointe", "statut"]
    with open(routes_filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(routes)
    print(f"[SUCCÈS] '{routes_filepath}' généré ({len(routes)} routes, sans croisement).")