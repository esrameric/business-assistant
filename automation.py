"""
Otomasyon modülü — zamanlanmış e-posta raporu ve kritik stok uyarıları.
Geliştirici C tarafından geliştirilmiştir.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import config

logger = logging.getLogger(__name__)

# Global scheduler nesnesi
scheduler: Optional[BackgroundScheduler] = None


# ── Özel yardımcı fonksiyonlar ────────────────────────────────────────────────

def _build_html_report(
    stocks: List[Dict],
    orders: List[Dict],
    tasks: List[Dict],
) -> str:
    """Kritik stok, bekleyen sipariş ve açık görevleri içeren HTML rapor üretir."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    stock_rows = ""
    for s in stocks:
        stock_rows += (
            f"<tr>"
            f"<td>{s.get('id', '')}</td>"
            f"<td>{s.get('kategori', '')}</td>"
            f"<td style='color:red;font-weight:bold'>{s.get('miktar', 0)}</td>"
            f"<td>{s.get('fiyat', 0):,} &#8378;</td>"
            f"</tr>"
        )

    order_rows = ""
    for o in orders:
        order_rows += (
            f"<tr>"
            f"<td>{o.get('id', '')}</td>"
            f"<td>{o.get('musteri', '')}</td>"
            f"<td>{o.get('durum', '')}</td>"
            f"<td>{o.get('tutar', 0):,} &#8378;</td>"
            f"</tr>"
        )

    task_rows = ""
    for t in tasks:
        task_rows += (
            f"<tr>"
            f"<td>{t.get('id', '')}</td>"
            f"<td>{t.get('kategori', '')}</td>"
            f"<td>{t.get('oncelik', '')}</td>"
            f"<td>{t.get('status', '')}</td>"
            f"<td>{t.get('son_tarih', '')}</td>"
            f"</tr>"
        )

    stock_section = (
        "<p><em>Kritik stok bulunmuyor.</em></p>"
        if not stocks
        else (
            "<table>"
            "<thead><tr><th>ID</th><th>Kategori</th><th>Miktar</th><th>Fiyat</th></tr></thead>"
            f"<tbody>{stock_rows}</tbody>"
            "</table>"
        )
    )

    order_section = (
        "<p><em>Bekleyen sipari&#351; bulunmuyor.</em></p>"
        if not orders
        else (
            "<table>"
            "<thead><tr><th>ID</th><th>M&#252;&#351;teri</th><th>Durum</th><th>Tutar</th></tr></thead>"
            f"<tbody>{order_rows}</tbody>"
            "</table>"
        )
    )

    task_section = (
        "<p><em>A&#231;&#305;k g&#246;rev bulunmuyor.</em></p>"
        if not tasks
        else (
            "<table>"
            "<thead><tr><th>ID</th><th>Kategori</th><th>&#214;ncelik</th><th>Durum</th><th>Son Tarih</th></tr></thead>"
            f"<tbody>{task_rows}</tbody>"
            "</table>"
        )
    )

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>KOB&#304; G&#252;nl&#252;k Rapor</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f4f6f8; color: #333; margin: 0; padding: 0; }}
  .container {{ max-width: 900px; margin: 20px auto; background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.12); }}
  h1 {{ color: #1a73e8; margin-top: 0; }}
  h2 {{ color: #444; border-bottom: 2px solid #1a73e8; padding-bottom: 6px; }}
  .summary {{ display: flex; gap: 16px; margin: 20px 0; }}
  .card {{ flex: 1; background: #e8f0fe; border-radius: 8px; padding: 16px; text-align: center; }}
  .card .num {{ font-size: 2.2em; font-weight: bold; color: #1a73e8; }}
  .card .label {{ color: #555; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0 24px; }}
  th {{ background: #1a73e8; color: #fff; padding: 10px 12px; text-align: left; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #eee; }}
  tr:hover td {{ background: #f0f4ff; }}
  .footer {{ margin-top: 28px; color: #aaa; font-size: .85em; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>&#128202; KOB&#304; G&#252;nl&#252;k &#304;&#351;letme Raporu</h1>
  <p>Rapor tarihi: <strong>{now}</strong></p>

  <div class="summary">
    <div class="card">
      <div class="num">{len(stocks)}</div>
      <div class="label">Kritik Stok</div>
    </div>
    <div class="card">
      <div class="num">{len(orders)}</div>
      <div class="label">Bekleyen Sipari&#351;</div>
    </div>
    <div class="card">
      <div class="num">{len(tasks)}</div>
      <div class="label">A&#231;&#305;k G&#246;rev</div>
    </div>
  </div>

  <h2>&#128721; Kritik Stok (miktar &lt; 10)</h2>
  {stock_section}

  <h2>&#128666; Bekleyen Sipari&#351;ler</h2>
  {order_section}

  <h2>&#128203; A&#231;&#305;k G&#246;revler</h2>
  {task_section}

  <div class="footer">
    Bu rapor otomatik olu&#351;turulmu&#351;tur &mdash; KOB&#304; AI Y&#246;netim Sistemi v1.0
  </div>
</div>
</body>
</html>"""
    return html


def _send_email(subject: str, html_body: str) -> bool:
    """SMTP_SSL ile Gmail üzerinden HTML mail gönderir. Başarıda True döner."""
    sender = config.EMAIL_SENDER
    password = config.EMAIL_PASSWORD

    if not sender:
        logger.warning("EMAIL_SENDER yapılandırılmamış — mail gönderilemedi")
        return False
    if not password:
        logger.warning("EMAIL_PASSWORD yapılandırılmamış — mail gönderilemedi")
        return False

    recipient = getattr(config, "EMAIL_RECIPIENT", None) or sender

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL(config.EMAIL_SMTP_SERVER, config.EMAIL_SMTP_PORT) as server:
            server.login(sender, password)
            server.send_message(msg)

        logger.info(f"Mail başarıyla gönderildi → {recipient} | Konu: {subject}")
        return True
    except Exception as e:
        logger.error(f"Mail gönderimi başarısız: {e}")
        return False


# ── Ana otomasyon fonksiyonları ────────────────────────────────────────────────

def send_email_report() -> bool:
    """Tüm işletme verisini çekip günlük HTML rapor maili gönderir."""
    logger.info(f"[ZAMANLI GÖREV] Günlük rapor başlatıldı — {datetime.now()}")
    try:
        from shared_utils import get_collection, init_db
        try:
            col = get_collection()
        except ValueError:
            init_db()
            col = get_collection()

        # Stok verisi
        stock_res = col.get(where={"type": "stok"}, include=["metadatas"])
        all_stocks = [
            {"id": sid, **meta}
            for sid, meta in zip(stock_res["ids"], stock_res["metadatas"])
        ]
        critical_stocks = [s for s in all_stocks if s.get("miktar", 0) < 10]

        # Sipariş verisi
        order_res = col.get(where={"type": "sipariş"}, include=["metadatas"])
        all_orders = [
            {"id": oid, **meta}
            for oid, meta in zip(order_res["ids"], order_res["metadatas"])
        ]
        pending_statuses = {"Hazırlanıyor", "Yeni", "Beklemede"}
        pending_orders = [o for o in all_orders if o.get("durum") in pending_statuses]

        # Görev verisi
        task_res = col.get(where={"type": "görev"}, include=["metadatas"])
        all_tasks = [
            {"id": tid, **meta}
            for tid, meta in zip(task_res["ids"], task_res["metadatas"])
        ]
        open_tasks = [t for t in all_tasks if t.get("status") != "Tamamlandı"]

        html = _build_html_report(critical_stocks, pending_orders, open_tasks)
        subject = f"KOBİ Günlük Rapor — {datetime.now().strftime('%d.%m.%Y')}"
        return _send_email(subject, html)

    except Exception as e:
        logger.error(f"send_email_report hatası: {e}")
        return False


def check_critical_stock() -> None:
    """Stoğu 5'in altına düşen ürünler için anlık uyarı maili gönderir (in-memory cache ile)."""
    if not hasattr(check_critical_stock, "_alerted"):
        check_critical_stock._alerted: set = set()

    try:
        from shared_utils import get_collection, init_db
        try:
            col = get_collection()
        except ValueError:
            init_db()
            col = get_collection()

        stock_res = col.get(where={"type": "stok"}, include=["metadatas"])

        for sid, meta in zip(stock_res["ids"], stock_res["metadatas"]):
            miktar = meta.get("miktar", 0)

            if miktar < 5:
                if sid not in check_critical_stock._alerted:
                    subject = f"KRITIK STOK UYARISI — {meta.get('kategori', sid)}"
                    html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Kritik Stok</title></head>
<body style="font-family:Arial,sans-serif;padding:20px">
<h2 style="color:#d32f2f">&#9888; Kritik Stok Uyard&#305;</h2>
<p><strong>{sid}</strong> — {meta.get('kategori', '')} kategorisindeki &#252;r&#252;n&#252;n sto&#287;u kritik seviyeye d&#252;&#351;t&#252;.</p>
<table style="border-collapse:collapse">
  <tr><td style="padding:6px 12px;font-weight:bold">Mevcut Miktar</td>
      <td style="padding:6px 12px;color:#d32f2f;font-weight:bold">{miktar}</td></tr>
  <tr><td style="padding:6px 12px;font-weight:bold">Fiyat</td>
      <td style="padding:6px 12px">{meta.get('fiyat', 0):,} &#8378;</td></tr>
  <tr><td style="padding:6px 12px;font-weight:bold">Son G&#252;ncelleme</td>
      <td style="padding:6px 12px">{meta.get('son_guncelleme', '')}</td></tr>
</table>
<p style="margin-top:16px;color:#555">L&#252;tfen acil tedarik i&#351;lemi ba&#351;lat&#305;n.</p>
</body>
</html>"""
                    sent = _send_email(subject, html)
                    if sent:
                        check_critical_stock._alerted.add(sid)
                        logger.warning(
                            f"Kritik stok uyarısı gönderildi: {sid} (miktar={miktar})"
                        )
            else:
                # Stok 5 üstüne çıktıysa cache'den çıkar — bir sonraki düşüşte yeniden uyarı verebilsin
                check_critical_stock._alerted.discard(sid)

    except Exception as e:
        logger.error(f"check_critical_stock hatası: {e}")


# ── Scheduler yönetimi ────────────────────────────────────────────────────────

def get_jobs_info() -> List[Dict]:
    """Scheduler'daki tüm job'ların bilgisini döner."""
    if scheduler is None:
        return []
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs


def init_scheduler() -> BackgroundScheduler:
    """Scheduler'ı başlatır; günlük rapor (08:00) ve kritik stok kontrolü (5 dk) job'larını ekler."""
    global scheduler

    try:
        scheduler = BackgroundScheduler(daemon=True)

        scheduler.add_job(
            func=send_email_report,
            trigger=CronTrigger(hour=8, minute=0),
            id="email_report_job",
            name="Günlük E-posta Raporu",
            replace_existing=True,
            misfire_grace_time=60,
        )

        scheduler.add_job(
            func=check_critical_stock,
            trigger=IntervalTrigger(minutes=5),
            id="critical_stock_check",
            name="Kritik Stok Kontrolü",
            replace_existing=True,
            misfire_grace_time=60,
        )

        scheduler.start()
        logger.info(
            "Otomasyon scheduler başlatıldı: "
            "email_report_job (her gün 08:00) + critical_stock_check (her 5 dk)"
        )
        return scheduler

    except Exception as e:
        logger.error(f"init_scheduler hatası: {e}")
        raise


def stop_scheduler() -> None:
    """Scheduler'ı düzgünce durdurur."""
    global scheduler
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=True)
            logger.info("Otomasyon scheduler durduruldu")
        except Exception as e:
            logger.error(f"Scheduler durdurma hatası: {e}")
        finally:
            scheduler = None
