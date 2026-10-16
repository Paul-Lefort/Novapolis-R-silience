import csv
import random


def generer_csv_fibre(sites_filepath="sites.csv", fibre_filepath="fibre.csv", nombre_fibres=800):
    """
    Génère un fichier fibre.csv connectant les sites du CSV.
    Colonnes : u,v,cost,statut
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
        print("[ERREUR] Il faut au moins 2 sites dans le fichier sites.csv pour créer des liaisons.")
        return

    fibres = []
    paires_existantes = set()

    statuts_possibles = ["actif", "actif", "actif", "en_maintenance", "deploiement"]

    while len(fibres) < nombre_fibres:
        u = random.choice(ids_sites)
        v = random.choice(ids_sites)

        if u == v or (u, v) in paires_existantes or (v, u) in paires_existantes:
            continue

        paires_existantes.add((u, v))

        cost = random.randint(500, 30000)

        statut = random.choice(statuts_possibles)

        fibres.append({
            "u": u,
            "v": v,
            "cost": cost,
            "statut": statut
        })

    champs = ["u", "v", "cost", "statut"]

    with open(fibre_filepath, mode="w", encoding="utf-8", newline="") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=champs)
        writer.writeheader()
        writer.writerows(fibres)

    print(f"[SUCCÈS] Le fichier '{fibre_filepath}' a été généré avec succès avec {len(fibres)} liaisons fibre !")