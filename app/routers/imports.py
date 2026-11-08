import csv
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/api/import", tags=["Import & Données"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class NetworkChangeRequest(BaseModel):
    action: str
    target_file: str
    identifier: str
    new_value: str


@router.post("/network")
async def load_custom_network(
        sites_file: Optional[UploadFile] = File(None),
        routes_file: Optional[UploadFile] = File(None),
        fibre_file: Optional[UploadFile] = File(None)
):
    logger.info("[IMPORT] Réception de fichiers réseaux personnalisés.")
    try:
        saved_files = []
        for file_obj, filename in [(sites_file, "sites.csv"), (routes_file, "routes.csv"), (fibre_file, "fibre.csv")]:
            if file_obj:
                with open(BASE_DIR / filename, "wb") as f:
                    f.write(await file_obj.read())
                saved_files.append(filename)

        if not saved_files:
            raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

        logger.info(f"[IMPORT] Fichiers écrasés : {', '.join(saved_files)}")
        return {"status": "success", "message": f"Import réussi pour : {', '.join(saved_files)}"}
    except Exception as e:
        logger.error(f"[IMPORT] Échec de l'importation : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'import.")


@router.post("/changes")
def apply_network_change(change: NetworkChangeRequest):
    logger.info(f"[IMPORT] Modification requise : {change.action} sur {change.identifier} dans {change.target_file}")

    if change.target_file not in ["sites.csv", "routes.csv", "fibre.csv"]:
        raise HTTPException(status_code=403, detail="Cible interdite.")

    file_path = BASE_DIR / change.target_file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")

    try:
        updated, rows = False, []
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                row_id = str(row.get("id") or f"{row.get('u')}-{row.get('v')}")
                if row_id == str(change.identifier):
                    if change.action == "update_status":
                        row["statut"] = change.new_value
                        updated = True
                rows.append(row)

        if not updated:
            raise HTTPException(status_code=404, detail="Élément introuvable.")

        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return {"status": "success", "action": change.action, "new_value": change.new_value}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[IMPORT] Échec modification unitaire : {e}")
        raise HTTPException(status_code=500, detail="Erreur d'écriture.")