from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.services.extractor import extract_text
from app.services.parser import parse_parameters
from app.services.summarizer import build_structured_summary
from app.models.response_model import ReportResponse
from app.utils.helpers import has_supported_extension

router = APIRouter()


@router.post("/analyze-report", response_model=ReportResponse)
async def analyze_report(file: UploadFile = File(...)) -> ReportResponse:
    if not has_supported_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Accepted PDF and image files.",
        )

    try:
        raw_text = await extract_text(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process uploaded file: {exc}",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to extract text from the uploaded file.",
        )

    parameters = parse_parameters(raw_text)
    summary = await build_structured_summary(parameters, raw_text)
    return summary
