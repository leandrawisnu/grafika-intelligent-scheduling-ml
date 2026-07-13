from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, LLM_MODEL
from app.models.schemas import QueryRequest, QueryResponse
import json


def nl_query(request: QueryRequest) -> QueryResponse:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=0.1,
    )

    from app.prompts import NL_QUERY_PROMPT
    prompt = ChatPromptTemplate.from_template(NL_QUERY_PROMPT)

    chain = prompt | llm

    try:
        result = chain.invoke({
            "query": request.query,
            "schedule_summary": f"Schedule ID: {request.schedule_id}",
        })
        content = result.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(content)
        return QueryResponse(
            answer=data.get("answer", "Maaf, saya tidak dapat menjawab pertanyaan ini."),
            result_data=data.get("result_data"),
        )
    except Exception as e:
        return QueryResponse(
            answer=f"Maaf, fitur query AI sedang tidak tersedia. Error: {str(e)}",
        )
