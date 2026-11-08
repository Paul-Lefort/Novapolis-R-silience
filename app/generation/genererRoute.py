import csv
import random

from app.generation.reseau import construire_graphe, haversine_km, lire_sites, orienter_routes


def generer_csv_routes(sites_filepath="sites.csv", routes_filepath="routes.csv", nombre_routes=None,
                       degre_max=3, part_sens_unique=0.15, nb_impasses=2, seed=0):
    """Réseau routier ORIENTÉ : liaisons courtes, sans croisement, temps basés sur la distance.

    - la plupart des liaisons sont à double sens, `part_sens_unique` à sens unique ;
    - le coeur du réseau est fortement connexe ; `nb_impasses` sites ne sont volontairement
      pas atteignables (cas limite pour le Module 1) ;
    - une route peut être 'travaux' (les deux sens) ou 'sature' (par sens) ; une route saturée
      reste praticable mais son temps de pointe est plus élevé.
    Retourne un dict de statistiques (None si échec).
    """
    try:
        sites = lire_sites(sites_filepath)
    except FileNotFoundError:
        print(f"[ERREUR] Le fichier '{sites_filepath}' est introuvable.")
        return None
    if len(sites) < 2:
        return None

    rng = random.Random(seed)
    G = construire_graphe(sites, nombre_routes, degre_max=degre_max, jitter=0.15, rng=rng)
    DG, impasses = orienter_routes(G, rng, part_sens_unique, nb_impasses)

    routes = []
    for u, v in sorted(tuple(sorted(e)) for e in G.edges()):
        km = haversine_km(sites[u], sites[v])
        vitesse = rng.uniform(30, 70)  # km/h
        type_voie, capacite = (("boulevard", 1500) if vitesse >= 55
                               else ("avenue", 1000) if vitesse >= 42 else ("rue", 600))
        temps_normal = max(0.5, round(km / vitesse * 60, 1))   # minutes
        travaux = rng.random() < 0.07
        for a, b in ((u, v), (v, u)):
            if not DG.has_edge(a, b):
                continue
            statut = "travaux" if travaux else ("sature" if rng.random() < 0.12 else "ouvert")
            facteur = rng.uniform(2.0, 3.0) if statut == "sature" else rng.uniform(1.2, 2.0)
            routes.append({
                "u": a, "v": b, "distance_km": round(km, 2),
                "temps_normal": temps_normal, "temps_pointe": round(temps_normal * facteur, 1),
                "statut": statut, "type_voie": type_voie, "capacite": capacite,
            })

    champs = ["u", "v", "distance_km", "temps_normal", "temps_pointe", "statut", "type_voie", "capacite"]
    with open(routes_filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(routes)
    nb_double = sum(1 for u, v in G.edges() if DG.has_edge(u, v) and DG.has_edge(v, u))
    print(f"[SUCCÈS] '{routes_filepath}' généré ({len(routes)} arcs pour {G.number_of_edges()} liaisons, "
          f"{nb_double} à double sens, impasses : {sorted(impasses)}).")
    return {"arcs": len(routes), "liaisons": G.number_of_edges(), "liaisons_double_sens": nb_double,
            "impasses": sorted(impasses)}