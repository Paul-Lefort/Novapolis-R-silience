import csv
import os
import random


def generer_csv_sites(filepath="sites.csv", nombre_sites=120):
  """Génère un fichier CSV de sites.

  Si le fichier existe déjà, il est écrasé (overwrite).
  """
  types_sites = [
      "Centrale électrique",
      "Station d'épuration",
      "Hôpital",
      "École",
      "Parc municipal",
      "Caserne de pompiers",
      "Gare routière",
      "Centre commercial",
      "Commissariat",
      "Bibliothèque",
  ]

  prefixes = [
      "Grand",
      "Nouveau",
      "Centre",
      "Quartier",
      "Résidence",
      "Zone Industrielle",
      "Complexe",
      "Parc",
      "Campus",
  ]
  noms_propres = [
      "Alpha",
      "Beta",
      "Gamma",
      "Delta",
      "Nord",
      "Sud",
      "Est",
      "Ouest",
      "Central",
      "Bellevue",
      "Rivage",
      "Colline",
      "Vallée",
      "Lumière",
      "Horizon",
      "Metropolis",
      "Novapolis",
      "Soleil",
      "Foch",
      "République",
      "Victor Hugo",
      "Jaurès",
      "Pasteur",
      "Curie",
      "Moulin",
      "Porte de Paris",
  ]

  sites = []
  base_lat = 48.8566
  base_lon = 2.3522

  for i in range(1, nombre_sites + 1):
    site_id = i
    type_site = random.choice(types_sites)
    prefix = random.choice(prefixes)
    nom_propre = random.choice(noms_propres)
    nom = f"{prefix} {type_site.lower()} {nom_propre} {i}"

    # Pas de sites superposés : on retire au hasard jusqu'à trouver une place libre (~400 m min.)
    for _ in range(200):
      latitude = round(base_lat + random.uniform(-0.15, 0.15), 6)
      longitude = round(base_lon + random.uniform(-0.20, 0.20), 6)
      if all((latitude - s["latitude"]) ** 2 + (longitude - s["longitude"]) ** 2 > 0.004 ** 2
             for s in sites):
        break

    sites.append({
        "id": site_id,
        "nom": nom,
        "type": type_site,
        "longitude": longitude,
        "latitude": latitude,
    })

  champs = ["id", "nom", "type", "longitude", "latitude"]

  # Le mode "w" écrase automatiquement l'ancien fichier s'il existe
  # utf-8-sig évite les problèmes de BOM avec PapaParse
  with open(filepath, mode="w", encoding="utf-8-sig", newline="") as fichier_csv:
    writer = csv.DictWriter(fichier_csv, fieldnames=champs)
    writer.writeheader()
    writer.writerows(sites)

  print(
      f"[SUCCÈS] Le fichier '{filepath}' a été écrasé et généré avec"
      f" {nombre_sites} sites !"
  )