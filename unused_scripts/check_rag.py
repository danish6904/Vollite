"""Check RAG requirements and service status"""
import sys

print("=== RAG Requirements Check ===\n")

# Check all required packages
required_packages = {
    "langchain": "langchain",
    "chromadb": "chromadb", 
    "ollama": "ollama",
    "sentence-transformers": "sentence_transformers"
}

print("Required Packages:")
all_installed = True
for name, import_name in required_packages.items():
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'installed')
        print(f"  [OK] {name:<25} {version}")
    except ImportError:
        print(f"  [MISSING] {name}")
        all_installed = False

print("\n=== RAG Service Status ===\n")
try:
    from services.rag_service import ForensicsRAGService, LANGCHAIN_AVAILABLE, CHROMADB_AVAILABLE
    
    print(f"LangChain Available: {LANGCHAIN_AVAILABLE}")
    print(f"ChromaDB Available: {CHROMADB_AVAILABLE}")
    
    rag = ForensicsRAGService()
    print(f"\nRAG Service Status:")
    print(f"  Available: {rag.available}")
    print(f"  Vector Store Path: {rag.vector_store_path}")
    print(f"  Model Name: {rag.model_name}")
    print(f"  Embedding Model: {rag.embedding_model}")
    
    if not rag.available:
        print("\n[WARNING] RAG Service is not fully available.")
        print("This may be due to:")
        print("  - Missing Ollama installation (download from https://ollama.ai)")
        print("  - Model not pulled (run: ollama pull llama2)")
        
except Exception as e:
    print(f"[ERROR] Could not initialize RAG service: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Summary ===")
if all_installed:
    print("[OK] All RAG requirements are installed!")
    print("\nNext Steps:")
    print("1. Install Ollama from https://ollama.ai")
    print("2. Run: ollama pull llama2")
    print("3. Start Ollama service")
    print("4. Test RAG with: python verify_rag.py")
else:
    print("[WARNING] Some RAG requirements are missing.")
    print("Run: pip install -r requirements-rag.txt")
