# 🚀 Hızlı Başlangıç

Projeyi 2 dakikada çalıştırmak için bu rehberi takip edin.

## 1️⃣ Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

## 2️⃣ Ortam Değişkenlerini Ayarlayın

`.env` dosyasını açın ve gerekli değerleri girin:

```env
GEMINI_API_KEY=sk-your_actual_key_here
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## 3️⃣ Kurulumun Çalıştığını Doğrulayın

```bash
python test_setup.py
```

Tüm testler pass etmeli ✅

## 4️⃣ Streamlit UI'ı Başlatın

```bash
streamlit run chatbot_ui.py
```

Tarayıcınızda `http://localhost:8501` açılacak.

## 5️⃣ (Opsiyonel) FastAPI Sunucusunu Başlatın

**Başka bir terminal'de:**

```bash
python main.py
```

API sunucusu `http://localhost:8000` üzerinde çalışacak.

Swagger API Dokümantasyonu: `http://localhost:8000/docs`

---

## 📂 Proje Yapısı

```
business-assistant/
├── shared_utils.py       ← ChromaDB ve arama (Geliştirici A)
├── main.py              ← FastAPI uygulaması (Geliştirici A)
├── chatbot_ui.py        ← Streamlit UI (Geliştirici B)
├── automation.py        ← APScheduler (Geliştirici C)
├── config.py            ← Merkezi konfigürasyon
├── routers/             ← API route şablonları
│   ├── chat_router.py   ← Sohbet endpoints (Geliştirici B)
│   └── automation_router.py ← Otomasyon endpoints (Geliştirici C)
├── requirements.txt     ← Bağımlılıklar
├── .env                 ← Ortam değişkenleri (GİZLİ!)
├── README.md            ← Detaylı dokümantasyon
├── DEVELOPMENT_GUIDE.md ← Geliştirici rehberi
└── test_setup.py        ← Kurulum testi
```

---

## 🔧 Temel Komutlar

### Streamlit UI
```bash
streamlit run chatbot_ui.py
```

### FastAPI Server
```bash
python main.py
```

### İkisini Beraber Çalıştırma
```bash
# Terminal 1
python main.py

# Terminal 2
streamlit run chatbot_ui.py
```

### Veritabanını Test Etme
```python
python -c "
from shared_utils import init_db, get_context
init_db()
result = get_context('laptop')
print(f'Bulundu: {len(result[\"documents\"])} belge')
"
```

---

## 🆘 Sorun Giderme

| Hata | Çözüm |
|------|-------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` çalıştırın |
| `GEMINI_API_KEY not found` | `.env` dosyasını kontrol edin |
| `Port already in use` | `streamlit run chatbot_ui.py --server.port 8502` |
| `ChromaDB connection failed` | `chroma_data/` dizini kontrol edin |

---

## 📊 Proje Görevleri

✅ **Geliştirici A** - Altyapı (TAMAMLANDI)
- Veritabanı kurulumu
- FastAPI uygulaması
- Konfigürasyon yönetimi

⏳ **Geliştirici B** - Sohbet Modülü
- Gemini API entegrasyonu
- Streamlit arayüzü
- Chat endpoints

⏳ **Geliştirici C** - Otomasyon
- E-posta raporu
- APScheduler görevleri
- Automation endpoints

---

## 📚 Kaynak Dosyalar

- [README.md](README.md) - Detaylı dokümantasyon
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Geliştirici rehberi
- [main.py](main.py) - FastAPI kaynak kodu
- [chatbot_ui.py](chatbot_ui.py) - Streamlit UI kaynağı
- [shared_utils.py](shared_utils.py) - Yardımcı fonksiyonlar
- [automation.py](automation.py) - APScheduler kaynağı
- [config.py](config.py) - Konfigürasyon

---

## 🎯 İlk Adımlar

1. ✅ `pip install -r requirements.txt`
2. ✅ `.env` dosyasını düzenle
3. ✅ `python test_setup.py` çalıştır
4. ✅ `streamlit run chatbot_ui.py` başlat
5. ✅ Tarayıcıda `http://localhost:8501` aç

**Bitti!** 🎉

---

**Not:** Daha fazla bilgi için [README.md](README.md) ve [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) dosyalarını okuyun.
