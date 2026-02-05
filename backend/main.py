from fastapi import FastAPI
from database import init_db
from routers import analytics, auth, docs, integration, projects, support, tasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from database import init_db
from routers import analytics, auth, docs, integration, projects, support, tasks

app = FastAPI(
    title="UA FLOW MVP",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api", include_in_schema=False)
def docs_redirect():
    """Help operators discover the interactive API explorer under the /api namespace."""

    return RedirectResponse(url="/api/docs")
