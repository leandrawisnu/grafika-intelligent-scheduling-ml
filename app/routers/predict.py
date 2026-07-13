from fastapi import APIRouter, HTTPException
from app.models.schemas import PredictRequest, PredictResponse, MLConflict
from app.services.predictor import predict_conflicts

router = APIRouter()


@router.post("/predict/conflicts", response_model=PredictResponse)
def predict(request: PredictRequest):
    if len(request.slots) == 0:
        return PredictResponse(conflicts=[])
    
    try:
        return predict_conflicts(request)
    except Exception as e:
        return PredictResponse(conflicts=[
            MLConflict(
                type="service_error",
                severity="warning",
                description=f"ML service error: {str(e)}",
                confidence=0.0,
            )
        ])
