"""
Automation router — zamanlanmış görev yönetimi ve e-posta tetikleyici endpoint'leri.
Developed by: Developer C
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Modelleri ====================

class JobInfo(BaseModel):
    id: str
    name: str
    next_run_time: Optional[str] = None
    trigger: str


class JobResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    scheduler_running: bool
    job_count: int
    message: str


# ==================== Endpoint'ler ====================

@router.get("/jobs", response_model=List[JobInfo], summary="Tüm zamanlanmış görevleri listele")
async def get_scheduled_jobs():
    """
    APScheduler'daki tüm kayıtlı görevleri döner.
    """
    try:
        from automation import get_jobs_info
        jobs = get_jobs_info()
        return [JobInfo(**j) for j in jobs]
    except Exception as e:
        logger.error(f"Görev listesi alınamadı: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Görev listesi alınamadı: {str(e)}")


@router.post(
    "/jobs/{job_id}/trigger",
    response_model=JobResponse,
    summary="Bir görevi manuel olarak tetikle",
)
async def trigger_job_manually(job_id: str):
    """
    `email_report_job` veya `critical_stock_check` görevini anında çalıştırır.
    Demo/jüri sunumunda manuel tetikleme için kullanılır.
    """
    ALLOWED_JOBS = {
        "email_report_job": "send_email_report",
        "critical_stock_check": "check_critical_stock",
    }

    if job_id not in ALLOWED_JOBS:
        raise HTTPException(
            status_code=404,
            detail=f"Bilinmeyen job_id '{job_id}'. Geçerli değerler: {list(ALLOWED_JOBS.keys())}",
        )

    try:
        import automation
        func = getattr(automation, ALLOWED_JOBS[job_id])
        result = func()
        logger.info(f"Manuel tetikleme: {job_id} → {result}")
        return JobResponse(
            success=True,
            message=f"'{job_id}' başarıyla çalıştırıldı. Sonuç: {result}",
            job_id=job_id,
        )
    except Exception as e:
        logger.error(f"Manuel tetikleme hatası ({job_id}): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/test-email",
    response_model=JobResponse,
    summary="Demo için anında rapor maili gönder",
)
async def send_test_email():
    """
    Demo sırasında jüriye anlık e-posta raporu göndermek için kullanılır.
    `send_email_report()` fonksiyonunu doğrudan çağırır.
    """
    try:
        from automation import send_email_report
        success = send_email_report()
        if success:
            return JobResponse(success=True, message="Test e-postası başarıyla gönderildi.")
        else:
            return JobResponse(
                success=False,
                message="E-posta gönderilemedi. EMAIL_SENDER/EMAIL_PASSWORD .env dosyasında tanımlı mı?",
            )
    except Exception as e:
        logger.error(f"Test e-posta hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse, summary="Otomasyon modülü sağlık kontrolü")
async def automation_health():
    """
    Scheduler'ın çalışıp çalışmadığını ve kayıtlı görev sayısını döner.
    """
    try:
        from automation import scheduler, get_jobs_info

        running = scheduler is not None and scheduler.running
        jobs = get_jobs_info()

        return HealthResponse(
            status="healthy" if running else "degraded",
            scheduler_running=running,
            job_count=len(jobs),
            message="Scheduler aktif." if running else "Scheduler çalışmıyor — setup_automation() çağrıldı mı?",
        )
    except Exception as e:
        logger.error(f"Health check hatası: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            scheduler_running=False,
            job_count=0,
            message=str(e),
        )
