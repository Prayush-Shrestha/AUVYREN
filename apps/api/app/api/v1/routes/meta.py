from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.meta import ApiMeta

router = APIRouter(tags=["System"])


@router.get("/meta", response_model=ApiMeta, summary="API metadata")
async def api_meta() -> ApiMeta:
    settings = get_settings()
    return ApiMeta(name=settings.app_name, version=settings.app_version)
