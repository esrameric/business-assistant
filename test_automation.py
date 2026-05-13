"""
automation.py için unit testler — SMTP mock'lu, gerçek mail gönderimi yok.
"""

import unittest
from unittest.mock import MagicMock, patch, call


# ── _build_html_report testleri ───────────────────────────────────────────────

class TestBuildHtmlReport(unittest.TestCase):
    """_build_html_report fonksiyonu için testler."""

    def setUp(self):
        from automation import _build_html_report
        self.fn = _build_html_report

    def test_empty_data_does_not_raise(self):
        """Boş listelerle çağrıldığında exception fırlatmamalı."""
        html = self.fn([], [], [])
        self.assertIsInstance(html, str)
        self.assertTrue(len(html) > 0)

    def test_returns_html_string(self):
        """Dolu veriyle geçerli HTML üretmeli."""
        stocks = [{"id": "stok_001", "kategori": "Bilgisayar", "miktar": 3, "fiyat": 10000}]
        orders = [{"id": "siparis_001", "musteri": "TestCo", "durum": "Yeni", "tutar": 5000}]
        tasks = [{"id": "gorev_001", "kategori": "BT", "oncelik": "Yüksek", "status": "Beklemede", "son_tarih": "2026-05-20"}]
        html = self.fn(stocks, orders, tasks)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)

    def test_contains_utf8_meta_charset(self):
        """HTML çıktısı UTF-8 charset meta etiketi içermeli."""
        html = self.fn([], [], [])
        self.assertIn('charset="UTF-8"', html)

    def test_stock_id_in_html(self):
        """Kritik stok ID'si HTML çıktısında görünmeli."""
        stocks = [{"id": "stok_013", "kategori": "Ağ", "miktar": 2, "fiyat": 6500}]
        html = self.fn(stocks, [], [])
        self.assertIn("stok_013", html)

    def test_empty_stock_shows_no_critical_message(self):
        """Kritik stok yoksa 'bulunmuyor' mesajı gösterilmeli."""
        html = self.fn([], [], [])
        self.assertIn("bulunmuyor", html.lower())

    def test_order_customer_in_html(self):
        """Sipariş müşteri adı HTML çıktısında bulunmalı."""
        orders = [{"id": "siparis_002", "musteri": "TestMusteri", "durum": "Beklemede", "tutar": 9999}]
        html = self.fn([], orders, [])
        self.assertIn("TestMusteri", html)

    def test_task_category_in_html(self):
        """Görev kategorisi HTML çıktısında bulunmalı."""
        tasks = [{"id": "gorev_001", "kategori": "Mali", "oncelik": "Orta", "status": "Beklemede", "son_tarih": "2026-06-01"}]
        html = self.fn([], [], tasks)
        self.assertIn("Mali", html)


# ── _send_email testleri ──────────────────────────────────────────────────────

class TestSendEmail(unittest.TestCase):
    """_send_email fonksiyonu için testler."""

    def test_returns_false_when_no_sender(self):
        """EMAIL_SENDER boşsa False dönmeli, exception fırlatmamalı."""
        with patch("automation.config") as mock_cfg:
            mock_cfg.EMAIL_SENDER = ""
            mock_cfg.EMAIL_PASSWORD = "testpass"
            from automation import _send_email
            result = _send_email("konu", "<p>test</p>")
        self.assertFalse(result)

    def test_returns_false_when_no_password(self):
        """EMAIL_PASSWORD boşsa False dönmeli, exception fırlatmamalı."""
        with patch("automation.config") as mock_cfg:
            mock_cfg.EMAIL_SENDER = "test@gmail.com"
            mock_cfg.EMAIL_PASSWORD = ""
            from automation import _send_email
            result = _send_email("konu", "<p>test</p>")
        self.assertFalse(result)

    def test_calls_smtp_with_correct_params(self):
        """SMTP_SSL doğru sunucu/port parametreleriyle çağrılmalı."""
        with patch("automation.config") as mock_cfg, \
             patch("automation.smtplib.SMTP_SSL") as mock_smtp_cls:
            mock_cfg.EMAIL_SENDER = "sender@gmail.com"
            mock_cfg.EMAIL_PASSWORD = "testpassword"
            mock_cfg.EMAIL_SMTP_SERVER = "smtp.gmail.com"
            mock_cfg.EMAIL_SMTP_PORT = 465
            mock_cfg.EMAIL_RECIPIENT = "recipient@gmail.com"

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            from automation import _send_email
            result = _send_email("test konu", "<p>içerik</p>")

            mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
            mock_server.login.assert_called_once_with("sender@gmail.com", "testpassword")
            self.assertTrue(result)

    def test_smtp_exception_returns_false(self):
        """SMTP exception alırsa False dönmeli, exception yukarı çıkmamalı."""
        with patch("automation.config") as mock_cfg, \
             patch("automation.smtplib.SMTP_SSL") as mock_smtp_cls:
            mock_cfg.EMAIL_SENDER = "sender@gmail.com"
            mock_cfg.EMAIL_PASSWORD = "pass"
            mock_cfg.EMAIL_SMTP_SERVER = "smtp.gmail.com"
            mock_cfg.EMAIL_SMTP_PORT = 465
            mock_cfg.EMAIL_RECIPIENT = None

            mock_smtp_cls.side_effect = Exception("Bağlantı hatası")

            from automation import _send_email
            result = _send_email("konu", "<p>test</p>")
        self.assertFalse(result)


# ── send_email_report testleri ────────────────────────────────────────────────

class TestSendEmailReport(unittest.TestCase):
    """send_email_report tam flow testleri."""

    def _make_mock_collection(self):
        """ChromaDB collection mock'u oluşturur."""
        stock_data = {"ids": ["stok_013"], "metadatas": [{"type": "stok", "kategori": "Ağ", "miktar": 3, "fiyat": 6500, "son_guncelleme": "2026-05-13"}]}
        order_data = {"ids": ["siparis_001"], "metadatas": [{"type": "sipariş", "musteri": "TestCo", "tutar": 5000, "durum": "Yeni", "son_guncelleme": "2026-05-13"}]}
        task_data = {"ids": ["gorev_001"], "metadatas": [{"type": "görev", "kategori": "BT", "oncelik": "Yüksek", "status": "Beklemede", "son_tarih": "2026-05-20", "son_guncelleme": "2026-05-13"}]}
        col = MagicMock()
        col.get.side_effect = lambda where, include: (
            stock_data if where.get("type") == "stok"
            else order_data if where.get("type") == "sipariş"
            else task_data
        )
        return col

    def test_full_flow_with_mock_collection(self):
        """Mock collection ile tam flow çalışmalı; _send_email çağrılmalı."""
        col = self._make_mock_collection()

        import sys
        mock_utils = MagicMock()
        mock_utils.get_collection.return_value = col
        mock_utils.init_db = MagicMock()

        with patch.dict("sys.modules", {"shared_utils": mock_utils}), \
             patch("automation._send_email", return_value=True) as mock_send:
            from automation import send_email_report
            send_email_report()

        self.assertTrue(mock_send.called)

    def test_no_credentials_returns_false(self):
        """Kimlik bilgileri eksikse send_email_report False dönmeli."""
        col = MagicMock()
        col.get.return_value = {"ids": [], "metadatas": []}

        import sys
        mock_utils = MagicMock()
        mock_utils.get_collection.return_value = col
        mock_utils.init_db = MagicMock()

        with patch.dict("sys.modules", {"shared_utils": mock_utils}), \
             patch("automation.config") as mock_cfg:
            mock_cfg.EMAIL_SENDER = ""
            mock_cfg.EMAIL_PASSWORD = ""
            mock_cfg.EMAIL_SMTP_SERVER = "smtp.gmail.com"
            mock_cfg.EMAIL_SMTP_PORT = 465

            from automation import send_email_report
            result = send_email_report()

        self.assertFalse(result)


# ── check_critical_stock testleri ────────────────────────────────────────────

class TestCheckCriticalStock(unittest.TestCase):
    """check_critical_stock cache mantığı testleri."""

    def setUp(self):
        """Her testten önce cache'i sıfırla."""
        from automation import check_critical_stock
        if hasattr(check_critical_stock, "_alerted"):
            check_critical_stock._alerted.clear()

    def _mock_collection(self, stocks: list):
        col = MagicMock()
        col.get.return_value = {
            "ids": [s["id"] for s in stocks],
            "metadatas": [{k: v for k, v in s.items() if k != "id"} for s in stocks],
        }
        return col

    def test_sends_alert_for_critical_stock(self):
        """Miktar < 5 olan ürün için mail gönderilmeli."""
        stocks = [{"id": "stok_001", "kategori": "Bilgisayar", "miktar": 2, "fiyat": 1000, "son_guncelleme": "2026-05-13"}]
        col = self._mock_collection(stocks)

        import sys
        mock_utils = MagicMock()
        mock_utils.get_collection.return_value = col

        with patch.dict("sys.modules", {"shared_utils": mock_utils}), \
             patch("automation._send_email", return_value=True) as mock_send:
            from automation import check_critical_stock
            check_critical_stock()

        mock_send.assert_called_once()

    def test_cache_prevents_duplicate_alert(self):
        """Aynı kritik ürün için iki kez ardışık çağrıda yalnızca bir mail gönderilmeli."""
        stocks = [{"id": "stok_001", "kategori": "Bilgisayar", "miktar": 2, "fiyat": 1000, "son_guncelleme": "2026-05-13"}]
        col = self._mock_collection(stocks)

        import sys
        mock_utils = MagicMock()
        mock_utils.get_collection.return_value = col

        with patch.dict("sys.modules", {"shared_utils": mock_utils}), \
             patch("automation._send_email", return_value=True) as mock_send:
            from automation import check_critical_stock
            check_critical_stock()
            check_critical_stock()  # ikinci çağrı

        self.assertEqual(mock_send.call_count, 1)

    def test_cache_reset_when_stock_recovers(self):
        """Stok 5 üstüne çıkınca cache temizlenmeli; bir sonraki düşüşte tekrar uyarı verilmeli."""
        from automation import check_critical_stock

        # İlk durum: kritik stok
        stocks_critical = [{"id": "stok_001", "kategori": "Ağ", "miktar": 3, "fiyat": 1000, "son_guncelleme": "t1"}]
        col_critical = self._mock_collection(stocks_critical)

        # Toparlanmış stok
        stocks_ok = [{"id": "stok_001", "kategori": "Ağ", "miktar": 60, "fiyat": 1000, "son_guncelleme": "t2"}]
        col_ok = self._mock_collection(stocks_ok)

        # Tekrar kritik stok
        col_critical2 = self._mock_collection(stocks_critical)

        import sys

        send_count = []

        def fake_send(subject, body):
            send_count.append(1)
            return True

        mock_utils = MagicMock()

        with patch("automation._send_email", side_effect=fake_send):
            # 1. çağrı — kritik, uyarı gider
            mock_utils.get_collection.return_value = col_critical
            with patch.dict("sys.modules", {"shared_utils": mock_utils}):
                check_critical_stock()
            self.assertEqual(len(send_count), 1)

            # 2. çağrı — stok toparlandı, cache temizlendi
            mock_utils.get_collection.return_value = col_ok
            with patch.dict("sys.modules", {"shared_utils": mock_utils}):
                check_critical_stock()
            self.assertEqual(len(send_count), 1)  # mail gönderilmedi

            # 3. çağrı — tekrar kritik, yeniden uyarı verilmeli
            mock_utils.get_collection.return_value = col_critical2
            with patch.dict("sys.modules", {"shared_utils": mock_utils}):
                check_critical_stock()
            self.assertEqual(len(send_count), 2)

    def test_no_alert_above_threshold(self):
        """Miktar >= 5 ise mail gönderilmemeli."""
        stocks = [{"id": "stok_001", "kategori": "Bellek", "miktar": 10, "fiyat": 500, "son_guncelleme": "2026-05-13"}]
        col = self._mock_collection(stocks)

        import sys
        mock_utils = MagicMock()
        mock_utils.get_collection.return_value = col

        with patch.dict("sys.modules", {"shared_utils": mock_utils}), \
             patch("automation._send_email", return_value=True) as mock_send:
            from automation import check_critical_stock
            check_critical_stock()

        mock_send.assert_not_called()


# ── init_scheduler testleri ───────────────────────────────────────────────────

class TestInitScheduler(unittest.TestCase):
    """Scheduler başlatma testleri."""

    def tearDown(self):
        """Test sonrası scheduler'ı durdur."""
        import automation
        if automation.scheduler is not None:
            try:
                automation.scheduler.shutdown(wait=False)
            except Exception:
                pass
            automation.scheduler = None

    def test_creates_two_jobs(self):
        """init_scheduler çağrısı tam olarak 2 job oluşturmalı."""
        from automation import init_scheduler
        sched = init_scheduler()
        jobs = sched.get_jobs()
        self.assertEqual(len(jobs), 2)

    def test_job_ids_are_correct(self):
        """Oluşturulan job ID'leri doğru olmalı."""
        from automation import init_scheduler
        sched = init_scheduler()
        job_ids = {job.id for job in sched.get_jobs()}
        self.assertIn("email_report_job", job_ids)
        self.assertIn("critical_stock_check", job_ids)

    def test_get_jobs_info_returns_list(self):
        """get_jobs_info scheduler başlatılmışsa liste dönmeli."""
        from automation import init_scheduler, get_jobs_info
        init_scheduler()
        info = get_jobs_info()
        self.assertIsInstance(info, list)
        self.assertEqual(len(info), 2)
        for job in info:
            self.assertIn("id", job)
            self.assertIn("name", job)
            self.assertIn("trigger", job)


if __name__ == "__main__":
    unittest.main()
