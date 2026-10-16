import csv
import random


def generer_csv_routes(sites_filepath="sites.csv", routes_filepath="routes.csv", nombre_routes=1200):
    """
    Génère un fichier routes.csv d'au moins 1000 lignes connectant les sites du CSV.
    Colonnes : u,v,temps_normal,temps_pointe,statut
    """
    ids_sites = []
    try:
        with open(sites_filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ids_sites.append(int(row["id"]))
    except FileNotFoundError:
        print(f"[ERREUR] Le fichier '{sites_filepath}' est introuvable. Générez-le d'abord !")
        return

    if len(ids_sites) < 2:
        print("[ERREUR] Il faut au moins 2 sites dans le fichier sites.csv pour créer des routes.")
        return

    routes = []
    paires_existantes = set()

    statuts_possibles = ["ouvert", "ouvert", "ouvert", "saturé", "travaux"]

    while len(routes) < nombre_routes:
        u = random.choice(ids_sites)
        v = random.choice(ids_sites)

        if u == v or (u, v) in paires_existantes or (v, u) in paires_existantes:
            continue

        paires_existantes.add((u, v))

        temps_normal = random.randint(2, 35)
        temps_pointe = int(temps_normal * random.uniform(1.2, 2.5))

        statut = random.choice(statuts_possibles)

        routes.append({
            "u": u,
            "v": v,
            "temps_normal": temps_normal,
            "temps_pointe": temps_pointe,
            "statut": statut
        })

    champs = ["u", "v", "temps_normal", "temps_pointe", "statut"]

    with open(routes_filepath, mode="w", encoding="utf-8", newline="") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=champs)
        writer.writeheader()
        writer.writerows(routes)

    print(f"[SUCCÈS] Le fichier '{routes_filepath}' a été généré avec succès avec {len(routes)} routes !")
