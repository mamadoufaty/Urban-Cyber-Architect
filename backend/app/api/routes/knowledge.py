from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

KB_ROOT = Path(settings.knowledge_base_path)


@router.get("/sectors")
async def list_sectors():
    sectors = []
    if KB_ROOT.exists():
        for path in KB_ROOT.iterdir():
            if path.is_dir() and (path / "index.yaml").exists():
                with open(path / "index.yaml", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                sectors.append({"id": path.name, "name": data.get("name", path.name), "domains": data.get("domains", [])})
    return sectors


@router.get("/sectors/{sector_id}")
async def get_sector(sector_id: str):
    path = KB_ROOT / sector_id / "index.yaml"
    if not path.exists():
        raise HTTPException(404, "Sector not found")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
