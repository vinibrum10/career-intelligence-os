from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)
ASSETS = Path(__file__).parent / "web"


@router.get("/profiles")
def profiles_page():
    return FileResponse(ASSETS / "index.html", headers={"Cache-Control": "no-store"})


@router.get("/profiles/assets/styles.css")
def profiles_styles():
    return FileResponse(ASSETS / "styles.css", media_type="text/css", headers={"Cache-Control": "no-store"})


@router.get("/profiles/assets/profiles.js")
def profiles_script():
    return FileResponse(ASSETS / "profiles.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})
