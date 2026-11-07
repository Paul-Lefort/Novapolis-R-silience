import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/import", tags=["Import & Données"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class NetworkChangeRequest(BaseModel):
    action: str  # ex: "update_status", "add_edge", "delete_node"
    target_file: str  # ex: "routes.csv", "fibre.csv", "sites.csv"
    identifier: str  # ex: identifiant du site ou de l'arête
    new_value: str  # ex: "travaux", "actif", etc.


@router.post("/network")
async def load_custom_network(
        sites_file: Optional[UploadFile] = File(None),
        routes_file: Optional[UploadFile] = File(None),
        fibre_file: Optional[UploadFile] = File(None)
):
    """
    1. Route pour charger/remplacer son propre graphe :
       - Nom des sites (sites.csv)
       - Réseau routier (routes.csv)
       - Réseau fibre / network (fibre.csv)
    """
    try:
        saved_files = []

        if sites_file:
            content = await sites_file.read()
            sites_path = BASE_DIR / "sites.csv"
            with open(sites_path, "wb") as f:
                f.write(content)
            saved_files.append("sites.csv")

        if routes_file:
            content = await routes_file.read()
            routes_path = BASE_DIR / "routes.csv"
            with open(routes_path, "wb") as f:
                f.write(content)
            saved_files.append("routes.csv")

        if fibre_file:
            content = await fibre_file.read()
            fibre_path = BASE_DIR / "fibre.csv"
            with open(fibre_path, "wb") as f:
                f.write(content)
            saved_files.append("fibre.csv")

        if not saved_files:
            raise HTTPException(status_code=400, detail="Aucun fichier valide fourni pour l'import.")

        return {
            "status": "success",
            "message": f"Fichiers importés et appliqués avec succès sur le serveur : {', '.join(saved_files)}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import du réseau : {str(e)}")


@router.post("/changes")
def apply_network_change(change: NetworkChangeRequest):
    """
    2. Route dissocier : gère et applique les changements/modifications spécifiques
       apportés au réseau (ex: mise à jour du statut d'une route, passage en travaux, etc.).
    """
    allowed_files = ["sites.csv", "routes.csv", "fibre.csv"]
    if change.target_file not in allowed_files:
        raise HTTPException(status_code=403, detail=f"Fichier cible non autorisé : {change.target_file}")

    file_path = BASE_DIR / change.target_file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Le fichier {change.target_file} est introuvable sur le serveur.")

    try:
        updated = False
        rows = []

        # Lecture et modification ciblée du CSV
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                # Identification de la ligne à modifier (selon les clés courantes id, u/v, etc.)
                row_id = str(row.get("id") or f"{row.get('u')}-{row.get('v')}")
                if row_id == str(change.identifier):
                    if change.action == "update_status":
                        row["statut"] = change.new_value
                        updated = True
                rows.append(row)

        if not updated:
            raise HTTPException(status_code=404,
                                detail=f"Élément identifié par '{change.identifier}' introuvable dans {change.target_file}.")

        # Réécriture du fichier CSV mis à jour
        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return {
            "status": "success",
            "message": f"Changement appliqué avec succès sur {change.target_file} pour l'élément {change.identifier}.",
            "action": change.action,
            "new_value": change.new_value
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'application du changement : {str(e)}")