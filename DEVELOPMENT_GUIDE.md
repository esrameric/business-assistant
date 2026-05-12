# Geliştirici Rehberi

Bu rehber, her geliştirici için görevleri, beklentileri ve entegrasyon noktalarını açıklar.

---

## 👤 Geliştirici A: Altyapı (✅ TAMAMLANDI)

### Tamamlanan Görevler
- [x] Proje yapısını oluşturma
- [x] Python bağımlılıklarını tanımlama (requirements.txt)
- [x] ChromaDB başlatma ve mock veri ekleme (shared_utils.py)
- [x] FastAPI uygulamasını kurma (main.py)
- [x] Proje konfigürasyonu (config.py)

### Sağlanan Dosyalar
```
✅ requirements.txt          → Tüm bağımlılıklar
✅ shared_utils.py          → init_db(), get_context()
✅ main.py                  → FastAPI uygulaması
✅ config.py                → Merkezi konfigürasyon
✅ .env                      → Ortam değişkenleri şablonu
✅ .gitignore               → Git ignore kuralları
```

### Diğer Geliştiriciler İçin Sağlanan API'ler

#### ChromaDB Erişimi
```python
from shared_utils import init_db, get_context, get_collection

# Başlangıç
init_db()

# Veri arama
results = get_context("sorgu metni", n_results=5)
# Sonuç:
# {
#   "query": "sorgu metni",
#   "results_count": 5,
#   "documents": [...],
#   "metadatas": [...],
#   "distances": [...],
#   "success": True
# }

# Collection doğrudan erişim
collection = get_collection()
```

#### Konfigürasyon Erişimi
```python
from config import config

print(config.GEMINI_API_KEY)
print(config.API_HOST)
print(config.CHROMA_DB_PATH)
```

---

## 👤 Geliştirici B: Sohbet Modülü

### Sorumluluklar
1. **Streamlit UI Geliştirme** (chatbot_ui.py)
   - Gemini API ile RAG tabanlı sohbet
   - Stok/sipariş/görev tablolarının görüntülenmesi
   - Sohbet geçmiş yönetimi

2. **FastAPI Chat Endpoints** (routers/chat_router.py)
   - `/api/chat/message` - Mesaj gönderme
   - `/api/chat/history/{session_id}` - Geçmiş alma
   - `/api/chat/session/{session_id}` - Oturum silme

### Başlangıç Adımları

#### 1. Gerekli İmportları Ekleyin
```python
# chatbot_ui.py
import streamlit as st
from shared_utils import init_db, get_context
import google.generativeai as genai
from config import config
```

#### 2. Gemini API Yapılandırması
```python
# Başlangıçta
init_db()
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
```

#### 3. RAG Akışı Uygulayın
```python
# Kullanıcı mesajı aldığında
def get_rag_response(user_message: str) -> str:
    # 1. ChromaDB'den context al
    context_data = get_context(user_message, n_results=5)
    
    if not context_data["success"]:
        return "Veritabanı sorgusu başarısız oldu"
    
    # 2. Context'i formatlı prompt'a dönüştür
    context_text = "\n".join([
        f"- {doc}" 
        for doc in context_data["documents"]
    ])
    
    system_prompt = f"""
    Sen bir işletme asistanısın. Aşağıdaki bağlamda sağlanan bilgileri 
    kullanarak kullanıcının sorusunu yanıtla:
    
    BAĞLAM:
    {context_text}
    """
    
    # 3. Gemini API'ye gönder
    response = model.generate_content(
        f"{system_prompt}\n\nSoru: {user_message}",
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1024
        }
    )
    
    return response.text
```

#### 4. FastAPI Endpoint Uygulayın
```python
# routers/chat_router.py
from fastapi import APIRouter
from shared_utils import get_context
import google.generativeai as genai
from config import config

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    # Context al
    context = get_context(request.message)
    
    # Response oluştur
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    response = model.generate_content(
        f"Context: {context['documents']}\n\n{request.message}"
    )
    
    return ChatResponse(
        response=response.text,
        context_documents=context["documents"],
        session_id=request.session_id or "default"
    )
```

### Beklenen Tablolar (chatbot_ui.py)
- **Stok Tablosu**: `ürün`, `miktar`, `fiyat`, `kategori`
- **Siparişler Tablosu**: `sipariş_no`, `müşteri`, `tutar`, `durum`
- **Görevler Listesi**: `görev`, `kategori`, `öncelik`, `son_tarih`

### Test Etme
```bash
# Streamlit çalıştır
streamlit run chatbot_ui.py

# Veya FastAPI çalıştır (başka terminal)
python main.py
# Swagger UI: http://localhost:8000/docs
```
### Nasıl Çalışır?
```WhatsApp Akışı:
# Müşteri WhatsApp'tan yazar
    → Twilio webhook'u /api/whatsapp/webhook'a POST atar
    → ChromaDB'den ilgili sipariş/stok verisi çekilir
    → Gemini AI akıllı cevap üretir
    → TwiML ile yanıt Twilio'ya döner
    → Müşteriye WhatsApp mesajı gider
```

---

## 👤 Geliştirici C: Otomasyon Modülü

### Sorumluluklar
1. **APScheduler Kurulumu** (automation.py)
   - Günlük saat 08:00'de e-posta raporu gönderme
   - Diğer zamanlanmış görevleri yönetme

2. **FastAPI Automation Endpoints** (routers/automation_router.py)
   - `/api/automation/jobs` - Tüm görevleri listele
   - `/api/automation/jobs/email-report` - E-posta yapılandırması
   - `/api/automation/jobs/{job_id}/trigger` - Görevi manuel çalıştır

### Başlangıç Adımları

#### 1. E-Posta Fonksiyonu Uygulayın
```python
# automation.py - send_email_report() fonksiyonunu düzenle

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from shared_utils import get_context

def send_email_report():
    """Günlük e-posta raporu gönder"""
    
    # 1. Report verilerini topla
    stock_data = get_context("stok durumu", n_results=10)
    orders_data = get_context("sipariş durumu", n_results=10)
    tasks_data = get_context("beklemede görev", n_results=10)
    
    # 2. HTML rapor oluştur
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Günlük İşletme Raporu</h2>
        <h3>Stok Özeti</h3>
        <p>{stock_data['documents'][0]}</p>
        
        <h3>Sipariş Özeti</h3>
        <p>{orders_data['documents'][0]}</p>
        
        <h3>Görev Özeti</h3>
        <p>{tasks_data['documents'][0]}</p>
    </body>
    </html>
    """
    
    # 3. E-posta gönder
    try:
        email_sender = config.EMAIL_SENDER
        email_password = config.EMAIL_PASSWORD
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Günlük İşletme Raporu"
        msg['From'] = email_sender
        msg['To'] = email_sender  # veya recipient list
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL(
            config.EMAIL_SMTP_SERVER, 
            config.EMAIL_SMTP_PORT
        ) as server:
            server.login(email_sender, email_password)
            server.send_message(msg)
        
        logger.info("E-posta raporu başarıyla gönderildi")
        
    except Exception as e:
        logger.error(f"E-posta gönderme hatası: {str(e)}")
```

#### 2. FastAPI Endpoints Uygulayın
```python
# routers/automation_router.py

from automation import get_jobs_info, send_email_report

@router.get("/jobs")
async def get_scheduled_jobs():
    jobs = get_jobs_info()
    return [JobInfo(**job) for job in jobs]

@router.post("/jobs/{job_id}/trigger")
async def trigger_job_manually(job_id: str):
    if job_id == "email_report_job":
        send_email_report()
        return JobResponse(
            success=True,
            message="E-posta raporu başlatıldı"
        )
    # ... diğer jobs
```

#### 3. FastAPI'de Entegre Edin
```python
# main.py

from automation import setup_automation
from routers import automation_router

# Startup'ta
@app.on_event("startup")
async def startup_event():
    setup_automation(app)
    
# Router'ı ekle
app.include_router(
    automation_router.router,
    prefix="/api/automation",
    tags=["Automation"]
)
```

### Gmail SMTP Ayarları
1. Gmail hesabınızda 2FA etkinleştirin
2. [Google Account Security](https://myaccount.google.com/security) sayfasına gidin
3. "Uygulama şifreleri" bölümüne gidin
4. Uygulama şifresi oluşturun
5. Oluşturulan şifreyi `.env`'ye ekleyin

### Test Etme
```bash
# FastAPI sunucusunu başlat
python main.py

# Başka terminalde test et
curl -X POST http://localhost:8000/api/automation/jobs/email_report_job/trigger

# Swagger UI
# http://localhost:8000/docs
```

---

## 🔗 Modüller Arası İletişim

### Modül Bağımlılıkları
```
shared_utils.py (Base)
    ↓
main.py (FastAPI App)
    ↓
├─ routers/chat_router.py (Dev B)
├─ routers/automation_router.py (Dev C)
└─ chatbot_ui.py (Dev B)
│
automation.py (Dev C)
```

### İmport Örnekleri

**Sohbet Modülünde:**
```python
from shared_utils import init_db, get_context
from config import config
import google.generativeai as genai
```

**Otomasyon Modülünde:**
```python
from shared_utils import get_context
from config import config
from apscheduler.schedulers.background import BackgroundScheduler
```

### Hata Yönetimi
Tüm modüller standardize logging kullanır:
```python
import logging
logger = logging.getLogger(__name__)

try:
    # Kod
except Exception as e:
    logger.error(f"Hata: {str(e)}")
```

---

## 🧪 Test Etme Checklist'i

**Developer B:**
- [ ] Streamlit UI başarıyla çalışıyor
- [ ] ChromaDB ile sorgular doğru sonuç veriyor
- [ ] Gemini API bağlantısı çalışıyor
- [ ] Sohbet geçmişi kaydediliyor
- [ ] Tablolar doğru şekilde gösteriliyor
- [ ] FastAPI endpoints çalışıyor

**Developer C:**
- [ ] APScheduler başarıyla başlatılıyor
- [ ] E-posta yapılandırması kaydediliyor
- [ ] Günlük rapor saat 08:00'de gönderiliyor
- [ ] Manuel trigger çalışıyor
- [ ] Başarısız işler log'a yazılıyor
- [ ] FastAPI endpoints çalışıyor

---

## 📞 Komünikasyon

### Sık Sorulan Sorular

**S: ChromaDB'ye nasıl veri eklerim?**
A: `shared_utils.py`'deki `collection.add()` metodunu kullanın

**S: Gemini API çağrı başarısız olduğunda ne yapmalıyım?**
A: API anahtarınızı kontrol edin ve rate limits'e dikkat edin

**S: E-posta görevini manuel olarak nasıl çalıştırırım?**
A: `curl` veya `/api/automation/jobs/{job_id}/trigger` endpoint'ini kullanın

**S: Projeyi production'a nasıl deploy ederim?**
A: README.md ve config.py dosyalarındaki production configuration'ı inceyin

---

## 📚 Ek Kaynaklar

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Google Generative AI Python](https://ai.google.dev/tutorials/python_quickstart)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

---

**Son Güncelleme:** 2026-05-10
