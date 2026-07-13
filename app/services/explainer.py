from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, LLM_MODEL
from app.models.schemas import ExplainRequest, ExplainResponse
import json


def explain_resolution(request: ExplainRequest) -> ExplainResponse:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=0.2,
    )

    from app.prompts import EXPLANATION_PROMPT
    prompt = ChatPromptTemplate.from_template(EXPLANATION_PROMPT)

    chain = prompt | llm

    try:
        context = request.context
        result = chain.invoke({
            "conflict_description": context.get("description", ""),
            "resolution": json.dumps(context, ensure_ascii=False),
        })
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(content)
        return ExplainResponse(
            explanation=data.get("explanation", ""),
            reasoning_steps=data.get("reasoning_steps", []),
        )
    except Exception as e:
        return ExplainResponse(
            explanation=f"Maaf, penjelasan AI sedang tidak tersedia. Error: {str(e)}",
            reasoning_steps=[],
        )
