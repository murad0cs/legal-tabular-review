import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import engine, Base, get_db_context
from .routes import (
    documents_router, 
    templates_router, 
    projects_router, 
    exports_router,
    comments_router,
    audit_router,
    settings_router,
    validation_router,
    search_router,
    evaluation_router
)
from .services import TemplateService
from .config import get_settings
from .exceptions import AppException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    Base.metadata.create_all(bind=engine)
    
    with get_db_context() as db:
        TemplateService(db).create_default_templates()
    
    logger.info("Application started successfully")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for extracting and reviewing fields from legal documents",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(documents_router)
app.include_router(templates_router)
app.include_router(projects_router)
app.include_router(exports_router)
app.include_router(comments_router)
app.include_router(audit_router)
app.include_router(settings_router)
app.include_router(validation_router)
app.include_router(search_router)
app.include_router(evaluation_router)


@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
