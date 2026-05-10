"""
Quick setup test for the RAG business assistant project.
Run this to verify all components are working correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("  ✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"  ❌ FastAPI import failed: {e}")
        return False
    
    try:
        import streamlit
        print("  ✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"  ❌ Streamlit import failed: {e}")
        return False
    
    try:
        import chromadb
        print("  ✅ ChromaDB imported successfully")
    except ImportError as e:
        print(f"  ❌ ChromaDB import failed: {e}")
        return False
    
    try:
        import google.generativeai
        print("  ✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"  ❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        print("  ✅ APScheduler imported successfully")
    except ImportError as e:
        print(f"  ❌ APScheduler import failed: {e}")
        return False
    
    try:
        import pandas
        print("  ✅ Pandas imported successfully")
    except ImportError as e:
        print(f"  ❌ Pandas import failed: {e}")
        return False
    
    return True


def test_env_file():
    """Test that .env file exists and has required variables."""
    print("\n🔍 Testing .env file...")
    
    env_path = project_root / ".env"
    if not env_path.exists():
        print(f"  ❌ .env file not found at {env_path}")
        return False
    
    print("  ✅ .env file found")
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        # Check for required environment variables
        required_vars = ["GEMINI_API_KEY", "EMAIL_SENDER", "EMAIL_PASSWORD"]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith("your_"):
                print(f"  ⚠️  {var} not configured properly (still has placeholder value)")
            else:
                print(f"  ✅ {var} is configured")
        
        return True
    except Exception as e:
        print(f"  ❌ Error reading .env file: {e}")
        return False


def test_project_structure():
    """Test that all required files exist."""
    print("\n🔍 Testing project structure...")
    
    required_files = [
        "main.py",
        "chatbot_ui.py",
        "automation.py",
        "shared_utils.py",
        "requirements.txt",
        ".env",
        "README.md",
    ]
    
    required_dirs = [
        "routers",
    ]
    
    all_exist = True
    
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✅ {file} exists")
        else:
            print(f"  ❌ {file} not found")
            all_exist = False
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/ directory exists")
        else:
            print(f"  ❌ {dir_name}/ directory not found")
            all_exist = False
    
    return all_exist


def test_database_init():
    """Test ChromaDB initialization."""
    print("\n🔍 Testing database initialization...")
    
    try:
        from shared_utils import init_db, get_context
        
        init_db()
        print("  ✅ Database initialized successfully")
        
        # Test context retrieval
        result = get_context("test query", n_results=3)
        
        if result["success"]:
            print(f"  ✅ Context retrieval working ({result['results_count']} results)")
        else:
            print(f"  ❌ Context retrieval failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 RAG Business Assistant - Setup Verification")
    print("=" * 60)
    
    results = {}
    
    # Run all tests
    results["imports"] = test_imports()
    results["env_file"] = test_env_file()
    results["project_structure"] = test_project_structure()
    results["database"] = test_database_init()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All systems go! Ready for development.")
        print("\n🚀 Next steps:")
        print("  1. Run Streamlit: streamlit run chatbot_ui.py")
        print("  2. Or run FastAPI: python main.py")
        print("  3. Check README.md for detailed instructions")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
