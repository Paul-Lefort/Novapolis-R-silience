import csv
import random

from app.generation.reseau import orienter, construire_graphe, haversine_km, lire_sites


def generer_csv_fibre(sites_filepath="sites.csv", fibre_filepath="fibre.csv", nombre_fibres=None):
    """Réseau fibre : topologie locale (câbles courts), coût proportionnel à la longueur.

    - faiblement connexe, NON fortement connexe
    - degré (in+out) max 3
    - jitter plus fort que pour les routes : la fibre ne suit pas exactement les routes
    """
    try:
        sites = lire_sites(sites_filepath)
    except FileNotFoundError:
        print(f"[ERREUR] Le fichier '{sites_filepath}' est introuvable. Générez-le d'abord !")
        return
    if len(sites) < 2:
        print("[INFO] Pas assez de sites pour créer des liaisons.")
        return

    DG = orienter(construire_graphe(sites, nombre_fibres, jitter=0.5))

    fibres = []
    for u, v in DG.edges():
        km = haversine_km(sites[u], sites[v])
        cost = max(500, round(km * random.uniform(800, 1500)))  # €/km
        statut = random.choices(["actif", "en_maintenance", "deploiement"], weights=[80, 10, 10])[0]
        fibres.append({"u": u, "v": v, "distance_km": round(km, 2), "cost": cost, "statut": statut})

    champs = ["u", "v", "distance_km", "cost", "statut"]
    with open(fibre_filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(fibres)
    print(f"[SUCCÈS] '{fibre_filepath}' généré ({len(fibres)} liaisons, sans croisement).")