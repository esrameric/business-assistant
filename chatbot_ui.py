"""
Streamlit UI for RAG-based business assistant chatbot.
Developed by: Developer B
"""

import streamlit as st
import pandas as pd
import logging
from dotenv import load_dotenv
from shared_utils import init_db, start_simulation_scheduler, get_context, get_collection
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def initialize_session_state():
    """Initialize Streamlit session state variables and start simulation."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False
        try:
            init_db()
            start_simulation_scheduler()
            st.session_state.db_initialized = True
            logger.info("Database and simulation initialized from Streamlit")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            st.error(f"❌ Veritabanı başlatılamadı: {e}")

    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = None
        try:
            import google.generativeai as genai
            
            def send_email_action():
                """Kullanıcının isteği üzerine (örneğin 'raporu mail at', 'mail gönder' vb. taleplerde) ilgili e-posta adresine işletmenin güncel stok, sipariş ve görev bilgilerini içeren günlük değerlendirme raporunu gönderir."""
                try:
                    from automation import send_email_report
                    send_email_report()
                    return "E-posta raporu başarıyla gönderildi."
                except Exception as e:
                    return f"E-posta gönderilirken hata oluştu: {str(e)}"

            if config.GEMINI_API_KEY:
                genai.configure(api_key=config.GEMINI_API_KEY)
                st.session_state.gemini_model = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    tools=[send_email_action]
                )
                logger.info("Gemini model initialized with tools")
            else:
                logger.warning("GEMINI_API_KEY not set")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")


def setup_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="İşletme Yardımcısı",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with controls and information. Returns (temperature, max_results)."""
    with st.sidebar:
        st.title("⚙️ Ayarlar")

        # Database status
        if st.session_state.get("db_initialized"):
            st.success("✅ Veritabanı Aktif")
            st.caption("Simülasyon: Her 2 dakikada çalışıyor")
        else:
            st.error("❌ Veritabanı Bağlantısı Yok")

        # Gemini status
        if st.session_state.get("gemini_model"):
            st.success("✅ Gemini API Aktif")
        else:
            st.warning("⚠️ Gemini API yapılandırılmamış")

        # Model settings
        st.subheader("Model Ayarları")
        temperature = st.slider(
            "Temperature (Yaratıcılık)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Düşük değerler daha tutarlı, yüksek değerler daha yaratıcı yanıtlar üretir"
        )

        max_results = st.slider(
            "Max Sonuç Sayısı",
            min_value=3,
            max_value=10,
            value=5,
            step=1,
            help="Veritabanından alınacak maksimum ilgili belge sayısı"
        )

        # Search history
        st.subheader("Arama Geçmişi")
        if st.button("🗑️ Sohbeti Temizle"):
            st.session_state.messages = []
            st.session_state.search_history = []
            st.rerun()

        if st.session_state.search_history:
            st.write("Son sorgular:")
            for query in st.session_state.search_history[-5:]:
                st.caption(f"• {query}")
        else:
            st.caption("Geçmiş boş")

        # Information
        st.divider()
        st.subheader("ℹ️ Bilgi")
        st.caption("""
        Bu uygulama, ChromaDB ve Gemini API kullanarak
        işletme verilerinize dayalı akıllı sohbet
        deneyimi sağlar.

        **Simülasyon:** Stok, siparişler ve görevler
        otomatik olarak güncelleniyor.
        """)

    return temperature, max_results


def get_gemini_response(user_message: str, temperature: float, max_results: int) -> str:
    """Retrieve ChromaDB context and query Gemini for a response."""
    try:
        from shared_utils import get_collection
        
        # 1. Semantik arama sonuçları
        context_data = get_context(user_message, n_results=max_results)

        # 2. Tüm veritabanının kesin durumu (Sayı ve miktarlar için kesin kaynak)
        collection = get_collection()
        all_data = collection.get()
        db_summary = ["--- TÜM GÜNCEL VERİTABANI ÖZETİ ---"]
        for doc, meta in zip(all_data.get("documents", []), all_data.get("metadatas", [])):
            meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items() if k != "son_guncelleme")
            db_summary.append(f"[{meta.get('type', 'belge').upper()}] {doc} -> Detaylar: {meta_str}")
        full_database_context = "\n".join(db_summary)

        if not context_data.get("success") or not context_data["documents"]:
            context_text = "Semantik arama sonucu bulunamadı."
        else:
            parts = []
            for doc, meta in zip(context_data["documents"], context_data["metadatas"]):
                meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items())
                parts.append(f"- Bilgi: {doc} | Veritabanı Detayları: {meta_str}")
            context_text = "\n".join(parts)

        model = st.session_state.get("gemini_model")
        if model is None:
            return (
                "⚠️ Gemini API yapılandırılmamış. "
                "Lütfen GEMINI_API_KEY değerini .env dosyasına ekleyin."
            )

        import google.generativeai as genai

        full_prompt = (
            "Sen bir KOBİ işletme asistanısın. Kullanıcının sorusunu yanıtlarken "
            "AŞAĞIDAKİ TÜM GÜNCEL VERİ TABANI TABLOLARINI BİRİNCİL KAYNAK OLARAK KULLAN.\n"
            "Kullanıcı herhangi bir ürünün stok miktarını, fiyatını veya sipariş durumunu soruyorsa, "
            "veritabanı özetine bakarak KESİN VE NET SAYILARI VER. Veritabanındaki ürün ismine benzeyen öğeleri bul ve miktar parametresini ("
            "meta_str = 'miktar: 46') içeren detayı kullanarak söyle.\n\n"
            f"{full_database_context}\n\n"
            f"İLGİLİ SEMANTİK ARAMALAR:\n{context_text}\n\n"
            f"Kullanıcı sorusu: {user_message}"
        )

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(full_prompt, generation_config=generation_config)
        return response.text

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"❌ Yanıt üretilirken hata oluştu: {e}"


def render_main_chat_interface(temperature: float, max_results: int):
    """Render main chat interface."""
    st.markdown('<div class="main-title">🤖 RAG Tabanlı İşletme Asistanı</div>', unsafe_allow_html=True)

    chat_container = st.container(height=400, border=True)
    with chat_container:
        if not st.session_state.messages:
            st.caption(
                "Merhaba! İşletmeniz hakkında sorular sorabilirsiniz. "
                "Örn: 'Kaç adet laptop var?', 'Bekleyen siparişler neler?'"
            )
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    user_input = st.chat_input("Örn: Kaç adet laptop stokumuz var?")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.search_history.append(user_input)

        with st.spinner("Yanıt hazırlanıyor..."):
            bot_response = get_gemini_response(user_input, temperature, max_results)

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()


def _highlight_critical_stock(row: pd.Series):
    """Return red background for rows where Miktar < 10."""
    if "Miktar" in row and row["Miktar"] < 10:
        return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)


def render_data_view_section():
    """Render data viewing section with three tabs."""
    st.divider()
    st.subheader("📊 Veri Görüntüsü")

    tab_stok, tab_siparis, tab_gorev = st.tabs(["Stok Durumu", "Siparişler", "Görevler"])

    with tab_stok:
        try:
            col = get_collection()
            results = col.get(where={"type": "stok"}, include=["documents", "metadatas"])
            metas = results["metadatas"]
            docs = results["documents"]
            st.write(f"📦 {len(metas)} ürün")
            if metas:
                rows = [
                    {
                        "Ürün": (d[:60] + "...") if len(d) > 60 else d,
                        "Kategori": m.get("kategori", ""),
                        "Miktar": m.get("miktar", 0),
                        "Fiyat (₺)": m.get("fiyat", 0),
                        "Son Güncelleme": str(m.get("son_guncelleme", ""))[:19],
                    }
                    for d, m in zip(docs, metas)
                ]
                df = pd.DataFrame(rows)
                styled = df.style.apply(_highlight_critical_stock, axis=1)
                st.dataframe(styled, use_container_width=True)
            else:
                st.info("Stok verisi bulunamadı.")
        except Exception as e:
            st.error(f"Stok verisi yüklenemedi: {e}")

    with tab_siparis:
        try:
            col = get_collection()
            results = col.get(where={"type": "sipariş"}, include=["documents", "metadatas"])
            metas = results["metadatas"]
            docs = results["documents"]
            st.write(f"🛒 {len(metas)} sipariş")
            if metas:
                rows = [
                    {
                        "Sipariş": (d[:60] + "...") if len(d) > 60 else d,
                        "Müşteri": m.get("musteri", ""),
                        "Tutar (₺)": m.get("tutar", 0),
                        "Durum": m.get("durum", ""),
                        "Son Güncelleme": str(m.get("son_guncelleme", ""))[:19],
                    }
                    for d, m in zip(docs, metas)
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                st.info("Sipariş verisi bulunamadı.")
        except Exception as e:
            st.error(f"Sipariş verisi yüklenemedi: {e}")

    with tab_gorev:
        try:
            col = get_collection()
            results = col.get(where={"type": "görev"}, include=["documents", "metadatas"])
            metas = results["metadatas"]
            docs = results["documents"]
            st.write(f"✅ {len(metas)} görev")
            if metas:
                rows = [
                    {
                        "Görev": (d[:60] + "...") if len(d) > 60 else d,
                        "Kategori": m.get("kategori", ""),
                        "Öncelik": m.get("oncelik", ""),
                        "Son Tarih": m.get("son_tarih", ""),
                        "Durum": m.get("status", ""),
                    }
                    for d, m in zip(docs, metas)
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                st.info("Görev verisi bulunamadı.")
        except Exception as e:
            st.error(f"Görev verisi yüklenemedi: {e}")


def main():
    """Main application entry point."""
    setup_page()
    initialize_session_state()
    temperature, max_results = render_sidebar()
    render_main_chat_interface(temperature, max_results)
    render_data_view_section()


if __name__ == "__main__":
    main()
