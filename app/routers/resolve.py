from fastapi import APIRouter
from app.models.schemas import ResolveRequest, ResolveResponse
from app.services.resolver import resolve_conflicts

router = APIRouter()


@router.post("/resolve/conflicts", response_model=ResolveResponse)
def resolve(request: ResolveRequest):
    return resolve_conflicts(request)
