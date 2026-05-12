"""
Otomasyon modülü birim testleri.
Mock SMTP ve ChromaDB kullanarak gerçek ağ/DB bağlantısı olmadan çalışır.

NOT: shared_utils.py modülü test ortamında load_dotenv() nedeniyle yüklenmeyebilir
(encoding sorunu). Bu dosya, shared_utils'i sys.modules üzerinden mock'layarak
automation.py fonksiyonlarını izole biçimde test eder.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# ------------------------------------------------------------------ #
# shared_utils'i gerçekten import etmeden önce sys.modules'a koy.    #
# Böylece automation.py içindeki "from shared_utils import ..."       #
# çağrıları da bu mock'u alır.                                        #
# ------------------------------------------------------------------ #
_mock_shared_utils = MagicMock()
sys.modules.setdefault("shared_utils", _mock_shared_utils)

# Şimdi automation modülünü güvenle yükleyebiliriz
import automation  # noqa: E402


# ==================== Yardımcı: koleksiyon mock'u ====================

def _make_collection_mock(
    stok_metas=None,
    stok_ids=None,
    siparis_metas=None,
    gorev_metas=None,
):
    """ChromaDB collection.get() çağrılarını simüle eden mock."""
    stok_metas = stok_metas or []
    stok_ids = stok_ids or [f"stok_{i:03d}" for i in range(len(stok_metas))]
    siparis_metas = siparis_metas or []
    gorev_metas = gorev_metas or []

    def _get_side_effect(where=None, include=None):
        type_filter = (where or {}).get("type", "")
        if type_filter == "stok":
            return {
                "ids": stok_ids,
                "metadatas": stok_metas,
                "documents": ["ürün açıklaması"] * len(stok_metas),
            }
        if type_filter == "sipariş":
            return {
                "ids": [f"siparis_{i:03d}" for i in range(len(siparis_metas))],
                "metadatas": siparis_metas,
                "documents": ["sipariş açıklaması"] * len(siparis_metas),
            }
        if type_filter == "görev":
            return {
                "ids": [f"gorev_{i:03d}" for i in range(len(gorev_metas))],
                "metadatas": gorev_metas,
                "documents": ["görev açıklaması"] * len(gorev_metas),
            }
        return {"ids": [], "metadatas": [], "documents": []}

    mock_col = MagicMock()
    mock_col.get.side_effect = _get_side_effect
    return mock_col


# ==================== Test Sınıfları ====================

class TestBuildHtmlReport(unittest.TestCase):
    """_build_html_report() fonksiyonu testleri."""

    def test_bos_veri_cokmuyor(self):
        """Boş veri setleriyle HTML üretimi hata vermemeli."""
        html = automation._build_html_report([], [], [])
        self.assertIn("<html", html)
        self.assertIn("UTF-8", html)

    def test_kritik_stok_ozet(self):
        """Kritik stok (miktar<10) sayısı özet kartında görünmeli."""
        stok = [{"type": "stok", "kategori": "Test", "miktar": 3, "fiyat": 100}]
        html = automation._build_html_report(stok, [], [])
        # 1 kritik stok → özet kartında sayı olarak bulunmalı
        self.assertIn("1", html)

    def test_bekleyen_siparis_gosteriliyor(self):
        """'Yeni' durumdaki müşteri adı raporda yer almalı."""
        siparis = [{"type": "sipariş", "musteri": "ACME", "tutar": 5000, "durum": "Yeni"}]
        html = automation._build_html_report([], siparis, [])
        self.assertIn("ACME", html)

    def test_tamamlanan_gorev_raporda_yok(self):
        """'Tamamlandı' statüsündeki görev açık görev listesinde olmamalı."""
        gorev_acik = [{"type": "görev", "kategori": "BT", "oncelik": "Orta",
                       "son_tarih": "2026-06-01", "status": "Beklemede"}]
        gorev_tamam = [{"type": "görev", "kategori": "BT", "oncelik": "Orta",
                        "son_tarih": "2026-06-01", "status": "Tamamlandı"}]
        html_acik = automation._build_html_report([], [], gorev_acik)
        html_tamam = automation._build_html_report([], [], gorev_tamam)
        self.assertIn("Beklemede", html_acik)
        self.assertIn("bulunmuyor", html_tamam)

    def test_utf8_charset_header(self):
        """HTML'de UTF-8 charset meta etiketi bulunmalı."""
        html = automation._build_html_report([], [], [])
        self.assertIn("charset", html.lower())
        self.assertIn("utf-8", html.lower())


class TestSendEmail(unittest.TestCase):
    """_send_email() SMTP entegrasyon testleri (mock SMTP)."""

    @patch("automation.smtplib.SMTP_SSL")
    def test_basarili_gonderim(self, mock_smtp_cls):
        """Geçerli credentials ile e-posta gönderilmeli."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", {
            "EMAIL_SENDER": "test@gmail.com",
            "EMAIL_PASSWORD": "secret",
            "EMAIL_SMTP_SERVER": "smtp.gmail.com",
            "EMAIL_SMTP_PORT": "465",
        }):
            result = automation._send_email("Konu", "<p>Test</p>")

        self.assertTrue(result)
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    def test_credentials_eksik_false_doner(self):
        """EMAIL_SENDER eksikse False dönmeli, exception fırlatmamalı."""
        with patch.dict("os.environ", {}, clear=True):
            result = automation._send_email("Konu", "<p>Test</p>")
        self.assertFalse(result)

    @patch("automation.smtplib.SMTP_SSL")
    def test_smtp_auth_hatasi(self, mock_smtp_cls):
        """SMTPAuthenticationError yakalanmalı, False dönmeli."""
        import smtplib
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", {
            "EMAIL_SENDER": "test@gmail.com",
            "EMAIL_PASSWORD": "yanlis_sifre",
            "EMAIL_SMTP_SERVER": "smtp.gmail.com",
            "EMAIL_SMTP_PORT": "465",
        }):
            result = automation._send_email("Konu", "<p>Test</p>")

        self.assertFalse(result)


class TestSendEmailReport(unittest.TestCase):
    """send_email_report() entegrasyon testleri."""

    def _run_with_mock(self, stok=None, siparis=None, gorev=None, email_ok=True):
        col = _make_collection_mock(
            stok_metas=stok or [],
            siparis_metas=siparis or [],
            gorev_metas=gorev or [],
        )
        # automation.py içinde: from shared_utils import get_collection
        # sys.modules['shared_utils'] zaten mock — sadece get_collection'ı override et
        _mock_shared_utils.get_collection.return_value = col

        with patch.object(automation, "_send_email", return_value=email_ok) as mock_send:
            result = automation.send_email_report()
            return result, mock_send

    def test_basarili_gonderim(self):
        """Veri varsa rapor gönderilmeli."""
        stok = [{"type": "stok", "kategori": "Test", "miktar": 20, "fiyat": 1000}]
        result, mock_send = self._run_with_mock(stok=stok)
        self.assertTrue(result)
        mock_send.assert_called_once()

    def test_bos_veriyle_cokmuyor(self):
        """Hiç veri olmasa bile rapor gönderilmeli."""
        result, mock_send = self._run_with_mock()
        self.assertTrue(result)

    def test_veritabani_hazir_degil(self):
        """get_collection ValueError atarsa False dönmeli, çökmemeli."""
        _mock_shared_utils.get_collection.side_effect = ValueError("DB yok")
        try:
            result = automation.send_email_report()
            self.assertFalse(result)
        finally:
            _mock_shared_utils.get_collection.side_effect = None


class TestCheckCriticalStock(unittest.TestCase):
    """check_critical_stock() cache mantığı testleri."""

    def setUp(self):
        automation._critical_stock_cache.clear()
        _mock_shared_utils.get_collection.side_effect = None

    def _run_check(self, stok_metas, stok_ids=None):
        col = _make_collection_mock(stok_metas=stok_metas, stok_ids=stok_ids)
        _mock_shared_utils.get_collection.return_value = col
        with patch.object(automation, "_send_email", return_value=True) as mock_send:
            result = automation.check_critical_stock()
            return result, mock_send

    def test_kritik_stok_uyari_gonderir(self):
        """Miktar < 5 olan stok için uyarı maili gönderilmeli."""
        stok = [{"type": "stok", "kategori": "Test", "miktar": 3, "fiyat": 100}]
        result, mock_send = self._run_check(stok, ["stok_001"])
        self.assertEqual(result["alerts_sent"], 1)
        mock_send.assert_called_once()

    def test_cache_tekrar_mail_atmaz(self):
        """Aynı (id, miktar) için ikinci kontrolde mail atılmamalı."""
        stok = [{"type": "stok", "kategori": "Test", "miktar": 3, "fiyat": 100}]
        self._run_check(stok, ["stok_001"])  # ilk çalışma — mail gönder
        result, mock_send = self._run_check(stok, ["stok_001"])  # ikinci — cache hit
        self.assertEqual(result["alerts_sent"], 0)
        mock_send.assert_not_called()

    def test_miktar_degisince_tekrar_uyari(self):
        """Miktar değişirse (4→2) yeni cache key oluşur → yeni uyarı."""
        stok_ilk = [{"type": "stok", "kategori": "Test", "miktar": 4, "fiyat": 100}]
        stok_dusuk = [{"type": "stok", "kategori": "Test", "miktar": 2, "fiyat": 100}]
        self._run_check(stok_ilk, ["stok_001"])
        result, mock_send = self._run_check(stok_dusuk, ["stok_001"])
        self.assertEqual(result["alerts_sent"], 1)
        mock_send.assert_called_once()

    def test_normal_stok_uyari_yok(self):
        """Miktar >= 5 ise uyarı gönderilmemeli."""
        stok = [{"type": "stok", "kategori": "Test", "miktar": 15, "fiyat": 100}]
        result, mock_send = self._run_check(stok, ["stok_001"])
        self.assertEqual(result["alerts_sent"], 0)
        mock_send.assert_not_called()

    def test_veritabani_hazir_degil_cokmuyor(self):
        """get_collection ValueError atarsa fonksiyon hata fırlatmamalı."""
        _mock_shared_utils.get_collection.side_effect = ValueError("DB yok")
        result = automation.check_critical_stock()
        self.assertEqual(result["alerts_sent"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
