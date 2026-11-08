import csv
import math
import random
from collections import defaultdict

BASE_LAT, BASE_LON = 48.8566, 2.3522   # ville fictive « Novapolis » centrée sur ces coordonnées
D_MIN = 0.004                          # distance minimale entre sites (degrés, ~400 m)

# Types normalisés (utilisés par les algorithmes) -> libellé affiché dans le nom
LIBELLES = {
    "quartier": "Quartier", "ecole": "École", "parc": "Parc",
    "centre_commercial": "Centre commercial", "commissariat": "Commissariat",
    "station_epuration": "Station d'épuration", "centrale_electrique": "Centrale électrique",
    "hopital": "Hôpital", "caserne": "Caserne", "telecom": "Centre de télécommunication",
}
# types « libres » tirés au hasard (poids relatifs)
POIDS_LIBRES = {"quartier": 46, "ecole": 16, "parc": 6, "centre_commercial": 5,
                "commissariat": 4, "station_epuration": 2, "centrale_electrique": 3}
# types « critiques » : (coefficient, minimum garanti). Effectif = max(minimum, coef * sqrt(n)) :
# une grande ville a proportionnellement moins de casernes/hôpitaux par site (sinon tout est « à côté »).
QUOTAS = {"hopital": (0.4, 2), "caserne": (0.5, 2), "telecom": (0.35, 2)}

NOMS_PROPRES = ["Alpha", "Beta", "Gamma", "Delta", "Nord", "Sud", "Est", "Ouest", "Central",
                "Bellevue", "Rivage", "Colline", "Vallée", "Lumière", "Horizon", "Metropolis",
                "Novapolis", "Soleil", "Foch", "République", "Victor Hugo", "Jaurès", "Pasteur",
                "Curie", "Moulin", "Porte de Paris"]


def _repartition(n, rng):
    types = []
    for t, (part, mini) in QUOTAS.items():
        types += [t] * max(mini, round(part * math.sqrt(n)))
    if len(types) > n:
        raise ValueError(f"{n} sites : trop peu pour garantir hôpitaux, casernes et centres télécom")
    libres = list(POIDS_LIBRES)
    types += rng.choices(libres, weights=[POIDS_LIBRES[t] for t in libres], k=n - len(types))
    rng.shuffle(types)
    return types


def _positions(n, rng):
    """n points sans chevauchement (grille d'index : O(1) par test). Zone agrandie si n > 3000."""
    echelle = max(1.0, math.sqrt(n / 3000))
    dlat, dlon = 0.15 * echelle, 0.20 * echelle
    grille, pts = defaultdict(list), []
    for _ in range(n):
        for _ in range(500):
            lat = round(BASE_LAT + rng.uniform(-dlat, dlat), 6)
            lon = round(BASE_LON + rng.uniform(-dlon, dlon), 6)
            ci, cj = int(lat // D_MIN), int(lon // D_MIN)
            if all((lat - a) ** 2 + (lon - b) ** 2 > D_MIN ** 2
                   for di in (-1, 0, 1) for dj in (-1, 0, 1)
                   for a, b in grille.get((ci + di, cj + dj), ())):
                break
        else:
            raise RuntimeError("Impossible de placer tous les sites sans chevauchement.")
        grille[(ci, cj)].append((lat, lon))
        pts.append((lat, lon))
    return pts


def generer_csv_sites(filepath="sites.csv", nombre_sites=120, seed=0):
    """Génère sites.csv (DONNÉES SYNTHÉTIQUES). Même graine => même fichier."""
    rng = random.Random(seed)
    types = _repartition(nombre_sites, rng)
    pts = _positions(nombre_sites, rng)
    sites = []
    for i, (t, (lat, lon)) in enumerate(zip(types, pts), start=1):
        sites.append({"id": i, "nom": f"{LIBELLES[t]} {rng.choice(NOMS_PROPRES)} {i}",
                      "type": t, "longitude": lon, "latitude": lat})
    with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "nom", "type", "longitude", "latitude"])
        w.writeheader()
        w.writerows(sites)
    print(f"[SUCCÈS] '{filepath}' généré ({nombre_sites} sites, graine {seed}).")