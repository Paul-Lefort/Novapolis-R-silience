import io
import zipfile
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.generation.genererFibre import generer_csv_fibre
from app.generation.genererRoute import generer_csv_routes
from app.generation.genererSite import generer_csv_sites

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api", tags=["Réseau & Fichiers"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@router.post("/generate")
def generate_on_server(nombre_sites: int = Query(120, ge=10, le=2000)):
    logger.info(f"[DOWNLOAD] Demande de génération de réseau pour {nombre_sites} sites.")
    try:
        sites_path = BASE_DIR / "sites.csv"
        routes_path = BASE_DIR / "routes.csv"
        fibre_path = BASE_DIR / "fibre.csv"

        generer_csv_sites(filepath=str(sites_path), nombre_sites=nombre_sites)

        max_possible = (3 * nombre_sites) // 2
        nb_routes = min(int(nombre_sites * 1.4), max_possible)
        nb_fibres = min(int(nombre_sites * 1.2), max_possible)

        generer_csv_routes(sites_filepath=str(sites_path), routes_filepath=str(routes_path), nombre_routes=nb_routes)
        generer_csv_fibre(sites_filepath=str(sites_path), fibre_filepath=str(fibre_path), nombre_fibres=nb_fibres)

        logger.info("[DOWNLOAD] Génération réussie.")
        return {
            "status": "success",
            "message": f"Réseau de {nombre_sites} sites généré avec succès.",
            "sites": "/api/download/sites.csv",
            "routes": "/api/download/routes.csv",
            "fibre": "/api/download/fibre.csv"
        }
    except Exception as e:
        logger.error(f"[DOWNLOAD] Échec de la génération : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération sur le serveur.")

@router.get("/download/all")
def download_all_existing_files():
    logger.info("[DOWNLOAD] Création de l'archive ZIP contenant tout le réseau.")
    try:
        sites_path, routes_path, fibre_path = BASE_DIR / "sites.csv", BASE_DIR / "routes.csv", BASE_DIR / "fibre.csv"

        if not all(p.exists() for p in [sites_path, routes_path, fibre_path]):
            raise HTTPException(status_code=404, detail="Fichiers manquants. Générez le réseau.")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(str(sites_path), arcname="sites.csv")
            zip_file.write(str(routes_path), arcname="routes.csv")
            zip_file.write(str(fibre_path), arcname="fibre.csv")
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer, media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=reseau_novapolis_complet.zip"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[DOWNLOAD] Erreur création ZIP : {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors du zippage.")

@router.get("/download/{filename}")
def download_single_file(filename: str):
    logger.info(f"[DOWNLOAD] Demande de téléchargement du fichier : {filename}")
    if filename not in ["sites.csv", "routes.csv", "fibre.csv"]:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    file_path = BASE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")

    return FileResponse(file_path, media_type="text/csv", filename=filename)