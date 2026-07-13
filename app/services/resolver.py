from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, LLM_MODEL
from app.models.schemas import ResolveRequest, ResolveResponse, Alternative
import json


def resolve_conflicts(request: ResolveRequest) -> ResolveResponse:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=0.3,
    )

    from app.prompts import RESOLUTION_PROMPT
    prompt = ChatPromptTemplate.from_template(RESOLUTION_PROMPT)

    chain = prompt | llm

    try:
        result = chain.invoke({
            "conflict_description": json.dumps(request.context.get("conflict", {}), ensure_ascii=False),
            "schedule_context": json.dumps(request.context.get("schedule_slots", []), indent=2, ensure_ascii=False, default=str),
        })
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(content)
        alternatives = [Alternative(**a) for a in data.get("alternatives", [])]
        return ResolveResponse(alternatives=alternatives)
    except Exception as e:
        return ResolveResponse(alternatives=[
            Alternative(
                rank=1,
                confidence=0.5,
                changes=[],
                explanation=f"AI resolution temporarily unavailable. Please resolve manually. Error: {str(e)}",
            )
        ])
