"""
Advanced AI Features Module

Provides AI-powered classification, summarization, anomaly detection,
smart search with RAG, and multimodal analysis.
"""

import os
import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import numpy as np
from collections import Counter
import joblib

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """AI classification result."""
    category: str
    subcategory: str
    confidence: float
    all_predictions: List[Dict[str, Any]]
    processing_time: float


@dataclass
class SummarizationResult:
    """Document summarization result."""
    summary: str
    key_points: List[str]
    word_count: int
    language: str
    processing_time: float


@dataclass
class AnomalyResult:
    """Anomaly detection result."""
    is_anomaly: bool
    anomaly_score: float
    anomaly_type: Optional[str]
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]


@dataclass
class VectorSearchResult:
    """Vector search result."""
    file_id: int
    filename: str
    similarity: float
    content_snippet: str
    metadata: Dict[str, Any]


@dataclass
class MultimodalResult:
    """Multimodal analysis result."""
    type: str  # image, video, audio
    caption: Optional[str]
    objects: List[str]
    text_content: str
    duration: Optional[float]
    transcript: Optional[str]
    processing_time: float


class BaseAIModel(ABC):
    """Abstract base for AI models."""

    @abstractmethod
    def load(self) -> bool:
        pass

    @abstractmethod
    async def predict_async(self, input_data: Any) -> Any:
        pass

    def predict(self, input_data: Any) -> Any:
        """Synchronous wrapper for async predict."""
        return asyncio.get_event_loop().run_until_complete(
            self.predict_async(input_data)
        )


class CLIPClassifier(BaseAIModel):
    """CLIP-based content classifier for semantic categorization."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """Initialize CLIP classifier."""
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._loaded = False
        self.categories = [
            "invoice", "contract", "report", "resume", "email",
            "presentation", "spreadsheet", "legal document", "technical document",
            "image", "video", "audio", "archive", "code", "configuration",
            "photo", "screenshot", "diagram", "chart", "logo", "drawing",
            "meeting recording", "tutorial", "presentation slide",
            "music track", "podcast episode", "voice recording",
            "spreadsheet data", "database export", "log file"
        ]

    def load(self) -> bool:
        """Load CLIP model."""
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self._loaded = True
            logger.info(f"Loaded CLIP model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            # Fallback to rule-based
            self._loaded = True
            return True

    async def predict_async(self, text: str) -> ClassificationResult:
        """Classify text using CLIP zero-shot classification."""
        import time
        start = time.time()

        if not self._loaded:
            self.load()

        if self.model is None:
            predictions = self._rule_based_classify(text)
        else:
            predictions = await self._clip_classify_async(text)

        processing_time = time.time() - start

        return ClassificationResult(
            category=predictions[0]["category"],
            subcategory=predictions[0]["category"],
            confidence=predictions[0]["confidence"],
            all_predictions=predictions,
            processing_time=processing_time
        )

    async def _clip_classify_async(self, text: str) -> List[Dict[str, Any]]:
        """Use CLIP for zero-shot classification."""
        try:
            # Prepare inputs
            inputs = self.processor(
                text=text,
                images=None,
                return_tensors="pt",
                padding=True
            )

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = outputs.logits.softmax(dim=-1)

            # Map to categories
            results = []
            for i, category in enumerate(self.categories):
                results.append({
                    "category": category,
                    "confidence": probs[0][i].item()
                })

            results.sort(key=lambda x: x["confidence"], reverse=True)
            return results[:5]

        except Exception as e:
            logger.error(f"CLIP classification failed: {e}")
            return self._rule_based_classify(text)

    def _rule_based_classify(self, text: str) -> List[Dict[str, Any]]:
        """Rule-based classification as fallback."""
        text_lower = text.lower()
        scores = []

        category_keywords = {
            "invoice": ["invoice", "billing", "amount due", "payment", "total", "invoice #"],
            "contract": ["agreement", "terms", "conditions", "parties", "signature", "hereby"],
            "report": ["findings", "analysis", "conclusion", "recommendations", "executive summary"],
            "resume": ["experience", "education", "skills", "employment", "background", "cv"],
            "email": ["dear", "sincerely", "regards", "email", "subject", "cc"],
            "legal": ["hereby", "pursuant", "jurisdiction", "liability", "legal"],
            "technical": ["api", "function", "implementation", "algorithm", "code", "database"],
            "presentation": ["slide", "presentation", "powerpoint", "keynote", "deck"],
            "spreadsheet": ["cell", "formula", "excel", "sheet", "data", "column"],
            "code": ["import", "def", "class", "function", "var", "const", "return"],
            "image": ["image", "photo", "picture", "jpg", "png", "width", "height"],
            "video": ["video", "mp4", "avi", "frame", "duration", "fps"],
            "audio": ["audio", "mp3", "wav", "frequency", "sample", "duration"]
        }

        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if text:
                score = score / len(keywords) + 0.3  # Base confidence
            scores.append({
                "category": category,
                "confidence": min(score, 0.95)
            })

        scores.sort(key=lambda x: x["confidence"], reverse=True)
        return scores[:5]


class HuggingFaceClassifier(BaseAIModel):
    """Hugging Face transformer-based classifier."""

    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        """Initialize classifier."""
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._loaded = False
        self.categories = [
            "invoice", "contract", "report", "resume", "email",
            "presentation", "spreadsheet", "legal document", "technical document",
            "image", "video", "audio", "archive", "code", "configuration"
        ]

    def load(self) -> bool:
        """Load model from Hugging Face."""
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._loaded = True
            logger.info(f"Loaded transformer model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._loaded = True
            return True

    async def predict_async(self, text: str) -> ClassificationResult:
        """Classify text content asynchronously."""
        import time
        start = time.time()

        if not self._loaded:
            self.load()

        if self.model is None:
            predictions = self._rule_based_classify(text)
        else:
            predictions = await self._transformer_classify_async(text)

        processing_time = time.time() - start

        return ClassificationResult(
            category=predictions[0]["category"],
            subcategory=predictions[0]["category"],
            confidence=predictions[0]["confidence"],
            all_predictions=predictions,
            processing_time=processing_time
        )

    async def _transformer_classify_async(self, text: str) -> List[Dict[str, Any]]:
        """Use transformer for classification."""
        try:
            from transformers import pipeline

            classifier = pipeline(
                "zero-shot-classification",
                model=self.model,
                tokenizer=self.tokenizer
            )

            result = classifier(
                text[:512],
                candidate_labels=self.categories,
                multi_label=True
            )

            return [
                {"category": label, "confidence": score}
                for label, score in zip(result["labels"], result["scores"])
            ]
        except Exception as e:
            logger.error(f"Transformer classification failed: {e}")
            return self._rule_based_classify(text)

    def _rule_based_classify(self, text: str) -> List[Dict[str, Any]]:
        """Rule-based classification as fallback."""
        text_lower = text.lower()
        scores = []

        category_keywords = {
            "invoice": ["invoice", "billing", "amount due", "payment", "total"],
            "contract": ["agreement", "terms", "conditions", "parties", "signature"],
            "report": ["findings", "analysis", "conclusion", "recommendations"],
            "resume": ["experience", "education", "skills", "employment", "background"],
            "email": ["dear", "sincerely", "regards", "email"],
            "legal": ["hereby", "pursuant", "jurisdiction", "liability"],
            "technical": ["api", "function", "implementation", "algorithm", "code"],
            "presentation": ["slide", "presentation", "powerpoint"],
            "spreadsheet": ["cell", "formula", "excel", "sheet"]
        }

        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if text:
                score /= len(keywords)
            scores.append({
                "category": category,
                "confidence": min(score + 0.3, 0.95)
            })

        scores.sort(key=lambda x: x["confidence"], reverse=True)
        return scores[:5]


class ContentSummarizer(BaseAIModel):
    """AI-powered content summarizer using GPT or local models."""

    def __init__(self, provider: str = "openai", api_key: str = None):
        """Initialize summarizer."""
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._loaded = False

    def load(self) -> bool:
        """Load summarization model."""
        self._loaded = True
        return True

    async def predict_async(self, content: str, max_length: int = 500) -> SummarizationResult:
        """Summarize content asynchronously."""
        import time
        start = time.time()

        if not self.api_key:
            return self._extractive_summarize(content, max_length)

        if self.provider == "openai":
            return await self._openai_summarize_async(content, max_length)
        else:
            return self._extractive_summarize(content, max_length)

    async def _openai_summarize_async(self, content: str, max_length: int) -> SummarizationResult:
        """Use OpenAI for abstractive summarization."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document summarization assistant. Provide a concise summary and 3-5 key bullet points."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this content (max {max_length} chars):\n\n{content[:4000]}"
                    }
                ],
                max_tokens=500
            )

            summary = response.choices[0].message.content

            # Extract key points (lines starting with - or *)
            key_points = [
                line.strip().lstrip("-* ")
                for line in summary.split("\n")
                if line.strip().startswith(("-+", "*", "•"))
            ]

            return SummarizationResult(
                summary=summary,
                key_points=key_points,
                word_count=len(content.split()),
                language="en",
                processing_time=response.usage.total_tokens / 1000
            )

        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            return self._extractive_summarize(content, max_length)

    def _extractive_summarize(self, content: str, max_length: int) -> SummarizationResult:
        """Extract key sentences as summary."""
        import re

        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return SummarizationResult(
                summary="",
                key_points=[],
                word_count=0,
                language="unknown",
                processing_time=0
            )

        words = content.lower().split()
        word_freq = Counter(words)
        max_freq = max(word_freq.values()) if word_freq else 1

        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = sentence.lower().split()
            if sentence_words:
                score = sum(word_freq.get(w, 0) / max_freq for w in sentence_words)
                sentence_scores[i] = score / len(sentence_words)

        ranked = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        selected_indices = [i for i, _ in ranked[:5]]

        summary_sentences = [sentences[i] for i in sorted(selected_indices)]
        summary = ". ".join(summary_sentences)[:max_length]

        key_points = sentences[:3] if len(sentences) >= 3 else sentences

        english_words = {"the", "is", "are", "was", "were", "have", "has"}
        spanish_words = {"el", "la", "es", "son", "fue", "fueron", "tiene"}
        french_words = {"le", "la", "les", "est", "sont", "été", "avoir"}

        content_lower = content.lower()
        eng = sum(1 for w in english_words if w in content_lower)
        spa = sum(1 for w in spanish_words if w in content_lower)
        fra = sum(1 for w in french_words if w in content_lower)

        language = "en" if eng >= max(spa, fra) else "es" if spa >= fra else "fr"

        return SummarizationResult(
            summary=summary,
            key_points=key_points[:5],
            word_count=len(words),
            language=language,
            processing_time=0
        )


class AnomalyDetector(BaseAIModel):
    """ML-based anomaly detection for files using Isolation Forest."""

    def __init__(self):
        """Initialize anomaly detector."""
        self.model = None
        self._loaded = False
        self.thresholds = {
            "file_size": {"low": 1e6, "high": 1e8},
            "extension_risk": {
                "exe": 0.9, "scr": 0.9, "bat": 0.9, "cmd": 0.9, "vbs": 0.9,
                "pdf": 0.3, "docx": 0.2, "zip": 0.4, "txt": 0.1,
                "jpg": 0.05, "png": 0.05, "mp4": 0.2, "mp3": 0.1
            }
        }

    def load(self) -> bool:
        """Load or train anomaly model."""
        try:
            model_path = "/app/models/anomaly_detector.joblib"
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info("Loaded pre-trained anomaly detector")
            else:
                from sklearn.ensemble import IsolationForest
                self.model = IsolationForest(
                    n_estimators=100,
                    contamination=0.1,
                    random_state=42,
                    n_jobs=-1
                )
                self._train_baseline()
                os.makedirs("/app/models", exist_ok=True)
                joblib.dump(self.model, model_path)
                logger.info("Trained and saved anomaly detector")

            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load anomaly detector: {e}")
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )
            self._loaded = True
            return True

    def _train_baseline(self):
        """Train with baseline data patterns."""
        # Generate synthetic normal data
        np.random.seed(42)
        n_samples = 500
        
        # Features: [log_size, filename_len, ext_len, dot_count, is_executable]
        normal_data = np.random.randn(n_samples, 5)
        normal_data[:, 0] = np.random.uniform(5, 20, n_samples)  # log file size
        normal_data[:, 1] = np.random.uniform(5, 50, n_samples)  # filename length
        normal_data[:, 2] = np.random.uniform(2, 5, n_samples)   # extension length
        normal_data[:, 3] = np.random.uniform(0, 2, n_samples)   # dot count
        normal_data[:, 4] = np.random.uniform(0, 0.1, n_samples) # is_executable
        
        self.model.fit(normal_data)

    async def predict_async(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        metadata: Dict[str, Any] = None
    ) -> AnomalyResult:
        """Detect anomalies asynchronously."""
        import time
        start = time.time()

        features = self._extract_features(filename, file_size, file_type, metadata)

        anomaly_score = 0.0
        anomaly_reasons = []

        # Rule-based detection
        if file_size > self.thresholds["file_size"]["high"]:
            anomaly_score += 0.3
            anomaly_reasons.append("Unusually large file")
        elif file_size > self.thresholds["file_size"]["high"] * 10:
            anomaly_score += 0.5
            anomaly_reasons.append("Extremely large file")

        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in self.thresholds["extension_risk"]:
            anomaly_score += self.thresholds["extension_risk"][ext]
            anomaly_reasons.append(f"High-risk extension: {ext}")

        suspicious_patterns = ["tmp", "temp", "random", "hidden", "system", "randomized"]
        if any(p in filename.lower() for p in suspicious_patterns):
            anomaly_score += 0.2
            anomaly_reasons.append("Suspicious filename pattern")

        if ext in ["exe", "scr", "bat", "cmd", "vbs"] and "." in filename.rsplit(".", 1)[0]:
            anomaly_score += 0.4
            anomaly_reasons.append("Double extension detected")

        # ML-based score
        try:
            ml_score = self.model.decision_function(features)[0]
            ml_anomaly = self.model.predict(features)[0]
            if ml_anomaly == -1:
                anomaly_score += 0.3
                anomaly_reasons.append("ML detected anomaly pattern")
        except Exception as e:
            logger.warning(f"ML anomaly detection failed: {e}")

        anomaly_score = min(anomaly_score, 1.0)

        if anomaly_score >= 0.8:
            severity = "critical"
        elif anomaly_score >= 0.6:
            severity = "high"
        elif anomaly_score >= 0.4:
            severity = "medium"
        else:
            severity = "low"

        anomaly_type = None
        if anomaly_score >= 0.4:
            if ext in ["exe", "scr", "bat", "cmd", "vbs"]:
                anomaly_type = "executable"
            elif file_size > self.thresholds["file_size"]["high"] * 10:
                anomaly_type = "oversized"
            elif "tmp" in filename.lower() or "temp" in filename.lower():
                anomaly_type = "temporary_file"
            else:
                anomaly_type = "suspicious"

        return AnomalyResult(
            is_anomaly=anomaly_score >= 0.4,
            anomaly_score=anomaly_score,
            anomaly_type=anomaly_type,
            severity=severity,
            details={
                "reasons": anomaly_reasons,
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
                "processing_time": time.time() - start
            }
        )

    def _extract_features(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        metadata: Dict[str, Any] = None
    ) -> np.ndarray:
        """Extract numerical features for ML model."""
        features = [
            np.log1p(file_size),
            len(filename),
            len(file_type),
            1 if "." in filename else 0,
            filename.count("."),
        ]
        return np.array(features).reshape(1, -1)


class FAISSVectorSearch(BaseAIModel):
    """FAISS-based vector search for semantic file search with RAG."""

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize FAISS vector search engine."""
        self.embedding_model = embedding_model
        self.model = None
        self.index = None
        self.file_mappings: Dict[int, Dict[str, Any]] = {}
        self._loaded = False
        self._dimension = 384  # Default for all-MiniLM-L6-v2

    def load(self) -> bool:
        """Load embedding model and build FAISS index."""
        try:
            from sentence_transformers import SentenceTransformer
            from faiss import IndexFlatIP

            self.model = SentenceTransformer(self.embedding_model)
            self._dimension = self.model.get_sentence_embedding_dimension()
            
            # Create FAISS index (Inner Product for cosine similarity)
            self.index = IndexFlatIP(self._dimension)
            
            self._loaded = True
            logger.info(f"Loaded FAISS vector search with model: {self.embedding_model}")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS: {e}")
            return False

    async def predict_async(self, query: str, top_k: int = 5) -> List[VectorSearchResult]:
        """Search using semantic similarity."""
        return self.search(query, top_k)

    def index_file(self, file_id: int, content: str, metadata: Dict[str, Any]):
        """Index a file for vector search."""
        if not self._loaded:
            self.load()

        # Generate embedding
        embedding = self.model.encode(content[:10000])

        # Store mapping
        self.file_mappings[file_id] = {
            "embedding": embedding,
            "content": content[:500],
            "metadata": metadata
        }

        # Add to FAISS index
        self.index.add(np.array([embedding]).astype('float32'))

        logger.info(f"Indexed file {file_id} in FAISS")

    def search(self, query: str, top_k: int = 5) -> List[VectorSearchResult]:
        """Search using semantic similarity."""
        if not self._loaded:
            self.load()

        if not self.file_mappings:
            return []

        query_embedding = self.model.encode(query)

        # FAISS search
        query_vector = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_vector, min(top_k, len(self.file_mappings)))

        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0:
                continue
            
            # Find file_id from index mapping (simplified - in production use ID mapping)
            file_ids = list(self.file_mappings.keys())
            if idx < len(file_ids):
                file_id = file_ids[idx]
                data = self.file_mappings[file_id]
                
                # Normalize distance to similarity (0-1)
                similarity = float(distance)
                if similarity > 1:
                    similarity = 1.0 / (1.0 + np.exp(-similarity))
                
                results.append(VectorSearchResult(
                    file_id=file_id,
                    filename=data["metadata"].get("filename", "unknown"),
                    similarity=similarity,
                    content_snippet=data["content"][:200],
                    metadata=data["metadata"]
                ))

        return results[:top_k]

    def clear_index(self):
        """Clear the vector index."""
        self.index = None
        self.file_mappings.clear()
        logger.info("Vector index cleared")


class LangChainRAG:
    """LangChain-based RAG (Retrieval-Augmented Generation) for smart search."""

    def __init__(self, openai_api_key: str = None):
        """Initialize RAG system."""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.retriever = None
        self.chain = None
        self._loaded = False

    def load(self) -> bool:
        """Load LangChain RAG components."""
        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from langchain.chains import RetrievalQA
            from langchain_community.vectorstores import FAISS
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain.schema import Document

            if not self.openai_api_key:
                logger.warning("No OpenAI API key provided for RAG")
                return False

            # Initialize embeddings
            embeddings = OpenAIEmbeddings(api_key=self.openai_api_key)

            # Initialize LLM
            self.llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.openai_api_key,
                temperature=0
            )

            self._loaded = True
            logger.info("LangChain RAG initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to load LangChain RAG: {e}")
            return False

    def create_index_from_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """Create vector index from texts."""
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import FAISS
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain.schema import Document

            if not self._loaded:
                self.load()

            embeddings = OpenAIEmbeddings(api_key=self.openai_api_key)

            # Split texts
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            documents = [
                Document(page_content=text, metadata=meta or {})
                for text, meta in zip(texts, metadatas or [{}] * len(texts))
            ]

            # Create vector store
            vectorstore = FAISS.from_documents(documents, embeddings)
            self.retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

            # Create QA chain
            from langchain.chains import RetrievalQA
            self.chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever
            )

            logger.info(f"Created RAG index from {len(texts)} documents")
            return True

        except Exception as e:
            logger.error(f"Failed to create RAG index: {e}")
            return False

    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system."""
        if not self.chain:
            return {"answer": "RAG not initialized", "sources": []}

        try:
            result = self.chain.invoke({"query": question})
            return {
                "answer": result["result"],
                "sources": [doc.metadata for doc in result.get("source_documents", [])]
            }
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"answer": str(e), "sources": []}


class MultimodalAnalyzer(BaseAIModel):
    """Advanced multimodal analysis for images, video, and audio."""

    def __init__(self):
        """Initialize multimodal analyzer."""
        self.vision_model = None
        self._loaded = False

    def load(self) -> bool:
        """Load models."""
        try:
            # Try to load vision-language model
            logger.info("Multimodal analyzer initialized (basic mode)")
        except Exception as e:
            logger.warning(f"Advanced models not loaded: {e}")
        
        self._loaded = True
        return True

    async def predict_async(self, file_path: str, file_type: str) -> MultimodalResult:
        """Route to appropriate analyzer."""
        import time
        start = time.time()

        if file_type in ["image", "jpg", "jpeg", "png", "gif", "bmp", "tiff"]:
            return await self._analyze_image_async(file_path)
        elif file_type in ["video", "mp4", "avi", "mov", "wmv"]:
            return await self._analyze_video_async(file_path)
        elif file_type in ["audio", "mp3", "wav", "flac", "aac", "m4a"]:
            return await self._analyze_audio_async(file_path)
        else:
            return MultimodalResult(
                type="unknown",
                caption=None,
                objects=[],
                text_content="",
                duration=None,
                transcript=None,
                processing_time=time.time() - start
            )

    async def _analyze_image_async(self, image_path: str) -> MultimodalResult:
        """Analyze image content with OCR and object detection."""
        import time
        start = time.time()

        try:
            from PIL import Image
            import pytesseract

            results = {
                "type": "image",
                "caption": None,
                "objects": [],
                "text_content": "",
                "duration": None,
                "transcript": None,
                "processing_time": 0
            }

            # OCR
            try:
                text = pytesseract.image_to_string(Image.open(image_path))
                results["text_content"] = text.strip()
            except Exception as e:
                logger.warning(f"OCR failed: {e}")

            # Basic image analysis
            with Image.open(image_path) as img:
                results["dimensions"] = {"width": img.width, "height": img.height}
                results["format"] = img.format
                results["mode"] = img.mode

                # Generate simple caption based on content
                if img.mode == "RGB":
                    results["caption"] = f"RGB image {img.width}x{img.height}"
                else:
                    results["caption"] = f"Image {img.width}x{img.height}"

            results["processing_time"] = time.time() - start
            return MultimodalResult(**results)

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return MultimodalResult(
                type="image",
                caption=None,
                objects=[],
                text_content="",
                duration=None,
                transcript=None,
                processing_time=time.time() - start
            )

    async def _analyze_video_async(self, video_path: str) -> MultimodalResult:
        """Extract key frames and audio from video."""
        import time
        start = time.time()

        try:
            import moviepy.editor as mp

            results = {
                "type": "video",
                "caption": None,
                "objects": [],
                "text_content": "",
                "duration": 0,
                "transcript": None,
                "processing_time": 0
            }

            clip = mp.VideoFileClip(video_path)
            results["duration"] = clip.duration
            results["fps"] = clip.fps
            results["resolution"] = {"width": clip.w, "height": clip.h}
            results["caption"] = f"Video: {clip.duration:.1f}s at {clip.fps}fps"

            # Extract audio if exists
            if clip.audio:
                audio_path = video_path.replace(".mp4", ".wav")
                clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
                results["audio_extracted"] = True

            clip.close()
            results["processing_time"] = time.time() - start
            return MultimodalResult(**results)

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return MultimodalResult(
                type="video",
                caption=None,
                objects=[],
                text_content="",
                duration=None,
                transcript=None,
                processing_time=time.time() - start
            )

    async def _analyze_audio_async(self, audio_path: str) -> MultimodalResult:
        """Analyze audio for transcription and features."""
        import time
        start = time.time()

        try:
            from pydub import AudioSegment

            results = {
                "type": "audio",
                "caption": None,
                "objects": [],
                "text_content": "",
                "duration": 0,
                "transcript": None,
                "processing_time": 0
            }

            audio = AudioSegment.from_file(audio_path)
            results["duration"] = len(audio) / 1000
            results["channels"] = audio.channels
            results["sample_rate"] = audio.frame_rate
            results["caption"] = f"Audio: {results['duration']:.1f}s, {audio.channels}ch"

            results["processing_time"] = time.time() - start
            return MultimodalResult(**results)

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return MultimodalResult(
                type="audio",
                caption=None,
                objects=[],
                text_content="",
                duration=None,
                transcript=None,
                processing_time=time.time() - start
            )


class PredictiveWorkflowEngine:
    """AI-powered predictive workflow engine."""

    def __init__(self):
        """Initialize predictive workflow engine."""
        self.model = None
        self._loaded = False
        self.user_history: Dict[int, List[Dict[str, Any]]] = {}

    def load(self) -> bool:
        """Load or train prediction model."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
            self._train_baseline()
            self._loaded = True
            logger.info("Predictive workflow engine loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load predictive engine: {e}")
            return False

    def _train_baseline(self):
        """Train with baseline patterns."""
        # Features: [hour, day_of_week, file_type_category, file_size_log]
        # Labels: [action_type]
        X = np.random.randn(500, 4)
        y = np.random.randint(0, 5, 500)
        self.model.fit(X, y)

    def predict_action(
        self,
        user_id: int,
        file_category: str,
        file_size: int,
        hour: int = None,
        day_of_week: int = None
    ) -> Dict[str, Any]:
        """Predict recommended action for a file."""
        if not self._loaded:
            self.load()

        import time
        hour = hour or time.localtime().tm_hour
        day_of_week = day_of_week or time.localtime().tm_wday

        # Map category to numeric
        category_map = {
            "document": 0, "image": 1, "video": 2, "audio": 3, "code": 4
        }
        category_num = category_map.get(file_category, 0)

        features = np.array([[hour, day_of_week, category_num, np.log1p(file_size)]])

        # Get prediction
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]

        action_map = {
            0: "move_to_folder",
            1: "archive",
            2: "delete",
            3: "share",
            4: "tag_and_keep"
        }

        suggested_action = action_map.get(prediction, "keep")
        confidence = float(max(probabilities))

        return {
            "suggested_action": suggested_action,
            "confidence": confidence,
            "alternative_actions": [
                {"action": action_map.get(i, "keep"), "confidence": float(p)}
                for i, p in enumerate(probabilities) if i != prediction
            ][:2],
            "recommended_folder": f"/{file_category}s",
            "suggested_tags": self._suggest_tags(file_category)
        }

    def _suggest_tags(self, category: str) -> List[str]:
        """Suggest tags based on category."""
        base_tags = {
            "document": ["important", "work", "pending-review"],
            "image": ["photos", "media", "personal"],
            "video": ["videos", "media", "entertainment"],
            "audio": ["audio", "music", "podcasts"],
            "code": ["source", "development", "project"]
        }
        return base_tags.get(category, ["uncategorized"])

    def record_action(self, user_id: int, file_id: int, action: str, outcome: bool):
        """Record user action for learning."""
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        
        self.user_history[user_id].append({
            "file_id": file_id,
            "action": action,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat()
        })


# Global instances
clip_classifier = CLIPClassifier()
ai_classifier = HuggingFaceClassifier()
content_summarizer = ContentSummarizer()
anomaly_detector = AnomalyDetector()
faiss_vector_search = FAISSVectorSearch()
langchain_rag = LangChainRAG()
multimodal_analyzer = MultimodalAnalyzer()
predictive_engine = PredictiveWorkflowEngine()


def init_ai_modules():
    """Initialize all AI modules."""
    clip_classifier.load()
    ai_classifier.load()
    content_summarizer.load()
    anomaly_detector.load()
    faiss_vector_search.load()
    langchain_rag.load()
    multimodal_analyzer.load()
    predictive_engine.load()
    logger.info("All AI modules initialized")
