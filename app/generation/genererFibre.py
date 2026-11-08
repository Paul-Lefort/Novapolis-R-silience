import csv
import random

from app.generation.reseau import construire_graphe, haversine_km, lire_sites

STATUTS = ["disponible", "travaux", "inondable", "panne", "interdit"]
POIDS = [90, 4, 3, 2, 1]
COUT_KM = (40, 120)   # UNITÉ : k€ par km (hypothèse de génération, à justifier dans le rapport)


def generer_csv_fibre(sites_filepath="sites.csv", fibre_filepath="fibre.csv", nombre_fibres=None,
                      degre_max=3, seed=0):
    """Réseau fibre NON ORIENTÉ : câbles courts, coût (k€) proportionnel à la longueur.

    Une ligne par tronçon {u,v} (u < v). Statuts : disponible | travaux | inondable | panne | interdit.
    Le jitter (0.5) est plus fort que pour les routes : la fibre ne suit pas exactement les routes.
    """
    try:
        sites = lire_sites(sites_filepath)
    except FileNotFoundError:
        print(f"[ERREUR] Le fichier '{sites_filepath}' est introuvable. Générez-le d'abord !")
        return None
    if len(sites) < 2:
        print("[INFO] Pas assez de sites pour créer des liaisons.")
        return None

    rng = random.Random(seed)
    G = construire_graphe(sites, nombre_fibres, degre_max=degre_max, jitter=0.5, rng=rng)

    fibres = []
    for u, v in sorted(tuple(sorted(e)) for e in G.edges()):
        km = haversine_km(sites[u], sites[v])
        fibres.append({"u": u, "v": v, "distance_km": round(km, 2),
                       "cost": max(5, round(km * rng.uniform(*COUT_KM))),
                       "statut": rng.choices(STATUTS, weights=POIDS)[0]})

    with open(fibre_filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["u", "v", "distance_km", "cost", "statut"])
        w.writeheader()
        w.writerows(fibres)
    print(f"[SUCCÈS] '{fibre_filepath}' généré ({len(fibres)} tronçons, coût en k€).")
    return {"troncons": len(fibres)}