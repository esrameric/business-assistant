"""
Automation module for scheduled tasks.
Developed by: Developer C
Uses APScheduler for task scheduling and SMTP for email notifications.
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    load_dotenv(encoding="utf-8")
except Exception:
    try:
        load_dotenv(encoding="utf-16")
    except Exception:
        pass

# Global scheduler instance
scheduler = None

# In-memory cache: (stock_id, miktar) tuples already alerted
_critical_stock_cache: set = set()


# ==================== Private Helpers ====================

def _build_html_report(
    stok_items: List[Dict],
    siparis_items: List[Dict],
    gorev_items: List[Dict],
) -> str:
    """HTML raporu oluşturur; UTF-8 charset başlığı içerir."""

    kritik_stoklar = [m for m in stok_items if int(m.get("miktar", 0)) < 10]
    bekleyen_siparisler = [
        m for m in siparis_items
        if m.get("durum") in ("Yeni", "Hazırlanıyor", "Beklemede")
    ]
    acik_gorevler = [m for m in gorev_items if m.get("status") != "Tamamlandı"]

    def _stok_row(idx: int, meta: Dict, doc: str) -> str:
        renk = "#ffe0e0" if int(meta.get("miktar", 0)) < 5 else "#fff3cd"
        return (
            f"<tr style='background:{renk}'>"
            f"<td>{idx}</td>"
            f"<td>{doc}</td>"
            f"<td>{meta.get('kategori', '-')}</td>"
            f"<td><b>{meta.get('miktar', 0)}</b></td>"
            f"<td>{meta.get('fiyat', 0):,} ₺</td>"
            f"</tr>"
        )

    def _siparis_row(idx: int, meta: Dict, doc: str) -> str:
        durum_renk = {"Yeni": "#cce5ff", "Hazırlanıyor": "#fff3cd", "Beklemede": "#f8d7da"}
        renk = durum_renk.get(meta.get("durum", ""), "#ffffff")
        return (
            f"<tr style='background:{renk}'>"
            f"<td>{idx}</td>"
            f"<td>{meta.get('musteri', '-')}</td>"
            f"<td>{meta.get('tutar', 0):,} ₺</td>"
            f"<td>{meta.get('durum', '-')}</td>"
            f"</tr>"
        )

    def _gorev_row(idx: int, meta: Dict, doc: str) -> str:
        oncelik_renk = {"Yüksek": "#f8d7da", "Orta": "#fff3cd", "Düşük": "#d4edda"}
        renk = oncelik_renk.get(meta.get("oncelik", ""), "#ffffff")
        return (
            f"<tr style='background:{renk}'>"
            f"<td>{idx}</td>"
            f"<td>{doc[:60]}{'...' if len(doc) > 60 else ''}</td>"
            f"<td>{meta.get('kategori', '-')}</td>"
            f"<td>{meta.get('oncelik', '-')}</td>"
            f"<td>{meta.get('son_tarih', '-')}</td>"
            f"<td>{meta.get('status', '-')}</td>"
            f"</tr>"
        )

    stok_rows = "".join(
        _stok_row(i + 1, m["meta"], m["doc"])
        for i, m in enumerate(
            [{"meta": m, "doc": d} for m, d in zip(stok_items, [""] * len(stok_items))]
        )
    )
    siparis_rows = "".join(
        _siparis_row(i + 1, m["meta"], m["doc"])
        for i, m in enumerate(
            [{"meta": m, "doc": d} for m, d in zip(siparis_items, [""] * len(siparis_items))]
        )
    )
    gorev_rows = "".join(
        _gorev_row(i + 1, m["meta"], m["doc"])
        for i, m in enumerate(
            [{"meta": m, "doc": d} for m, d in zip(gorev_items, [""] * len(gorev_items))]
        )
    )

    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>İşletme Raporu</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #333; margin: 20px; }}
    h1 {{ color: #2c3e50; }}
    h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 4px; }}
    .ozet {{ display: flex; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }}
    .kart {{
      background: #3498db; color: white; border-radius: 8px;
      padding: 16px 24px; min-width: 160px; text-align: center;
    }}
    .kart.uyari {{ background: #e74c3c; }}
    .kart.bilgi  {{ background: #27ae60; }}
    .kart span {{ display: block; font-size: 2em; font-weight: bold; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 32px; }}
    th {{ background: #2c3e50; color: white; padding: 8px 12px; text-align: left; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #ddd; }}
    .footer {{ color: #999; font-size: 0.85em; margin-top: 32px; }}
  </style>
</head>
<body>
  <h1>📊 İşletme Günlük Raporu</h1>
  <p>Rapor tarihi: <b>{now_str}</b></p>

  <div class="ozet">
    <div class="kart">
      <span>{len(stok_items)}</span>
      Toplam Ürün
    </div>
    <div class="kart uyari">
      <span>{len(kritik_stoklar)}</span>
      Kritik Stok (&lt;10)
    </div>
    <div class="kart bilgi">
      <span>{len(bekleyen_siparisler)}</span>
      Bekleyen Sipariş
    </div>
    <div class="kart" style="background:#8e44ad">
      <span>{len(acik_gorevler)}</span>
      Açık Görev
    </div>
  </div>

  <h2>⚠️ Kritik Stok Durumu (miktar &lt; 10)</h2>
  {"<p><i>Kritik stok bulunmuyor.</i></p>" if not kritik_stoklar else f"""
  <table>
    <tr><th>#</th><th>Ürün</th><th>Kategori</th><th>Miktar</th><th>Fiyat</th></tr>
    {"".join(_stok_row(i+1, m, "") for i, m in enumerate(kritik_stoklar))}
  </table>"""}

  <h2>📦 Bekleyen Siparişler</h2>
  {"<p><i>Bekleyen sipariş bulunmuyor.</i></p>" if not bekleyen_siparisler else f"""
  <table>
    <tr><th>#</th><th>Müşteri</th><th>Tutar</th><th>Durum</th></tr>
    {"".join(_siparis_row(i+1, m, "") for i, m in enumerate(bekleyen_siparisler))}
  </table>"""}

  <h2>📋 Açık Görevler</h2>
  {"<p><i>Açık görev bulunmuyor.</i></p>" if not acik_gorevler else f"""
  <table>
    <tr><th>#</th><th>Görev</th><th>Kategori</th><th>Öncelik</th><th>Son Tarih</th><th>Durum</th></tr>
    {"".join(_gorev_row(i+1, m, "") for i, m in enumerate(acik_gorevler))}
  </table>"""}

  <p class="footer">Bu rapor otomatik olarak oluşturulmuştur. RAG Business Assistant v1.0</p>
</body>
</html>"""
    return html


def _send_email(subject: str, html_body: str, recipient: Optional[str] = None) -> bool:
    """SMTP_SSL üzerinden Gmail ile e-posta gönderir."""
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 465))

    if not email_sender or not email_password:
        logger.warning("E-posta gönderilemiyor: EMAIL_SENDER veya EMAIL_PASSWORD tanımlı değil.")
        return False

    to_address = recipient or os.getenv("EMAIL_RECIPIENT", email_sender)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_sender
        msg["To"] = to_address

        part = MIMEText(html_body, "html", "utf-8")
        msg.attach(part)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_sender, email_password)
            server.sendmail(email_sender, to_address, msg.as_string())

        logger.info(f"E-posta gönderildi → {to_address} | Konu: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP kimlik doğrulama hatası: EMAIL_SENDER ve EMAIL_PASSWORD'u kontrol et.")
        return False
    except Exception as e:
        logger.error(f"E-posta gönderilemedi: {str(e)}")
        return False


# ==================== Public Scheduled Functions ====================

def send_email_report() -> bool:
    """
    Günlük işletme raporunu HTML olarak hazırlayıp e-posta ile gönderir.
    ChromaDB'den stok/sipariş/görev verilerini çeker, HTML tablo raporu üretir.

    Returns:
        bool: Gönderim başarılıysa True
    """
    logger.info(f"[SCHEDULED TASK] E-posta raporu başlatıldı — {datetime.now()}")

    try:
        from shared_utils import get_collection
        collection = get_collection()

        stok_result = collection.get(where={"type": "stok"}, include=["metadatas", "documents"])
        siparis_result = collection.get(where={"type": "sipariş"}, include=["metadatas", "documents"])
        gorev_result = collection.get(where={"type": "görev"}, include=["metadatas", "documents"])

        stok_meta: List[Dict] = stok_result.get("metadatas", []) or []
        siparis_meta: List[Dict] = siparis_result.get("metadatas", []) or []
        gorev_meta: List[Dict] = gorev_result.get("metadatas", []) or []

        html = _build_html_report(stok_meta, siparis_meta, gorev_meta)

        subject = f"İşletme Günlük Raporu — {datetime.now().strftime('%d.%m.%Y')}"
        success = _send_email(subject, html)

        if success:
            logger.info("Günlük rapor başarıyla gönderildi.")
        else:
            logger.warning("Günlük rapor gönderilemedi (credentials eksik veya SMTP hatası).")

        return success

    except ValueError as e:
        logger.warning(f"Veritabanı henüz başlatılmamış, rapor atlandı: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"send_email_report hatası: {str(e)}")
        return False


def check_critical_stock() -> Dict[str, Any]:
    """
    Stoğu 5'in altına düşen ürünler için anında uyarı maili gönderir.
    Cache, (stock_id, miktar) çiftine göre çalışır — aynı düzeyde tekrar mail atılmaz.

    Returns:
        Dict: Kontrol özeti (kontrol edilen, uyarı gönderilen sayısı)
    """
    logger.info(f"[SCHEDULED TASK] Kritik stok kontrolü — {datetime.now()}")

    alerts_sent = 0
    checked = 0

    try:
        from shared_utils import get_collection
        collection = get_collection()

        result = collection.get(where={"type": "stok"}, include=["metadatas", "documents"])
        ids: List[str] = result.get("ids", []) or []
        metas: List[Dict] = result.get("metadatas", []) or []
        docs: List[str] = result.get("documents", []) or []

        critical_items = []

        for stock_id, meta, doc in zip(ids, metas, docs):
            checked += 1
            miktar = int(meta.get("miktar", 0))

            if miktar < 5:
                cache_key = (stock_id, miktar)
                if cache_key not in _critical_stock_cache:
                    critical_items.append((stock_id, meta, doc, miktar))
                    _critical_stock_cache.add(cache_key)

        if critical_items:
            rows = "".join(
                f"<tr><td>{sid}</td><td>{doc}</td><td style='color:red'><b>{mkt}</b></td>"
                f"<td>{m.get('kategori', '-')}</td></tr>"
                for sid, m, doc, mkt in critical_items
            )
            html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Kritik Stok Uyarısı</title></head>
<body>
<h1 style="color:#c0392b">🚨 Kritik Stok Uyarısı</h1>
<p>Aşağıdaki ürünlerin stoğu <b>5 adedin altına</b> düştü:</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%">
  <tr style="background:#c0392b;color:white">
    <th>Stok ID</th><th>Ürün</th><th>Miktar</th><th>Kategori</th>
  </tr>
  {rows}
</table>
<p style="color:#666;font-size:0.85em">RAG Business Assistant — Otomatik Uyarı</p>
</body>
</html>"""
            subject = f"🚨 KRİTİK STOK UYARISI — {len(critical_items)} ürün"
            sent = _send_email(subject, html)
            if sent:
                alerts_sent = len(critical_items)
                logger.warning(
                    f"Kritik stok uyarısı gönderildi: {[s for s, *_ in critical_items]}"
                )
        else:
            logger.info("Kritik stok kontrolü tamamlandı — yeni uyarı yok.")

    except ValueError as e:
        logger.warning(f"Veritabanı hazır değil, kritik stok atlandı: {str(e)}")
    except Exception as e:
        logger.error(f"check_critical_stock hatası: {str(e)}")

    return {"checked": checked, "alerts_sent": alerts_sent}


# ==================== Scheduler Management ====================

def init_scheduler() -> BackgroundScheduler:
    """
    APScheduler'ı başlatır ve görevleri zamanlar.

    Returns:
        BackgroundScheduler: Başlatılmış zamanlayıcı
    """
    global scheduler

    try:
        scheduler = BackgroundScheduler(daemon=True)

        scheduler.add_job(
            func=send_email_report,
            trigger=CronTrigger(hour=8, minute=0),
            id="email_report_job",
            name="Daily Email Report",
            replace_existing=True,
            misfire_grace_time=60,
        )

        scheduler.add_job(
            func=check_critical_stock,
            trigger=IntervalTrigger(minutes=5),
            id="critical_stock_check",
            name="Critical Stock Check",
            replace_existing=True,
            misfire_grace_time=30,
        )

        logger.info("Scheduler başlatıldı. Zamanlanmış görevler:")
        logger.info("  - Daily Email Report    : Her gün 08:00")
        logger.info("  - Critical Stock Check  : Her 5 dakikada bir")

        return scheduler

    except Exception as e:
        logger.error(f"Scheduler başlatılamadı: {str(e)}")
        raise


def start_scheduler() -> None:
    """Scheduler'ı çalıştırır."""
    if scheduler is None:
        raise RuntimeError("Scheduler başlatılmadı. Önce init_scheduler() çağırın.")

    try:
        scheduler.start()
        logger.info("Scheduler çalışıyor.")
    except Exception as e:
        logger.error(f"Scheduler başlatma hatası: {str(e)}")
        raise


def stop_scheduler() -> None:
    """Scheduler'ı nazikçe durdurur."""
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler durduruldu.")
        except Exception as e:
            logger.error(f"Scheduler durdurma hatası: {str(e)}")


def add_custom_job(func, trigger, job_id: str, job_name: str):
    """Scheduler'a özel bir görev ekler."""
    if scheduler is None:
        raise RuntimeError("Scheduler başlatılmadı.")

    try:
        job = scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=job_name,
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f"Görev eklendi: '{job_name}' (ID: {job_id})")
        return job
    except Exception as e:
        logger.error(f"Görev eklenemedi '{job_name}': {str(e)}")
        raise


def get_jobs_info() -> List[Dict[str, str]]:
    """Tüm zamanlanmış görevlerin bilgisini döner."""
    if scheduler is None:
        return []

    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else "Duraklatıldı",
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]


def setup_automation(app=None) -> BackgroundScheduler:
    """FastAPI uygulaması için otomasyon modülünü kurar ve başlatır."""
    try:
        init_scheduler()
        start_scheduler()
        logger.info("Otomasyon modülü aktif.")

        if app:
            @app.on_event("shutdown")
            async def shutdown_scheduler():
                stop_scheduler()

        return scheduler

    except Exception as e:
        logger.error(f"Otomasyon kurulumu başarısız: {str(e)}")
        raise


if __name__ == "__main__":
    import time

    logger.info("Otomasyon modülü bağımsız modda başlatılıyor...")
    try:
        setup_automation()
        for i in range(5):
            time.sleep(1)
            logger.info(f"Çalışıyor... {i+1}/5")
    except KeyboardInterrupt:
        logger.info("Kapatılıyor...")
        stop_scheduler()
    except Exception as e:
        logger.error(f"Kritik hata: {str(e)}")
        stop_scheduler()
