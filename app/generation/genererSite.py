import csv
import random


def generer_csv_sites(filepath="sites.csv", nombre_sites=120):
    """
    Génère un fichier CSV contenant un jeu de données réaliste d'au moins 100 sites.
    Colonnes : id, nom, type, longitude, latitude
    """
    types_sites = [
        "Centrale électrique",
        "Station d'épuration",
        "Hôpital",
        "École",
        "Parc municipal",
        "Caserne de pompiers",
        "Station de métro",
        "Centre commercial",
        "Commissariat",
        "Bibliothèque"
    ]

    prefixes = ["Grand", "Nouveau", "Centre", "Quartier", "Résidence", "Zone Industrielle", "Complexe", "Station",
                "Parc", "Campus"]
    noms_propres = [
        "Alpha", "Beta", "Gamma", "Delta", "Nord", "Sud", "Est", "Ouest",
        "Central", "Bellevue", "Rivage", "Colline", "Vallée", "Lumière",
        "Horizon", "Metropolis", "Novapolis", "Soleil", "Foch", "République",
        "Victor Hugo", "Jaurès", "Pasteur", "Curie", "Moulin", "Porte de Paris"
    ]

    sites = []

    base_lat = 48.8566
    base_lon = 2.3522

    for i in range(1, nombre_sites + 1):
        site_id = i
        type_site = random.choice(types_sites)

        # Génération d'un nom réaliste et varié
        prefix = random.choice(prefixes)
        nom_propre = random.choice(noms_propres)
        nom = f"{prefix} {type_site.lower()} {nom_propre} {i}"

        latitude = round(base_lat + random.uniform(-0.15, 0.15), 6)
        longitude = round(base_lon + random.uniform(-0.20, 0.20), 6)

        sites.append({
            "id": site_id,
            "nom": nom,
            "type": type_site,
            "longitude": longitude,
            "latitude": latitude
        })

    champs = ["id", "nom", "type", "longitude", "latitude"]

    with open(filepath, mode="w", encoding="utf-8", newline="") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=champs)
        writer.writeheader()
        writer.writerows(sites)

    print(f"[SUCCÈS] Le fichier '{filepath}' a été généré avec succès avec {nombre_sites} sites !")


if __name__ == "__main__":
    generer_csv_sites()