import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse


from app.database import get_db

router = APIRouter(prefix="/api")


@router.get("/check-db")
def check_db(db: Session = Depends(get_db)):
    try:
        version = db.execute(text("SELECT VERSION()")).scalar()
        return {"status": "success", "mysql_version": version}
    except Exception as e:
        pass
    raise HTTPException(status_code=500, detail=str(e))