from fastapi import APIRouter, Depends

from app.api.dependencies import validate_request_origin
from app.api.v1.routes import auth, meta

api_router = APIRouter(dependencies=[Depends(validate_request_origin)])
api_router.include_router(meta.router)
api_router.include_router(auth.router)
