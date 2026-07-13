from fastapi import APIRouter
from app.models.schemas import ExplainRequest, ExplainResponse
from app.services.explainer import explain_resolution

router = APIRouter()


@router.post("/explain/resolution", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    return explain_resolution(request)
