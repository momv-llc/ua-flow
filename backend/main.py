from fastapi import FastAPI
from database import init_db
from routers import analytics, auth, docs, integration, projects, support, tasks, timebilling
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

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(docs.router, prefix="/api/v1/docs", tags=["Docs"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Support"])
app.include_router(integration.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(timebilling.router, prefix="/api/v1/timebilling", tags=["Time & Billing"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}
