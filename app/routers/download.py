import os
import sys
import io
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.responses import FileResponse

from app.generation.genererFibre import generer_csv_fibre
from app.generation.genererRoute import generer_csv_routes
from app.generation.genererSite import generer_csv_sites

sys.path.append("/app")

router = APIRouter(prefix="/api/download", tags=["Téléchargements"])


@router.get("/sites")
def download_sites():
    file_path = "sites.csv"
    if not os.path.exists(file_path):
        generer_csv_sites(filepath=file_path)
    return FileResponse(file_path, media_type="text/csv", filename="sites.csv")


@router.get("/routes")
def download_routes():
    file_path = "routes.csv"
    if not os.path.exists(file_path):
        if not os.path.exists("sites.csv"):
            generer_csv_sites(filepath="sites.csv")
        generer_csv_routes(sites_filepath="sites.csv", routes_filepath=file_path)
    return FileResponse(file_path, media_type="text/csv", filename="routes.csv")


@router.get("/fibre")
def download_fibre():
    file_path = "fibre.csv"
    if not os.path.exists(file_path):
        if not os.path.exists("sites.csv"):
            generer_csv_sites(filepath="sites.csv")
        generer_csv_fibre(sites_filepath="sites.csv", fibre_filepath=file_path)
    return FileResponse(file_path, media_type="text/csv", filename="fibre.csv")


# 🚀 Nouvelle route : Génère et télécharge les 3 fichiers dans un ZIP unique
@router.get("/all")
def download_all_as_zip():
    try:
        # 1. S'assurer que les 3 fichiers existent (les générer si besoin)
        if not os.path.exists("sites.csv"):
            generer_csv_sites("sites.csv")
        if not os.path.exists("routes.csv"):
            generer_csv_routes("sites.csv", "routes.csv")
        if not os.path.exists("fibre.csv"):
            generer_csv_fibre("sites.csv", "fibre.csv")

        # 2. Créer un fichier ZIP en mémoire
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write("sites.csv", arcname="sites.csv")
            zip_file.write("routes.csv", arcname="routes.csv")
            zip_file.write("fibre.csv", arcname="fibre.csv")

        zip_buffer.seek(0)

        # 3. Renvoyer le ZIP en téléchargement direct
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=reseau_novapolis.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du ZIP : {e}")