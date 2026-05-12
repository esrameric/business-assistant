# RAG Business Assistant - Proje Rehberi

**Teknoloji Stack:** Python 3.11+, FastAPI, ChromaDB, Gemini API, Streamlit

---

## 📋 Proje Özeti

Bu proje, ChromaDB ve Google Gemini API kullanarak işletme verilerine dayalı bir Retrieval-Augmented Generation (RAG) tabanlı asistan sunar. Sistem üç ana modülden oluşur:

- **Ana API (FastAPI)**: REST API sunucu
- **Chatbot UI (Streamlit)**: Etkileşimli web arayüzü
- **Otomasyonu (APScheduler)**: Zamanlanmış görevler

---

## 🚀 Hızlı Başlangıç

### 1. Ortam Hazırlığı

Python 3.11 veya üstü sürümünün yüklü olduğunu doğrulayın:

```bash
python --version
```

Sanal ortam oluşturun:

```bash
python -m venv venv
```

Sanal ortamı etkinleştirin:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 2. Bağımlılıkları Yükleme

```bash
pip install -r requirements.txt
```

### 3. Ortam Değişkenleri Yapılandırması

`.env` dosyasını düzenleyin ve gerekli değerleri girin:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Gemini API Anahtarı Nasıl Alınır:**
1. [Google AI Studio](https://aistudio.google.com/app/apikeys) ziyaret edin
2. "Create API Key" butonuna tıklayın
3. Oluşturulan anahtarı `.env` dosyasına yapıştırın

**Gmail Şifresi Oluşturma:**
1. [Google Hesap Güvenliği](https://myaccount.google.com/security) sayfasına gidin
2. "Uygulama şifreleri" bölümüne gidin
3. Uygulama şifresi oluşturun ve `.env` dosyasına ekleyin

---

## 📁 Proje Yapısı

```
business-assistant/
│
├── main.py                 # FastAPI uygulaması ana dosyası
├── chatbot_ui.py          # Streamlit web arayüzü
├── automation.py          # APScheduler otomasyonu
├── shared_utils.py        # ChromaDB ve paylaşılan fonksiyonlar
│
├── requirements.txt       # Python bağımlılıkları
├── .env                   # Ortam değişkenleri (GİZLİ)
├── .gitignore            # Git tarafından göz ardı edilecek dosyalar
├── README.md             # Bu dosya
│
├── routers/              # API rotaları (geliştiriciler tarafından doldurulacak)
├── chroma_data/          # ChromaDB veritabanı dizini (otomatik oluşturulur)
└── logs/                 # Uygulama logları
```

---

## 🏃 Uygulamayı Çalıştırma

### Seçenek 1: Streamlit UI (Önerilen - Geliştirilme)

```bash
streamlit run chatbot_ui.py
```

Tarayıcınızda otomatik olarak `http://localhost:8501` adresine açılacaktır.

### Seçenek 2: FastAPI Sunucu

```bash
python main.py
```

API `http://localhost:8000` adresinde çalışacaktır.

API dokümantasyonu: `http://localhost:8000/docs` (Swagger UI)

### Seçenek 3: İkisini Beraber Çalıştırma

Terminal 1 (FastAPI):
```bash
python main.py
```

Terminal 2 (Streamlit):
```bash
streamlit run chatbot_ui.py
```

---

## 👨‍💻 Geliştirici Görevleri

### Geliştirici A: Altyapı (✅ Tamamlandı)
- [x] requirements.txt oluşturma
- [x] ChromaDB başlatma ve mock veri ekleme
- [x] FastAPI sunucu iskeletini kurma
- [x] Proje yapısını oluşturma

### Geliştirici B: Sohbet Modülü (⏳ Yapılacak)

`chatbot_ui.py` içinde:
1. Gemini API entegrasyonunu yapın
2. `get_context()` fonksiyonunu kullanarak ilgili belgeleri alın
3. Sohbet geçmişini yönetin
4. Stok ve sipariş tablolarını görüntüleyin

**API Endpoints:** Geliştirilecek
```
POST /api/chat/message - Sohbet mesajı gönderme
GET  /api/chat/history - Sohbet geçmişi alma
```

### Geliştirici C: Otomasyon Modülü (⏳ Yapılacak)

`automation.py` içinde:
1. E-posta gönderme logikasını uygulayın
2. Günlük istatistikler raporunu oluşturun
3. SMTP veya Gmail API ile e-posta gönderin

**Zamanlanmış Görevler:**
- Her gün saat 08:00'de e-posta raporu gönderme

---

## 🗄️ Veritabanı

### ChromaDB Detayları

- **Konum:** `./chroma_data/`
- **Collection:** `isletme_verileri`
- **Öğe Sayısı:** 20 (stok, sipariş, görev)
- **Arama Türü:** Kosinüs benzerliği (semantic search)

### Mock Veri Türleri

1. **Stok (Stock)**: Ürün bilgileri, miktar, fiyat
2. **Sipariş (Order)**: Müşteri siparişleri, tutarlar, durumlar
3. **Görev (Task)**: İşletme görevleri, öncelik, son tarih

### Veri Sorgulama Örneği

```python
from shared_utils import init_db, get_context

init_db()

# Doğal dille sorgulama
results = get_context("Kaç adet laptop var?")
print(results["documents"])
print(results["metadatas"])
```

---

## ⚙️ Dinamik Simülasyon Mekanizması

### Genel Bakış

Proje, **gerçekçi işletme verileri simülasyonu** için otomatik bir mekanizma içerir. Her **2 dakikada bir** ChromaDB'deki verileri dinamik olarak güncelleyen APScheduler tabanlı bir sistem çalışır.

### Simülasyon Bileşenleri

#### 1. **Dinamik Stok Yönetimi** (`update_stock_levels()`)

**Satış Simülasyonu:**
- Tüm ürünlerin **%40 ihtimali** vardır
- Seçilen ürünün stoğu **%10-20 oranında azaltılır**
- Örnek: Laptop HP (25 adet) → 20 adet

**Tedarik Simülasyonu:**
- Stok **10 adetinin altına** düşerse
- **%35 ihtimaliyle** otomatik **+50 adet** tedarik yapılır
- Örnek: WiFi Router (9 adet) → 59 adet

**Loglama:**
```
📉 Stok stok_001: 25 → 20 (Satış)
📈 Stok stok_013: 9 → 59 (Tedarik)
```

#### 2. **Sipariş Durumu Güncellemesi** (`update_order_status()`)

- **"Hazırlanıyor"** statüsündeki siparişlerin **%50 ihtimaliyle** durum değiştirilir
- Yeni durum: **"Kargoya Verildi"**
- Her simülasyon döngüsünde kontrol edilir

**Loglama:**
```
📦 Sipariş siparis_002: Hazırlanıyor → Kargoya Verildi
```

#### 3. **Görev Yönetimi** (`update_tasks()`)

**Görev Tamamlama:**
- Mevcut görevlerin **%30 ihtimaliyle** statüsü **"Tamamlandı"** olur
- Beklemede/Devam Ediyor durumundaki görevler güncellenebilir

**Yeni Görev Ekleme:**
- Her simülasyon döngüsünde **%20 ihtimaliyle** yeni görev eklenir
- Eklenen görev listesi:
  - "Yeni sipariş kontrolü: Sabah gelen tüm siparişler gözden geçirilmeli"
  - "Depo düzenleme: Yenilikleri kendi bölümlerine yerleştir"
  - "Müşteri takip: Beklemede olan sipariş statüsü güncelle"
  - "Stok kontrol: Kritik stok seviyeleri kontrol et"
  - "Tedarik planlaması: Eksik malzemeleri satıcıdan talep et"

**Loglama:**
```
✅ Görev gorev_003: → Tamamlandı
➕ Yeni Görev Eklendi: gorev_011
```

### Simülasyon Mimarisi

#### APScheduler Konfigürasyonu

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    func=simulate_business_activity,
    trigger=IntervalTrigger(minutes=2),
    id='business_simulation',
    name='Business Activity Simulation'
)
scheduler.start()
```

#### Thread Safety

Tüm database işlemleri thread-safe şekilde yapılır:

```python
import threading

db_lock = threading.Lock()

with db_lock:
    collection.update(
        ids=[item_id],
        metadatas=[updated_metadata]
    )
```

#### Metadata Yapısı

Tüm öğelerin metadata'sında `son_guncelleme` timestamp'i vardır:

```python
{
    "type": "stok",
    "kategori": "Bilgisayar",
    "miktar": 25,
    "fiyat": 45000,
    "son_guncelleme": "2026-05-10T14:30:45.123456"  # ISO format
}
```

### Simülasyon Başlangıç

#### FastAPI ile

`main.py` öntanımlı olarak başlangıçta simülasyonu başlatır:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_simulation_scheduler()  # ← Simülasyon başlatılır
    yield
    # Shutdown
    stop_simulation_scheduler()
```

#### Streamlit ile

`chatbot_ui.py`'de session state'de simülasyon başlatılır:

```python
if "db_initialized" not in st.session_state:
    init_db()
    start_simulation_scheduler()
    st.session_state.db_initialized = True
```

### Simülasyon Çıktısı Örneği

Konsol output her 2 dakikada bir:

```
INFO:shared_utils:🔄 SIMULATION UPDATE - Stock: 2 items | Orders: 1 items | Tasks: 2 items
INFO:shared_utils:  📉 Stok stok_003: 12 → 10 (Satış)
INFO:shared_utils:  📈 Stok stok_013: 9 → 59 (Tedarik)
INFO:shared_utils:  📦 Sipariş siparis_006: Hazırlanıyor → Kargoya Verildi
INFO:shared_utils:  ✅ Görev gorev_002: → Tamamlandı
INFO:shared_utils:  ➕ Yeni Görev Eklendi: gorev_011
```

### Simülasyon Kontrol Fonksiyonları

```python
from shared_utils import (
    start_simulation_scheduler,
    stop_simulation_scheduler,
    simulate_business_activity
)

# Simülasyonu başlat
start_simulation_scheduler()

# Manuel simülasyon çalıştırma (test için)
result = simulate_business_activity()
print(result)

# Simülasyonu durdur
stop_simulation_scheduler()
```

### Veri İstatistikleri

**Mock Data Kapsamı:**
- **20 Stok Ürünü**: Kategoriler - Bilgisayar, Aksesuar, Yazıcı, Tablet, Ağ, Güç, Depolama, Kasa, Soğutma, Kablo, Bellek
- **10 Sipariş**: 5 farklı müşteri, 5 farklı durum (Yeni, Onaylandı, Hazırlanıyor, Kargoya Verildi, Tamamlandı)
- **10 Görev**: 8 farklı kategori (Stok, Satış, Destek, İdari, BT, Pazarlama, Kalite, Depo, Mali, Tedarik)

---

## 🔍 API Endpoints

### Sistem
- `GET /health` - Sistem sağlık kontrolü

### Sohbet (Geliştirici B tarafından eklenecek)
- `POST /api/chat/message` - Sohbet mesajı gönderme
- `GET  /api/chat/history` - Geçmiş alma

### Otomasyon (Geliştirici C tarafından eklenecek)
- `GET /api/automation/jobs` - Zamanlanmış görevler
- `POST /api/automation/jobs` - Yeni görev ekleme

---

## 🐛 Sorun Giderme

### Problem: "GEMINI_API_KEY not found"
**Çözüm:** `.env` dosyasına geçerli bir Gemini API anahtarı ekleyin

### Problem: "ChromaDB connection failed"
**Çözüm:** `chroma_data/` dizinin yazma izni olduğunu kontrol edin

### Problem: "Module not found" hatası
**Çözüm:** Sanal ortamın etkin olduğundan ve bağımlılıkların yüklendiğinden emin olun
```bash
pip install -r requirements.txt --force-reinstall
```

### Problem: Port 8000 veya 8501 zaten kullanımda
**Çözüm:** Farklı port kullanın
```bash
streamlit run chatbot_ui.py --server.port 8502
```

---

## 📊 Logging

Uygulamalar `INFO` seviyesinde log tutar. Loglar:
- Terminal çıkışında gösterilir
- `logs/` dizinine yazılır (yapılandırıldığında)

---

## 🔒 Güvenlik Notları

1. **`.env` dosyasını asla commit etmeyin**
   - `.gitignore` içine ekleyin
   
2. **API Anahtarlarını güvenli tutun**
   - Production ortamında environment variables kullanın
   - CI/CD pipeline'ında secrets yönetimi kullanın

3. **CORS Yapılandırması**
   - `main.py`'da gerekirse CORS origins'i sınırlandırın

---

## 🧪 Test Etme

### Basit Test

```python
# test_setup.py
from shared_utils import init_db, get_context

init_db()
result = get_context("sipariş durumu")
assert result["success"] == True
assert result["results_count"] > 0
print("✅ Setup test passed!")
```

Çalıştırın:
```bash
python test_setup.py
```

---

## 📚 Kaynaklar

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Google Generative AI](https://ai.google.dev/)
- [APScheduler](https://apscheduler.readthedocs.io/)

---

## 📝 Lisans

Bu proje özel kullanım için hazırlanmıştır.

---

## 👥 Ekip

- **Geliştirici A:** Altyapı ve Veritabanı ( Esra Meriç TOPAKTAŞ )
- **Geliştirici B:** Sohbet ve UI ( Yasemin KOÇBIYIK )
- **Geliştirici C:** Otomasyon ve E-posta ( Taha Yusuf ERTEN )

---

**Son Güncelleme:** 2026-05-10  
**Versiyon:** 1.0.0
