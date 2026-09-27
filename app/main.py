from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import explain, jadwal, predict, query, resolve

app = FastAPI(title="Grafika ML Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(resolve.router)
app.include_router(explain.router)
app.include_router(query.router)
app.include_router(jadwal.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "grafika-ml"}
