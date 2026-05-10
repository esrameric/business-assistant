"""
Configuration management for the RAG business assistant.
Centralized settings for all modules.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Application
    APP_NAME = "RAG Business Assistant"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_WORKERS = int(os.getenv("API_WORKERS", 4))
    
    # Streamlit Settings
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
    STREAMLIT_MAX_UPLOAD_SIZE = 200  # MB
    
    # ChromaDB Settings
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_data")
    CHROMA_COLLECTION_NAME = "isletme_verileri"
    CHROMA_BATCH_SIZE = 100
    
    # Gemini API Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-pro"
    GEMINI_TEMPERATURE = 0.7
    GEMINI_MAX_TOKENS = 1024
    
    # Email Settings
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_SMTP_SERVER = "smtp.gmail.com"
    EMAIL_SMTP_PORT = 465
    EMAIL_USE_TLS = True
    EMAIL_REPORT_TIME = "08:00"  # HH:MM format
    
    # Search Settings
    SEARCH_N_RESULTS = 5
    SEARCH_MIN_DISTANCE = 0.5  # Minimum cosine similarity
    
    # Chat Settings
    CHAT_MAX_HISTORY = 50
    CHAT_SESSION_TIMEOUT = 3600  # 1 hour in seconds
    
    # Logging Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = "./logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS Settings
    CORS_ORIGINS = ["*"]
    CORS_CREDENTIALS = True
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    # Automation/Scheduler Settings
    SCHEDULER_TIMEZONE = "UTC"
    SCHEDULER_MISFIRE_GRACE_TIME = 60  # seconds
    
    @staticmethod
    def validate_credentials() -> tuple[bool, Optional[str]]:
        """
        Validate that required credentials are configured.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY.startswith("your_"):
            errors.append("GEMINI_API_KEY not configured")
        
        if not Config.EMAIL_SENDER or Config.EMAIL_SENDER.startswith("your_"):
            errors.append("EMAIL_SENDER not configured")
        
        if not Config.EMAIL_PASSWORD or Config.EMAIL_PASSWORD.startswith("your_"):
            errors.append("EMAIL_PASSWORD not configured")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, None
    
    @staticmethod
    def get_database_url() -> str:
        """Get the database connection string."""
        return f"chroma+persistent://{Config.CHROMA_DB_PATH}"
    
    @staticmethod
    def get_log_file_path() -> str:
        """Get the main log file path."""
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        return os.path.join(Config.LOG_DIR, "app.log")
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = {}
        for key, value in cls.__dict__.items():
            # Skip private/magic attributes and sensitive data
            if not key.startswith("_") and not callable(value):
                if "API_KEY" in key or "PASSWORD" in key:
                    config_dict[key] = "***REDACTED***"
                else:
                    config_dict[key] = value
        return config_dict


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    API_WORKERS = int(os.getenv("API_WORKERS", 8))


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    CHROMA_DB_PATH = "./test_chroma_data"
    LOG_LEVEL = "DEBUG"


def get_config() -> Config:
    """
    Get configuration based on environment.
    
    Returns:
        Appropriate Config class instance
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Create default config instance
config = get_config()
