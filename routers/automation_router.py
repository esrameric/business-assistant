"""
Otomasyon API router — zamanlanmış görev yönetimi ve e-posta tetikleme endpoint'leri.
Geliştirici C tarafından geliştirilmiştir.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/jobs")
async def get_scheduled_jobs() -> List[Dict]:
    """Zamanlanmış tüm job'ların listesini döner."""
    try:
        from automation import get_jobs_info
        return get_jobs_info()
    except Exception as e:
        logger.error(f"get_scheduled_jobs hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/trigger")
async def trigger_job_manually(job_id: str) -> Dict:
    """
    Belirtilen job'u anında tetikler.
    Geçerli job_id: email_report_job, critical_stock_check
    """
    valid_jobs = {
        "email_report_job": None,
        "critical_stock_check": None,
    }

    if job_id not in valid_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job bulunamadı: '{job_id}'. Geçerli job'lar: {list(valid_jobs.keys())}",
        )

    try:
        from automation import send_email_report, check_critical_stock

        if job_id == "email_report_job":
            result = send_email_report()
            return {
                "success": result,
                "job_id": job_id,
                "message": "Günlük rapor maili gönderildi" if result else "Mail gönderilemedi (kimlik bilgileri eksik olabilir)",
            }
        else:
            check_critical_stock()
            return {
                "success": True,
                "job_id": job_id,
                "message": "Kritik stok kontrolü çalıştırıldı",
            }

    except Exception as e:
        logger.error(f"trigger_job_manually hatası (job_id={job_id}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-email")
async def test_email() -> Dict:
    """send_email_report() fonksiyonunu manuel olarak tetikler (demo/test amaçlı)."""
    try:
        from automation import send_email_report

        result = send_email_report()
        return {
            "success": result,
            "message": "Rapor maili gönderildi" if result else "Mail gönderilemedi (kimlik bilgileri eksik olabilir)",
        }
    except Exception as e:
        logger.error(f"test_email hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def automation_health() -> Dict:
    """Otomasyon modülü sağlık durumunu döner."""
    try:
        from automation import scheduler

        running = scheduler is not None and scheduler.running
        return {
            "status": "ok",
            "scheduler_running": running,
        }
    except Exception as e:
        logger.error(f"automation_health hatası: {e}")
        return {
            "status": "error",
            "scheduler_running": False,
            "detail": str(e),
        }
