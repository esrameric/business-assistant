"""
Shared utilities for RAG system.
Handles ChromaDB initialization, semantic search, and business simulation.
"""

import os
import logging
import random
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from chromadb import PersistentClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global ChromaDB client
client = None
collection = None
simulation_scheduler = None

# Thread-safe lock for database operations
db_lock = threading.Lock()


def init_db() -> None:
    """
    Initialize ChromaDB client and create/populate the collection with mock data.
    
    Raises:
        Exception: If database initialization fails
    """
    global client, collection
    
    try:
        # Initialize persistent ChromaDB client (new API)
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_data")
        client = PersistentClient(path=db_path)
        logger.info(f"ChromaDB PersistentClient initialized with path: {db_path}")

        # Get or create collection
        collection = client.get_or_create_collection(
            name="isletme_verileri",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Collection 'isletme_verileri' created/loaded")
        
        # Add mock data if collection is empty
        if collection.count() == 0:
            _populate_mock_data()
            logger.info("Mock data successfully added to collection")
        else:
            logger.info(f"Collection already contains {collection.count()} documents")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def _populate_mock_data() -> None:
    """
    Populate collection with comprehensive mock business data.
    Includes 20 stock items, 10 orders, and 10 tasks for realistic simulation.
    """
    mock_data = [
        # Stok (Stock) items - 20 products for realistic inventory
        {
            "id": "stok_001",
            "content": "Laptop HP EliteBook 840 G9 - İşlemci: Intel i7, RAM: 16GB, SSD: 512GB",
            "metadata": {"type": "stok", "kategori": "Bilgisayar", "miktar": 25, "fiyat": 45000, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_002",
            "content": "Monitor Samsung 27 inç 4K UHD - Çözünürlük: 3840x2160",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 50, "fiyat": 8500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_003",
            "content": "Yazıcı Canon imagePRUNT 5255 - Renk: Siyah, Yazdırma hızı: 55 ppm",
            "metadata": {"type": "stok", "kategori": "Yazıcı", "miktar": 12, "fiyat": 35000, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_004",
            "content": "Fare Logitech MX Master 3S - Bluetooth ve USB bağlantı",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 100, "fiyat": 2800, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_005",
            "content": "Klavye Mechanical RGB Cherry MX - Türkçe F layout",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 75, "fiyat": 1500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_006",
            "content": "USB-C Hub 7 Port - Thunderbolt 3 uyumlu, 100W güç kaynağı",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 150, "fiyat": 3500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_007",
            "content": "Notebook 15.6 inç Intel Core i5 - RAM: 8GB, SSD: 256GB",
            "metadata": {"type": "stok", "kategori": "Bilgisayar", "miktar": 18, "fiyat": 28000, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_008",
            "content": "Başlık Sony WH-1000XM5 - Gürültü iptal, 30 saat batarya",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 35, "fiyat": 4200, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_009",
            "content": "Webcam Logitech C920 - 1080p Full HD, Otomatik odaklama",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 42, "fiyat": 1800, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_010",
            "content": "Harici SSD Samsung T5 1TB - Taşınabilir, 1050MB/s okuma hızı",
            "metadata": {"type": "stok", "kategori": "Depolama", "miktar": 28, "fiyat": 5500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_011",
            "content": "Tablet Apple iPad Pro 12.9 M2 - 128GB, WiFi+Cellular",
            "metadata": {"type": "stok", "kategori": "Tablet", "miktar": 15, "fiyat": 35000, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_012",
            "content": "Taş iPad Pencil - 2. nesil, manyetik bağlantı",
            "metadata": {"type": "stok", "kategori": "Aksesuar", "miktar": 22, "fiyat": 3500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_013",
            "content": "WiFi Router ASUS ROG Rapture GT-AX12000 - WiFi 6, gaming",
            "metadata": {"type": "stok", "kategori": "Ağ", "miktar": 9, "fiyat": 6500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_014",
            "content": "UPS APC Smart-UPS 1500VA - 675W, yazılım kontrolü",
            "metadata": {"type": "stok", "kategori": "Güç", "miktar": 11, "fiyat": 8000, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_015",
            "content": "HDMI Kablo 2.1 8K - 2 metrelik, dayanıklı konnektör",
            "metadata": {"type": "stok", "kategori": "Kablo", "miktar": 200, "fiyat": 250, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_016",
            "content": "Güç Kaynağı Corsair RM850e - 850W 80+ Gold modüler",
            "metadata": {"type": "stok", "kategori": "Güç", "miktar": 19, "fiyat": 3800, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_017",
            "content": "RAM Kingston Fury Beast 16GB DDR4 3600MHz - RGB",
            "metadata": {"type": "stok", "kategori": "Bellek", "miktar": 45, "fiyat": 1200, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_018",
            "content": "SSD WD_BLACK 1TB - PCIe 4.0 NVMe, oyun optimizasyonu",
            "metadata": {"type": "stok", "kategori": "Depolama", "miktar": 31, "fiyat": 4500, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_019",
            "content": "Soğutucu be quiet! Dark Rock Pro TR4 - Çift tower 250W",
            "metadata": {"type": "stok", "kategori": "Soğutma", "miktar": 14, "fiyat": 2200, "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "stok_020",
            "content": "Kasa Lian Li Lancool 216 - ATX, RGB şerit dahil",
            "metadata": {"type": "stok", "kategori": "Kasa", "miktar": 16, "fiyat": 1500, "son_guncelleme": datetime.now().isoformat()}
        },
        # Sipariş (Order) items - 10 orders with different statuses
        {
            "id": "siparis_001",
            "content": "Sipariş #2026-001: 10x Laptop HP EliteBook, müşteri Acme Corp, tarih: 2026-05-08",
            "metadata": {"type": "sipariş", "musteri": "Acme Corp", "tutar": 450000, "durum": "Onaylandı", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_002",
            "content": "Sipariş #2026-002: 5x Monitor Samsung 4K, müşteri TechHub, tarih: 2026-05-09",
            "metadata": {"type": "sipariş", "musteri": "TechHub", "tutar": 42500, "durum": "Hazırlanıyor", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_003",
            "content": "Sipariş #2026-003: 2x Yazıcı Canon, müşteri PrintWorks, tarih: 2026-05-07",
            "metadata": {"type": "sipariş", "musteri": "PrintWorks", "tutar": 70000, "durum": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_004",
            "content": "Sipariş #2026-004: 20x Fare ve 15x Klavye, müşteri OfficeSupply, tarih: 2026-05-10",
            "metadata": {"type": "sipariş", "musteri": "OfficeSupply", "tutar": 78500, "durum": "Yeni", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_005",
            "content": "Sipariş #2026-005: 30x Monitor Samsung, müşteri DataCenter Inc, tarih: 2026-05-06",
            "metadata": {"type": "sipariş", "musteri": "DataCenter Inc", "tutar": 255000, "durum": "Tamamlandı", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_006",
            "content": "Sipariş #2026-006: 40x USB-C Hub, müşteri TechRetail, tarih: 2026-05-09",
            "metadata": {"type": "sipariş", "musteri": "TechRetail", "tutar": 140000, "durum": "Hazırlanıyor", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_007",
            "content": "Sipariş #2026-007: 8x iPad Pro, müşteri CreativeStudio, tarih: 2026-05-08",
            "metadata": {"type": "sipariş", "musteri": "CreativeStudio", "tutar": 280000, "durum": "Kargoya Verildi", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_008",
            "content": "Sipariş #2026-008: 50x Başlık Sony, müşteri RetailChain, tarih: 2026-05-10",
            "metadata": {"type": "sipariş", "musteri": "RetailChain", "tutar": 210000, "durum": "Hazırlanıyor", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_009",
            "content": "Sipariş #2026-009: 12x Router ASUS, müşteri ISPProvider, tarih: 2026-05-05",
            "metadata": {"type": "sipariş", "musteri": "ISPProvider", "tutar": 78000, "durum": "Tamamlandı", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "siparis_010",
            "content": "Sipariş #2026-010: 25x RAM Kingston, müşteri BuilderCorp, tarih: 2026-05-09",
            "metadata": {"type": "sipariş", "musteri": "BuilderCorp", "tutar": 30000, "durum": "Hazırlanıyor", "son_guncelleme": datetime.now().isoformat()}
        },
        # Görev (Task) items - 10 tasks with different categories
        {
            "id": "gorev_001",
            "content": "Stok taraması: Tüm laptopların envanter sayısı kontrol edilmesi ve sistem güncellenmesi",
            "metadata": {"type": "görev", "kategori": "Stok", "oncelik": "Yüksek", "son_tarih": "2026-05-15", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_002",
            "content": "Müşteri Acme Corp ile Sipariş #2026-001 hakkında teslimat saati koordinasyonu",
            "metadata": {"type": "görev", "kategori": "Satış", "oncelik": "Yüksek", "son_tarih": "2026-05-11", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_003",
            "content": "Teknik destek: TechHub müşterisine Monitor kalibrasyon eğitimi sağlanması",
            "metadata": {"type": "görev", "kategori": "Destek", "oncelik": "Orta", "son_tarih": "2026-05-20", "status": "Devam Ediyor", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_004",
            "content": "Vergi raporlaması: Mayıs ayı satış verileri maliye raporuna dahil edilmesi",
            "metadata": {"type": "görev", "kategori": "İdari", "oncelik": "Yüksek", "son_tarih": "2026-06-05", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_005",
            "content": "Sistem bakımı: Veritabanı yedeklemesi ve periyodik güvenlik taraması yapılması",
            "metadata": {"type": "görev", "kategori": "BT", "oncelik": "Orta", "son_tarih": "2026-05-25", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_006",
            "content": "E-posta kampanyası: Tüm müşterilere yeni ürün kataloğu gönderilmesi",
            "metadata": {"type": "görev", "kategori": "Pazarlama", "oncelik": "Düşük", "son_tarih": "2026-05-18", "status": "Tamamlandı", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_007",
            "content": "Müşteri memnuniyeti anketi: Üç ay içinde yapılan tüm satışlar için geri bildirim toplanması",
            "metadata": {"type": "görev", "kategori": "Kalite", "oncelik": "Orta", "son_tarih": "2026-06-10", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_008",
            "content": "Depo düzenleme: Yeni gelen ürünlerin raf konumlarına yerleştirilmesi",
            "metadata": {"type": "görev", "kategori": "Depo", "oncelik": "Orta", "son_tarih": "2026-05-12", "status": "Devam Ediyor", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_009",
            "content": "Bütçe planlaması: Q3 2026 harcama tahmini ve satın alma planı hazırlanması",
            "metadata": {"type": "görev", "kategori": "Mali", "oncelik": "Yüksek", "son_tarih": "2026-05-31", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        },
        {
            "id": "gorev_010",
            "content": "Tedarikçi görüşmesi: HP ve Samsung ile yeni koşullar ve fiyatlandırma müzakeresi",
            "metadata": {"type": "görev", "kategori": "Tedarikçi", "oncelik": "Orta", "son_tarih": "2026-05-22", "status": "Beklemede", "son_guncelleme": datetime.now().isoformat()}
        }
    ]
    
    # Add documents to collection with thread safety
    with db_lock:
        for item in mock_data:
            collection.add(
                ids=[item["id"]],
                documents=[item["content"]],
                metadatas=[item["metadata"]]
            )


def get_context(query: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Retrieve relevant context from ChromaDB using semantic search.
    
    Args:
        query: Natural language search query
        n_results: Number of results to return (default: 5)
    
    Returns:
        Dictionary containing search results and metadata
    
    Raises:
        ValueError: If collection is not initialized
    """
    if collection is None:
        raise ValueError("Database not initialized. Call init_db() first.")
    
    try:
        # Query the collection
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        context_data = {
            "query": query,
            "results_count": len(results["ids"][0]) if results["ids"] else 0,
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "success": True
        }
        
        logger.info(f"Search query '{query}' returned {context_data['results_count']} results")
        return context_data
        
    except Exception as e:
        logger.error(f"Search query failed: {str(e)}")
        return {
            "query": query,
            "results_count": 0,
            "documents": [],
            "metadatas": [],
            "distances": [],
            "success": False,
            "error": str(e)
        }


def get_collection():
    """
    Get the current ChromaDB collection.
    
    Returns:
        ChromaDB collection object
    
    Raises:
        ValueError: If collection is not initialized
    """
    if collection is None:
        raise ValueError("Database not initialized. Call init_db() first.")
    return collection


# ==================== Business Simulation Functions ====================

def simulate_business_activity() -> Dict[str, Any]:
    """
    Main simulation function that orchestrates all business activity updates.
    Runs every 2 minutes via APScheduler.
    
    Returns:
        Dictionary with simulation summary
    """
    try:
        if collection is None:
            logger.warning("Collection not initialized for simulation")
            return {"success": False, "reason": "Collection not initialized"}
        
        with db_lock:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "stock_updated": update_stock_levels(),
                "orders_updated": update_order_status(),
                "tasks_updated": update_tasks(),
                "success": True
            }
            
            # Log simulation summary
            logger.info(
                f"🔄 SIMULATION UPDATE - "
                f"Stock: {summary['stock_updated']['count']} items | "
                f"Orders: {summary['orders_updated']['count']} items | "
                f"Tasks: {summary['tasks_updated']['count']} items"
            )
            
            return summary
            
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return {"success": False, "error": str(e)}


def update_stock_levels() -> Dict[str, Any]:
    """
    Update stock levels in ChromaDB:
    - Reduce random stock by 10-20% (sales simulation)
    - Increase stock by 50 if below threshold (supply simulation)
    
    Returns:
        Dictionary with update count and details
    """
    try:
        # Get all stock items
        stock_results = collection.get(
            where={"type": "stok"},
            include=["metadatas"]
        )
        
        updates = []
        updated_count = 0
        critical_threshold = 10
        
        for stock_id, metadata in zip(stock_results["ids"], stock_results["metadatas"]):
            current_quantity = metadata.get("miktar", 0)
            
            # 40% chance of sales (reduce stock by 10-20%)
            if random.random() < 0.4:
                reduction_percent = random.uniform(0.1, 0.2)
                new_quantity = max(0, int(current_quantity * (1 - reduction_percent)))
                
                if new_quantity != current_quantity:
                    metadata["miktar"] = new_quantity
                    metadata["son_guncelleme"] = datetime.now().isoformat()
                    updates.append((stock_id, metadata))
                    updated_count += 1
                    
                    if new_quantity < current_quantity:
                        logger.info(f"  📉 Stok {stock_id}: {current_quantity} → {new_quantity} (Satış)")
            
            # If below threshold, 35% chance of restocking
            if current_quantity < critical_threshold and random.random() < 0.35:
                new_quantity = current_quantity + 50
                metadata["miktar"] = new_quantity
                metadata["son_guncelleme"] = datetime.now().isoformat()
                updates.append((stock_id, metadata))
                updated_count += 1
                logger.info(f"  📈 Stok {stock_id}: {current_quantity} → {new_quantity} (Tedarik)")
        
        # Apply updates to ChromaDB
        for stock_id, updated_metadata in updates:
            collection.update(
                ids=[stock_id],
                metadatas=[updated_metadata]
            )
        
        return {
            "count": updated_count,
            "details": f"{updated_count} ürün güncellendi"
        }
        
    except Exception as e:
        logger.error(f"Stock update error: {str(e)}")
        return {"count": 0, "error": str(e)}


def update_order_status() -> Dict[str, Any]:
    """
    Update order statuses in ChromaDB:
    - Change 'Hazırlanıyor' → 'Kargoya Verildi' with 50% probability
    
    Returns:
        Dictionary with update count and details
    """
    try:
        # Get all order items
        order_results = collection.get(
            where={"type": "sipariş"},
            include=["metadatas"]
        )
        
        updated_count = 0
        
        for order_id, metadata in zip(order_results["ids"], order_results["metadatas"]):
            current_status = metadata.get("durum", "")
            
            # If preparing, 50% chance to ship
            if current_status == "Hazırlanıyor" and random.random() < 0.5:
                new_status = "Kargoya Verildi"
                metadata["durum"] = new_status
                metadata["son_guncelleme"] = datetime.now().isoformat()
                
                collection.update(
                    ids=[order_id],
                    metadatas=[metadata]
                )
                
                updated_count += 1
                logger.info(f"  📦 Sipariş {order_id}: {current_status} → {new_status}")
        
        return {
            "count": updated_count,
            "details": f"{updated_count} sipariş güncellendi"
        }
        
    except Exception as e:
        logger.error(f"Order update error: {str(e)}")
        return {"count": 0, "error": str(e)}


def update_tasks() -> Dict[str, Any]:
    """
    Update task statuses in ChromaDB:
    - Change random task status to 'Tamamlandı' (30% chance)
    - Add new random tasks to the list (20% chance)
    
    Returns:
        Dictionary with update count and details
    """
    try:
        # Get all task items
        task_results = collection.get(
            where={"type": "görev"},
            include=["metadatas"]
        )
        
        updated_count = 0
        
        # Update existing tasks
        for task_id, metadata in zip(task_results["ids"], task_results["metadatas"]):
            current_status = metadata.get("status", "Beklemede")
            
            # 30% chance to complete task
            if current_status != "Tamamlandı" and random.random() < 0.3:
                metadata["status"] = "Tamamlandı"
                metadata["son_guncelleme"] = datetime.now().isoformat()
                
                collection.update(
                    ids=[task_id],
                    metadatas=[metadata]
                )
                
                updated_count += 1
                logger.info(f"  ✅ Görev {task_id}: → Tamamlandı")
        
        # 20% chance to add new task
        if random.random() < 0.2:
            new_tasks = [
                "Yeni sipariş kontrolü: Sabah gelen tüm siparişler gözden geçirilmeli",
                "Depo düzenleme: Yenilikleri kendi bölümlerine yerleştir",
                "Müşteri takip: Beklemede olan sipariş statüsü güncelle",
                "Stok kontrol: Kritik stok seviyeleri kontrol et",
                "Tedarik planlaması: Eksik malzemeleri satıcıdan talep et"
            ]
            
            new_task = random.choice(new_tasks)
            task_count = len(task_results["ids"])
            new_task_id = f"gorev_{str(task_count + 1).zfill(3)}"
            
            new_task_metadata = {
                "type": "görev",
                "kategori": "Diğer",
                "oncelik": "Orta",
                "son_tarih": "2026-05-20",
                "status": "Beklemede",
                "son_guncelleme": datetime.now().isoformat()
            }
            
            collection.add(
                ids=[new_task_id],
                documents=[new_task],
                metadatas=[new_task_metadata]
            )
            
            updated_count += 1
            logger.info(f"  ➕ Yeni Görev Eklendi: {new_task_id}")
        
        return {
            "count": updated_count,
            "details": f"{updated_count} görev işlendi"
        }
        
    except Exception as e:
        logger.error(f"Task update error: {str(e)}")
        return {"count": 0, "error": str(e)}


def start_simulation_scheduler():
    """
    Initialize and start APScheduler for business simulation.
    Runs simulate_business_activity() every 2 minutes.
    
    Returns:
        Scheduler instance or None if already running
    """
    global simulation_scheduler
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        if simulation_scheduler is not None:
            logger.warning("Simulation scheduler already running")
            return simulation_scheduler
        
        simulation_scheduler = BackgroundScheduler(daemon=True)
        
        # Schedule simulation every 2 minutes
        simulation_scheduler.add_job(
            func=simulate_business_activity,
            trigger=IntervalTrigger(minutes=2),
            id='business_simulation',
            name='Business Activity Simulation',
            replace_existing=True
        )
        
        simulation_scheduler.start()
        logger.info("✨ Business simulation scheduler started (every 2 minutes)")
        
        return simulation_scheduler
        
    except ImportError:
        logger.error("APScheduler not installed. Install with: pip install apscheduler")
        return None
    except Exception as e:
        logger.error(f"Failed to start simulation scheduler: {str(e)}")
        return None


def stop_simulation_scheduler():
    """
    Stop the business simulation scheduler gracefully.
    """
    global simulation_scheduler
    
    if simulation_scheduler is not None:
        try:
            simulation_scheduler.shutdown(wait=True)
            simulation_scheduler = None
            logger.info("Business simulation scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
