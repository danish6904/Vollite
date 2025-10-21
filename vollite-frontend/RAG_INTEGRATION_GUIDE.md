# RAG Pipeline Integration Guide

## Overview

This document explains how to set up and use the RAG (Retrieval-Augmented Generation) pipeline in volLite for AI-powered memory forensics analysis.

## What is RAG?

RAG combines:
- **Retrieval**: Finding relevant historical data and knowledge
- **Augmented**: Enhancing analysis with context
- **Generation**: Creating AI-powered insights and explanations

## Features

### 1. **Context-Aware Analysis**
- Searches historical analyses for similar patterns
- Provides context from previous incidents
- Learns from your analysis history

### 2. **AI-Powered Explanations**
- Explains complex findings in simple terms
- References security knowledge bases
- Suggests remediation steps

### 3. **Intelligent Recommendations**
- Risk-based action items
- Prioritized investigation paths
- Industry best practices

### 4. **Report Generation**
- AI-generated executive summaries
- Context-aware narratives
- Professional forensics reports

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Activate your virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install RAG dependencies
pip install -r requirements-rag.txt
```

### Step 2: Install Ollama (Local LLM)

**Option A: Ollama (Recommended - Free & Local)**

1. Download Ollama from https://ollama.ai
2. Install Ollama
3. Pull a model:
```bash
ollama pull llama2
# or
ollama pull mistral
```

**Option B: OpenAI API (Cloud)**

1. Get API key from https://platform.openai.com
2. Set environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

3. Update `rag_service.py` to use OpenAI instead of Ollama

### Step 3: Initialize Vector Store

The vector store will be automatically created on first use in:
```
data/vector_store/
```

### Step 4: Test the Setup

```python
from services.rag_service import get_rag_service

rag = get_rag_service()
print(f"RAG Available: {rag.available}")
```

## API Endpoints

### 1. Get RAG Status
```http
GET /api/rag/status
```

Response:
```json
{
  "available": true,
  "model": "llama2",
  "embedding_model": "all-MiniLM-L6-v2",
  "vector_store_initialized": true
}
```

### 2. Explain Finding
```http
POST /api/rag/explain
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "finding": "Suspicious lsass.exe memory access detected"
}
```

### 3. Get Recommendations
```http
GET /api/rag/recommendations/<analysis_id>
Authorization: Bearer <jwt_token>
```

### 4. Find Similar Cases
```http
POST /api/rag/similar-cases
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "query": "ransomware encryption",
  "limit": 5
}
```

### 5. Enhance Analysis
```http
POST /api/rag/enhance-analysis/<analysis_id>
Authorization: Bearer <jwt_token>
```

### 6. Generate Summary
```http
POST /api/rag/generate-summary/<analysis_id>
Authorization: Bearer <jwt_token>
```

## Usage Examples

### Python Usage

```python
from services.rag_service import get_rag_service

# Get RAG service
rag = get_rag_service()

# Index an analysis for future retrieval
analysis_data = {
    'summary': 'Malware detected in memory',
    'risk_score': 85,
    'key_findings': ['Suspicious process', 'Network connection'],
    'alerts': [...]
}
rag.index_analysis_result(analysis_data, 'analysis_123')

# Query similar cases
similar = rag.query_similar_cases('credential dumping attack', k=5)

# Get AI insights
enhanced = rag.analyze_with_context(analysis_data)

# Explain a finding
explanation = rag.explain_finding('mimikatz process detected')

# Get recommendations
recommendations = rag.get_recommendations(analysis_data)
```

### JavaScript/Frontend Usage

```javascript
// Get RAG status
fetch('/api/rag/status')
  .then(res => res.json())
  .then(data => console.log('RAG Available:', data.available));

// Explain a finding
fetch('/api/rag/explain', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    finding: 'Suspicious DLL injection detected'
  })
})
.then(res => res.json())
.then(data => console.log(data.explanation));

// Get recommendations
fetch(`/api/rag/recommendations/${analysisId}`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => console.log(data.recommendations));
```

## Architecture

```
┌─────────────────────────────────────────────┐
│          volLite Application                │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│        RAG Service (rag_service.py)         │
├─────────────────────────────────────────────┤
│  - ForensicsRAGService                      │
│  - Knowledge Base Management                │
│  - Query Processing                         │
└────┬─────────────────────────┬──────────────┘
     │                         │
┌────▼─────────────┐  ┌────────▼──────────────┐
│  Vector Store    │  │   LLM (Ollama/OpenAI) │
│  (ChromaDB)      │  │   - llama2            │
│                  │  │   - mistral           │
│  - Embeddings    │  │   - gpt-3.5-turbo     │
│  - Similarity    │  │                       │
│    Search        │  │                       │
└──────────────────┘  └───────────────────────┘
```

## Performance Considerations

### Memory Requirements
- **Embeddings Model**: ~400MB RAM
- **Vector Store**: Scales with data (~1MB per 1000 analyses)
- **LLM (Ollama)**: 4-8GB RAM depending on model

### Speed
- **Embedding**: ~100ms per document
- **Similarity Search**: ~10-50ms
- **LLM Generation**: 1-5 seconds

### Optimization Tips
1. Use smaller embedding models for faster processing
2. Limit vector store size (keep last N analyses)
3. Use quantized LLM models
4. Cache frequent queries

## Troubleshooting

### Issue: "RAG service not available"
**Solution**: Install dependencies
```bash
pip install -r requirements-rag.txt
```

### Issue: "Ollama connection failed"
**Solution**: 
1. Check if Ollama is running: `ollama serve`
2. Verify model is downloaded: `ollama list`
3. Pull model if needed: `ollama pull llama2`

### Issue: "Out of memory"
**Solution**:
1. Use smaller model (e.g., `tinyllama` instead of `llama2`)
2. Reduce batch size in embeddings
3. Increase system RAM or use cloud GPU

### Issue: "Slow response times"
**Solution**:
1. Use faster embedding model (e.g., `all-MiniLM-L6-v2`)
2. Reduce number of similar cases retrieved
3. Enable caching
4. Use GPU acceleration if available

## Security Notes

1. **Data Privacy**: All data stays local when using Ollama
2. **API Keys**: Never commit OpenAI keys to repository
3. **Access Control**: RAG endpoints require JWT authentication
4. **Data Sanitization**: User inputs are validated before processing

## Future Enhancements

- [ ] Fine-tune models on forensics data
- [ ] Add support for more LLM providers (Claude, Gemini)
- [ ] Implement semantic caching
- [ ] Add graph-based knowledge representation
- [ ] Real-time streaming responses
- [ ] Multi-language support

## Resources

- **LangChain Docs**: https://python.langchain.com/
- **ChromaDB**: https://docs.trychroma.com/
- **Ollama**: https://ollama.ai/
- **Sentence Transformers**: https://www.sbert.net/

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review example code in `services/rag_service.py`
