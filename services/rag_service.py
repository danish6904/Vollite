"""
RAG (Retrieval-Augmented Generation) Service for Memory Forensics
Provides context-aware analysis using vector embeddings and LLM
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    # Newer LangChain package layout
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_community.llms import Ollama
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    try:
        # Fallback to older LangChain imports
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import Chroma
        from langchain.llms import Ollama
        LANGCHAIN_AVAILABLE = True
    except ImportError as e2:
        LANGCHAIN_AVAILABLE = False
        print(f"Warning: LangChain not installed correctly. RAG features will be disabled.")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not installed. Vector storage will be disabled.")


class ForensicsRAGService:
    """
    RAG service specialized for memory forensics analysis
    """
    
    def __init__(self, 
                 vector_store_path: str = "data/vector_store",
                 model_name: Optional[str] = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG service
        
        Args:
            vector_store_path: Path to store vector embeddings
            model_name: LLM model name (Ollama model)
            embedding_model: Embedding model name
        """
        self.logger = logging.getLogger(__name__)
        self.vector_store_path = vector_store_path
        self.model_name = model_name or os.getenv("RAG_MODEL", "tinyllama")
        self.embedding_model = embedding_model
        
        # Check if dependencies are available
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available. RAG features disabled.")
            self.available = False
            return
        
        self.available = True
        
        # Initialize embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'}
            )
            self.logger.info(f"Initialized embeddings with {embedding_model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings: {e}")
            self.available = False
            return
        
        # Initialize vector store
        self._init_vector_store()
        
        # Initialize LLM
        self._init_llm()
        
        # Initialize knowledge base
        self._init_knowledge_base()
    
    def _init_vector_store(self):
        """Initialize or load vector store"""
        try:
            os.makedirs(self.vector_store_path, exist_ok=True)
            
            if CHROMADB_AVAILABLE:
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
                self.logger.info("Vector store initialized successfully")
            else:
                self.logger.warning("ChromaDB not available")
                self.vector_store = None
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            self.vector_store = None
    
    def _init_llm(self):
        """Initialize LLM (Ollama)"""
        try:
            self.llm = Ollama(
                model=self.model_name,
                temperature=0.3  # Lower temperature for more focused responses
            )
            self.logger.info(f"Initialized LLM: {self.model_name}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _init_knowledge_base(self):
        """Initialize forensics knowledge base"""
        self.knowledge_base = {
            'malicious_processes': [
                'mimikatz.exe', 'psexec.exe', 'netcat.exe', 'ncat.exe',
                'cmd.exe (from suspicious parent)', 'powershell.exe (suspicious args)'
            ],
            'suspicious_dll_patterns': [
                'unknown_origin', 'unsigned', 'hidden', 'packed'
            ],
            'attack_patterns': {
                'credential_dumping': ['lsass.exe access', 'sekurlsa', 'mimikatz'],
                'lateral_movement': ['psexec', 'wmi', 'remote_exec'],
                'persistence': ['registry_run_keys', 'scheduled_tasks', 'services'],
                'data_exfiltration': ['unusual_network', 'compression', 'encryption']
            }
        }
    
    def index_analysis_result(self, analysis_data: Dict[str, Any], analysis_id: str):
        """
        Index an analysis result for future retrieval
        
        Args:
            analysis_data: Analysis result dictionary
            analysis_id: Unique identifier for this analysis
        """
        if not self.available or not self.vector_store:
            self.logger.warning("RAG not available for indexing")
            return False
        
        try:
            # Create document text from analysis
            doc_text = self._create_document_from_analysis(analysis_data)
            
            # Create metadata
            metadata = {
                'analysis_id': analysis_id,
                'timestamp': datetime.now().isoformat(),
                'risk_score': analysis_data.get('risk_score', 0),
                'os_info': analysis_data.get('system_info', {}).get('os', 'unknown')
            }
            
            # Add to vector store
            self.vector_store.add_texts(
                texts=[doc_text],
                metadatas=[metadata],
                ids=[analysis_id]
            )
            
            # Persist changes
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
            
            self.logger.info(f"Indexed analysis {analysis_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to index analysis: {e}")
            return False
    
    def _create_document_from_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Convert analysis data to searchable document"""
        parts = []
        
        # Summary
        if 'summary' in analysis_data:
            parts.append(f"Summary: {analysis_data['summary']}")
        
        # Key findings
        if 'key_findings' in analysis_data:
            parts.append("Findings: " + ", ".join(analysis_data['key_findings']))
        
        # Alerts
        if 'alerts' in analysis_data:
            alert_texts = [
                f"{alert.get('title', '')}: {alert.get('description', '')}"
                for alert in analysis_data['alerts']
            ]
            parts.append("Alerts: " + "; ".join(alert_texts))
        
        # Process information
        if 'process_tree' in analysis_data:
            processes = analysis_data['process_tree'].get('processes', [])
            process_names = [p.get('name', '') for p in processes]
            parts.append("Processes: " + ", ".join(process_names[:20]))  # Limit to 20
        
        return "\n".join(parts)
    
    def query_similar_cases(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar historical cases
        
        Args:
            query: Query text describing the case
            k: Number of similar cases to return
        
        Returns:
            List of similar cases with metadata
        """
        if not self.available or not self.vector_store:
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            similar_cases = []
            for doc, score in results:
                similar_cases.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': float(score)
                })
            
            return similar_cases
        
        except Exception as e:
            self.logger.error(f"Failed to query similar cases: {e}")
            return []
    
    def analyze_with_context(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance analysis with RAG-based context
        
        Args:
            analysis_data: Current analysis data
        
        Returns:
            Enhanced analysis with AI insights
        """
        if not self.available or not self.llm:
            return analysis_data
        
        try:
            # Create query from current analysis
            query = self._create_query_from_analysis(analysis_data)
            
            # Find similar cases
            similar_cases = self.query_similar_cases(query, k=3)
            
            # Create prompt with context
            prompt = self._create_analysis_prompt(analysis_data, similar_cases)
            
            # Get LLM response
            ai_insights = self.llm.invoke(prompt)
            
            # Clean response of prompt artifacts
            ai_insights = self._clean_llm_response(ai_insights)
            
            # Add to analysis
            analysis_data['ai_insights'] = {
                'summary': ai_insights,
                'similar_cases_found': len(similar_cases),
                'context_used': True
            }
            
            return analysis_data
        
        except Exception as e:
            self.logger.error(f"Failed to analyze with context: {e}")
            return analysis_data
    
    def _clean_llm_response(self, text: str) -> str:
        """Clean LLM response of prompt artifacts and echoed instructions"""
        if not text:
            return ""
            
        clean_lines = []
        # specific phrases from the prompt to strip
        skip_phrases = [
            "based strictly", "format your", "instructions:", "start specificially", 
            "do not include", "example start", "critical:", "identify the",
            "provide a specific", "strictly align", "format exactly",
            "strictly based on", "to assess this data", "i would follow",
            "determine the threat", "write a short assessment"
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            if not line_stripped:
                continue
            
            # Skip instruction lines
            if any(phrase in line_lower for phrase in skip_phrases):
                continue
                
            # Skip echoed input data
            if line_stripped.startswith("Risk Score:") or line_stripped.startswith("Summary:") or line_stripped.startswith("Findings:"):
                continue
                
            clean_lines.append(line_stripped)
            
        return "\n".join(clean_lines)

    def _create_query_from_analysis(self, analysis_data: Dict[str, Any]) -> str:
        return " ".join([analysis_data.get('summary', '')])
    
    def _create_analysis_prompt(self, 
                                analysis_data: Dict[str, Any],
                                similar_cases: List[Dict[str, Any]]) -> str:
        """Create prompt for LLM analysis"""
        # Determine strict threat level for the prompt to force the model
        score = analysis_data.get('risk_score', 0)
        forced_level = "Low"
        if score >= 70: forced_level = "High"
        elif score >= 40: forced_level = "Medium"
        
        prompt = f"""
You are a cybersecurity analyst.
Analysis Data:
- Risk Score: {score} ({forced_level} Risk)
- Findings: {', '.join(analysis_data.get('key_findings', [])[:5])}

Write a short executive summary.
Start with "Threat Level: {forced_level}".
Then explain the findings in 2 sentences.
Actionable recommendation:

### RESPONSE
"""
        return prompt
    
    def generate_report_summary(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate AI-powered report summary
        
        Args:
            analysis_data: Analysis results
        
        Returns:
            Generated summary text
        """
        if not self.available or not self.llm:
            return "AI summary generation not available."
        
        try:
            prompt = f"""
Generate a professional forensics report summary for the following analysis:

Risk Score: {analysis_data.get('risk_score', 0)}/100
Findings: {', '.join(analysis_data.get('key_findings', []))}
Alerts: {len(analysis_data.get('alerts', []))} alerts detected

Write 2-3 paragraphs suitable for an executive summary.
"""
            
            summary = self.llm.invoke(prompt)
            return summary
        
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return "Summary generation failed."
    
    def explain_finding(self, finding: str) -> str:
        """
        Get detailed explanation of a specific finding
        
        Args:
            finding: The finding to explain
        
        Returns:
            Detailed explanation
        """
        if not self.available or not self.llm:
            return "Explanation not available."
        
        try:
            # Check knowledge base first
            explanation = self._check_knowledge_base(finding)
            
            if explanation:
                return explanation
            
            # Use LLM for unknown findings
            prompt = f"""
Explain this memory forensics finding in simple terms:
"{finding}"

Provide:
1. What it means (1-2 sentences)
2. Why it matters (1-2 sentences)
3. Typical next steps (2-3 bullet points)
"""
            
            explanation = self.llm.invoke(prompt)
            return explanation
        
        except Exception as e:
            self.logger.error(f"Failed to explain finding: {e}")
            return "Explanation failed."
    
    def _check_knowledge_base(self, finding: str) -> Optional[str]:
        """Check if finding matches known patterns"""
        finding_lower = finding.lower()
        
        for attack_type, indicators in self.knowledge_base['attack_patterns'].items():
            if any(indicator in finding_lower for indicator in indicators):
                return f"This finding is related to {attack_type.replace('_', ' ')}. " \
                       f"Common indicators: {', '.join(indicators)}"
        
        return None
    
    def get_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """
        Get AI-powered recommendations based on analysis
        
        Args:
            analysis_data: Analysis results
        
        Returns:
            List of recommendations
        """
        if not self.available:
            return self._get_default_recommendations(analysis_data)
        
        try:
            risk_score = analysis_data.get('risk_score', 0)
            
            prompt = f"""
Given a memory forensics analysis with risk score {risk_score}/100, provide 5 specific,
actionable recommendations for the incident response team.

Focus on immediate actions and investigation priorities.
Format as numbered list.
"""
            
            response = self.llm.invoke(prompt)
            
            # Parse recommendations
            recommendations = [
                line.strip() 
                for line in response.split('\n') 
                if line.strip() and any(c.isdigit() for c in line[:3])
            ]
            
            return recommendations[:5]
        
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return self._get_default_recommendations(analysis_data)
    
    def _get_default_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Fallback recommendations based on risk score"""
        risk_score = analysis_data.get('risk_score', 0)
        
        if risk_score >= 70:
            return [
                "Immediately isolate the affected system from the network",
                "Preserve all evidence including memory dumps and disk images",
                "Initiate incident response procedures",
                "Conduct thorough network traffic analysis",
                "Review and reset all credentials accessed from this system"
            ]
        elif risk_score >= 40:
            return [
                "Monitor the system closely for suspicious activity",
                "Review recent user activity and login history",
                "Check for lateral movement indicators",
                "Update security tools and run full scan",
                "Document all findings for further analysis"
            ]
        else:
            return [
                "Continue routine monitoring",
                "Update malware definitions",
                "Review system logs periodically",
                "Maintain current security posture",
                "Schedule regular security assessments"
            ]


# Singleton instance
_rag_service_instance = None

def get_rag_service() -> ForensicsRAGService:
    """Get or create RAG service instance"""
    return ForensicsRAGService()
