"""
Streamlit UI for RAG-based business assistant chatbot.
Developed by: Developer B
"""

import streamlit as st
import logging
from dotenv import load_dotenv
from shared_utils import init_db, start_simulation_scheduler

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
    """Render sidebar with controls and information."""
    with st.sidebar:
        st.title("⚙️ Ayarlar")
        
        # Database status
        if st.session_state.db_initialized:
            st.success("✅ Veritabanı Aktif")
            st.caption("Simülasyon: Her 2 dakikada çalışıyor")
        else:
            st.error("❌ Veritabanı Bağlantısı Yok")
        
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
        if st.button("🗑️ Geçmişi Temizle"):
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


def render_main_chat_interface():
    """Render main chat interface."""
    st.markdown('<div class="main-title">🤖 RAG Tabanlı İşletme Asistanı</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>👨‍💼 Gemini API ile RAG tabanlı sohbet ve stok tablosu buraya eklenecek</strong><br><br>
    Lütfen işletme hakkında bir soru sorunuz. Sistem, ChromaDB veritabanında
    ilgili bilgileri arayarak Gemini API vasıtasıyla yanıt oluşturacaktır.
    </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Input area
    st.divider()
    col1, col2 = st.columns([0.9, 0.1])
    
    with col1:
        user_input = st.chat_input(
            "📝 Soru sorunuz...",
            placeholder="Örn: Kaç adet laptop stokumuz var?"
        )
    
    with col2:
        send_button = st.button("📤 Gönder", use_container_width=True)
    
    if user_input and send_button:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.search_history.append(user_input)
        
        # TODO: Developer B - Add Gemini API RAG response logic here
        # Steps:
        # 1. Call get_context(user_input) from shared_utils
        # 2. Send context + user_input to Gemini API
        # 3. Parse and display response
        
        # Placeholder response
        bot_response = "Bu fonksiyon henüz geliştirilmektedir. Gemini API entegrasyonu yapılacaktır."
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_response
        })
        
        st.rerun()


def render_data_view_section():
    """Render data viewing section."""
    st.divider()
    st.subheader("📊 Veri Görüntüsü")
    
    view_options = st.tabs(["Stok Durumu", "Siparişler", "Görevler"])
    
    with view_options[0]:
        st.write("📦 Stok Durumu Tablosu")
        st.caption("Stok bilgileri bu bölüme eklenecektir")
        # TODO: Developer B - Add stock data table here
    
    with view_options[1]:
        st.write("🛒 Siparişler Tablosu")
        st.caption("Sipariş bilgileri bu bölüme eklenecektir")
        # TODO: Developer B - Add orders data table here
    
    with view_options[2]:
        st.write("✅ Görevler Listesi")
        st.caption("Görev bilgileri bu bölüme eklenecektir")
        # TODO: Developer B - Add tasks data here


def main():
    """Main application entry point."""
    initialize_session_state()
    setup_page()
    render_sidebar()
    render_main_chat_interface()
    render_data_view_section()


if __name__ == "__main__":
    main()
