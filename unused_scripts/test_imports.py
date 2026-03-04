"""Test LangChain imports"""

print("Testing LangChain imports...")

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("✓ langchain_text_splitters.RecursiveCharacterTextSplitter")
except Exception as e:
    print(f"✗ langchain_text_splitters.RecursiveCharacterTextSplitter: {e}")

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("✓ langchain_community.embeddings.HuggingFaceEmbeddings")
except Exception as e:
    print(f"✗ langchain_community.embeddings.HuggingFaceEmbeddings: {e}")

try:
    from langchain_community.vectorstores import Chroma
    print("✓ langchain_community.vectorstores.Chroma")
except Exception as e:
    print(f"✗ langchain_community.vectorstores.Chroma: {e}")

try:
    from langchain_community.llms import Ollama
    print("✓ langchain_community.llms.Ollama")
except Exception as e:
    print(f"✗ langchain_community.llms.Ollama: {e}")

try:
    from langchain.chains import RetrievalQA
    print("✓ langchain.chains.RetrievalQA")
except Exception as e:
    print(f"✗ langchain.chains.RetrievalQA: {e}")

try:
    from langchain.prompts import PromptTemplate
    print("✓ langchain.prompts.PromptTemplate")
except Exception as e:
    print(f"✗ langchain.prompts.PromptTemplate: {e}")
