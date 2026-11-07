from fastapi import APIRouter, Depends

from app.api.dependencies import validate_request_origin
from app.api.v1.routes import (
    auth,
    calendar,
    goals,
    habit,
    intelligence,
    meta,
    projects,
    routines,
    tasks,
)

api_router = APIRouter(dependencies=[Depends(validate_request_origin)])
api_router.include_router(meta.router)
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(goals.router)
api_router.include_router(projects.router)
api_router.include_router(habit.router)
api_router.include_router(calendar.router)
api_router.include_router(routines.router)
api_router.include_router(intelligence.router)
