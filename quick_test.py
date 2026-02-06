"""Quick RAG test"""
print("Step 1: Import langchain_text_splitters...")
from langchain_text_splitters import RecursiveCharacterTextSplitter
print("  OK")

print("Step 2: Import HuggingFaceEmbeddings...")
from langchain_community.embeddings import HuggingFaceEmbeddings
print("  OK")

print("Step 3: Import Chroma...")
from langchain_community.vectorstores import Chroma
print("  OK")

print("Step 4: Import Ollama...")
from langchain_community.llms import Ollama
print("  OK")

print("\nAll imports successful!")
print("LANGCHAIN_AVAILABLE = True")
