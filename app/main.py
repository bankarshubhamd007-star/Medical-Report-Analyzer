import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response

from app.routes.upload import router as upload_router

app = FastAPI(title="Medical Report Summarizer", version="1.0.0")
app.include_router(upload_router)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("report_service")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Medical report summarization service is starting")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/api/docs", include_in_schema=False)
async def api_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)
