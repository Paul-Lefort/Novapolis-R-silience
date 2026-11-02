import os
import sys
import io
import zipfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.generation.genererFibre import generer_csv_fibre
from app.generation.genererRoute import generer_csv_routes
from app.generation.genererSite import generer_csv_sites

sys.path.append("/app")

router = APIRouter(prefix="/api/download", tags=["Réseau"])


@router.get("/all")
def generate_and_download(nombre_sites: int = Query(120, ge=10, le=2000)):
    """
    Génère dynamiquement les fichiers sites.csv, routes.csv et fibre.csv
    selon le nombre de sites spécifié, puis renvoie une archive ZIP complète.
    """
    try:
        sites_path = "sites.csv"
        routes_path = "routes.csv"
        fibre_path = "fibre.csv"

        # 1. Génération des sites avec le nombre personnalisé
        generer_csv_sites(filepath=sites_path, nombre_sites=nombre_sites)

        # 2. Calcul proportionnel sécurisé (maximum mathématique = (3 * n) // 2)
        max_possible = (3 * nombre_sites) // 2

        # On prend un nombre cohérent de routes/fibres (ex: 1.2 lien par site, plafonné au max possible)
        nb_routes = min(int(nombre_sites * 1.4), max_possible)
        nb_fibres = min(int(nombre_sites * 1.2), max_possible)

        # 3. Génération des routes et de la fibre
        generer_csv_routes(sites_filepath=sites_path, routes_filepath=routes_path, nombre_routes=nb_routes)
        generer_csv_fibre(sites_filepath=sites_path, fibre_filepath=fibre_path, nombre_fibres=nb_fibres)

        # 4. Création de l'archive ZIP en mémoire
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(sites_path, arcname="sites.csv")
            zip_file.write(routes_path, arcname="routes.csv")
            zip_file.write(fibre_path, arcname="fibre.csv")

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=reseau_novapolis_{nombre_sites}_sites.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du réseau : {e}")