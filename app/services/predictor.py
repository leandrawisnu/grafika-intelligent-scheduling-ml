from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import json
from app.config import OPENAI_API_KEY, LLM_MODEL
from app.models.schemas import PredictRequest, PredictResponse, MLConflict


def predict_conflicts(request: PredictRequest) -> PredictResponse:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=0.1,
    )

    schedule_json = json.dumps([s.model_dump() for s in request.slots], indent=2, ensure_ascii=False)
    teacher_json = json.dumps([t.model_dump() for t in request.teachers], indent=2, ensure_ascii=False)

    from app.prompts import CONFLICT_PREDICTION_PROMPT
    prompt = ChatPromptTemplate.from_template(CONFLICT_PREDICTION_PROMPT)

    chain = prompt | llm

    try:
        result = chain.invoke({"schedule_data": schedule_json, "teacher_data": teacher_json})
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        conflicts_data = json.loads(content)
        conflicts = [MLConflict(**c) for c in conflicts_data]
        return PredictResponse(conflicts=conflicts)
    except Exception as e:
        return PredictResponse(conflicts=[
            MLConflict(
                type="service_error",
                severity="warning",
                description=f"ML prediction temporarily unavailable: {str(e)}",
                confidence=0.0,
            )
        ])
