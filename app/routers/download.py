import os
import sys
import io
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.generation.genererFibre import generer_csv_fibre
from app.generation.genererRoute import generer_csv_routes
from app.generation.genererSite import generer_csv_sites

router = APIRouter(prefix="/api", tags=["Réseau & Fichiers"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@router.post("/generate")
def generate_on_server(nombre_sites: int = Query(120, ge=10, le=2000)):
    """
    Génère dynamiquement les fichiers sites.csv, routes.csv et fibre.csv
    uniquement sur le disque du serveur (appelé par le front-end).
    """
    try:
        sites_path = BASE_DIR / "sites.csv"
        routes_path = BASE_DIR / "routes.csv"
        fibre_path = BASE_DIR / "fibre.csv"

        # 1. Génération des sites
        generer_csv_sites(filepath=str(sites_path), nombre_sites=nombre_sites)

        # 2. Calcul proportionnel sécurisé syntaxiquement correct
        max_possible = (3 * nombre_sites) // 2
        nb_routes = min(int(nombre_sites * 1.4), max_possible)
        nb_fibres = min(int(nombre_sites * 1.2), max_possible)

        # 3. Génération des routes et de la fibre
        generer_csv_routes(sites_filepath=str(sites_path), routes_filepath=str(routes_path), nombre_routes=nb_routes)
        generer_csv_fibre(sites_filepath=str(sites_path), fibre_filepath=str(fibre_path), nombre_fibres=nb_fibres)

        return {
            "status": "success",
            "message": f"Réseau de {nombre_sites} sites généré et enregistré sur le serveur avec succès.",
            "sites": "/api/download/sites.csv",
            "routes": "/api/download/routes.csv",
            "fibre": "/api/download/fibre.csv"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération sur le serveur : {e}")


@router.get("/download/all")
def download_all_existing_files():
    """
    Crée et télécharge une archive ZIP contenant les fichiers CSV déjà existants sur le serveur.
    """
    try:
        sites_path = BASE_DIR / "sites.csv"
        routes_path = BASE_DIR / "routes.csv"
        fibre_path = BASE_DIR / "fibre.csv"

        if not sites_path.exists() or not routes_path.exists() or not fibre_path.exists():
            raise HTTPException(status_code=404, detail="Certains fichiers du réseau manquent sur le serveur. Veuillez d'abord générer le réseau.")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(str(sites_path), arcname="sites.csv")
            zip_file.write(str(routes_path), arcname="routes.csv")
            zip_file.write(str(fibre_path), arcname="fibre.csv")

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=reseau_novapolis_complet.zip"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'archive ZIP : {e}")


@router.get("/download/{filename}")
def download_single_file(filename: str):
    """
    Permet de télécharger un fichier CSV unique existant sur le serveur
    (ex: /api/download/routes.csv, /api/download/sites.csv ou /api/download/fibre.csv).
    """
    allowed_files = ["sites.csv", "routes.csv", "fibre.csv"]
    if filename not in allowed_files:
        raise HTTPException(status_code=403, detail="Accès refusé à ce fichier.")

    file_path = BASE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Le fichier {filename} est introuvable sur le serveur.")

    return FileResponse(
        file_path,
        media_type="text/csv",
        filename=filename
    )