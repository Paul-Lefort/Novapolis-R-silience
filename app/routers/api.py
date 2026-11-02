import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

@router.get("/check-db")
def check_db(db: Session = Depends(get_db)):
    try:
        version = db.execute(text("SELECT VERSION()")).scalar()
        return {"status": "success", "mysql_version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites")
def get_root_sites():
    file_path = BASE_DIR / "sites.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier sites.csv introuvable. Générez le réseau d'abord.")
    return FileResponse(file_path, media_type="text/csv")

@router.get("/routes")
def get_root_routes():
    file_path = BASE_DIR / "routes.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier routes.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")

@router.get("/fibre")
def get_root_fibre():
    file_path = BASE_DIR / "fibre.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier fibre.csv introuvable.")
    return FileResponse(file_path, media_type="text/csv")