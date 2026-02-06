from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import ExportService

router = APIRouter(prefix="/api/projects", tags=["Exports"])


@router.get("/{project_id}/export/csv")
def export_csv(project_id: int, db: Session = Depends(get_db)):
    service = ExportService(db)
    filename, content = service.export_csv(project_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{project_id}/export/excel")
def export_excel(project_id: int, db: Session = Depends(get_db)):
    service = ExportService(db)
    filename, content = service.export_excel(project_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
