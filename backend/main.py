from fastapi import FastAPI
from database import init_db
from routers import auth, tasks, docs
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="UA FLOW MVP", version="0.1.0")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(docs.router, prefix="/api/v1/docs", tags=["Docs"])

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}
