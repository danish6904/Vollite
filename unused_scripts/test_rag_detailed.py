"""Test RAG initialization with detailed logging"""
import sys
import os

print("=" * 60)
print("RAG Service Initialization Test")
print("=" * 60)

print("\n[1/6] Setting environment...")
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Allow online
os.environ['HF_HUB_OFFLINE'] = '0'

print("[2/6] Testing basic imports...")
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.llms import Ollama
    print("  ✓ LangChain imports OK")
except Exception as e:
    print(f"  ✗ LangChain imports failed: {e}")
    sys.exit(1)

print("[3/6] Testing HuggingFaceEmbeddings import...")
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    print("  ✓ HuggingFaceEmbeddings import OK")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print("[4/6] Creating embeddings object (may take 30-60 seconds first time)...")
print("  Please wait, loading model from cache...")
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("  ✓ Embeddings object created!")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[5/6] Testing embedding generation...")
try:
    test_embedding = embeddings.embed_query("test")
    print(f"  ✓ Generated {len(test_embedding)}-dimensional embedding")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print("[6/6] Testing full RAG service...")
try:
    from services.rag_service import get_rag_service
    rag = get_rag_service()
    print(f"  ✓ RAG Service initialized")
    print(f"     Available: {rag.available}")
    print(f"     Model: {rag.model_name}")
    print(f"     Embedding: {rag.embedding_model}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS! RAG service is fully operational!")
print("=" * 60)
