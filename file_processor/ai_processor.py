"""
AI/ML Processor

Provides OCR, content classification, and intelligent auto-tagging.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import base64
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    success: bool
    text: str
    confidence: float
    processing_time: float
    error: Optional[str] = None


@dataclass
class ClassificationResult:
    """Result of content classification."""
    category: str
    subcategory: str
    confidence: float
    suggested_tags: List[str]
    entities: List[Dict[str, str]]
    language: Optional[str] = None


@dataclass
class AutoTagSuggestion:
    """Auto-generated tag suggestion."""
    tag: str
    source: str  # "ocr", "ml_classification", "metadata", "content_analysis"
    confidence: float
    reason: str


class BaseAIModel(ABC):
    """Abstract base class for AI models."""

    @abstractmethod
    def load(self) -> bool:
        """Load the model."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model."""
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        pass


class OCRProcessor(BaseAIModel):
    """Optical Character Recognition processor."""

    def __init__(self, model_path: str = None):
        """Initialize OCR processor."""
        self.model_path = model_path or os.getenv("OCR_MODEL_PATH")
        self.model = None
        self._loaded = False

    def load(self) -> bool:
        """Load OCR model."""
        try:
            # Try to load Tesseract or EasyOCR
            try:
                import easyocr
                self.model = easyocr.Reader(['en'], gpu=False)
                self._loaded = True
                logger.info("EasyOCR model loaded")
            except ImportError:
                # Fall back to pytesseract
                import pytesseract
                from PIL import Image
                self.model = pytesseract
                self._loaded = True
                logger.info("Tesseract OCR loaded")

            return self._loaded

        except Exception as e:
            logger.error(f"Failed to load OCR model: {e}")
            return False

    def unload(self) -> None:
        """Unload OCR model."""
        self.model = None
        self._loaded = False

    def is_loaded(self) -> bool:
        """Check if OCR model is loaded."""
        return self._loaded

    def process_image(self, image_path: str) -> OCRResult:
        """Extract text from an image."""
        import time
        start_time = time.time()

        if not self._loaded:
            self.load()

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                if hasattr(self.model, 'readtext'):
                    # Using EasyOCR
                    results = self.model.readtext(img)
                    text = " ".join([result[1] for result in results])
                    confidence = sum([result[2] for result in results]) / len(results) if results else 0
                else:
                    # Using Tesseract
                    text = self.model.image_to_string(img)
                    confidence = 0.9  # Tesseract doesn't provide confidence by default

            return OCRResult(
                success=True,
                text=text.strip(),
                confidence=confidence,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )

    def process_pdf(self, pdf_path: str) -> OCRResult:
        """Extract text from a PDF with OCR if needed."""
        import time
        start_time = time.time()

        try:
            from PIL import Image
            import PyPDF2

            # First try direct text extraction
            text = ""
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # If no text found, use OCR on each page
            if not text.strip():
                logger.info("No text found in PDF, using OCR")
                images = self._pdf_to_images(pdf_path)
                for img_path in images:
                    result = self.process_image(img_path)
                    if result.success:
                        text += result.text + "\n"
                    # Clean up temp image
                    Path(img_path).unlink()

            return OCRResult(
                success=True,
                text=text.strip(),
                confidence=0.85 if text else 0,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )

    def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """Convert PDF pages to images for OCR."""
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path)
        image_paths = []

        for i, img in enumerate(images):
            img_path = f"/tmp/pdf_page_{i}.png"
            img.save(img_path)
            image_paths.append(img_path)

        return image_paths


class ContentClassifier(BaseAIModel):
    """ML-based content classifier."""

    def __init__(self):
        """Initialize content classifier."""
        self.model = None
        self._loaded = False
        self.categories = {
            "document": ["contract", "report", "invoice", "resume", "manual", "letter"],
            "image": ["photo", "screenshot", "diagram", "chart", "logo"],
            "video": ["presentation", "tutorial", "recording"],
            "audio": ["music", "podcast", "recording"],
            "code": ["script", "source_code", "config", "data"]
        }

    def load(self) -> bool:
        """Load classification model."""
        try:
            # Try to load a lightweight classification model
            # For production, use a proper model like CLIP or custom classifier
            self._loaded = True
            logger.info("Content classifier initialized (rule-based fallback)")
            return True

        except Exception as e:
            logger.error(f"Failed to load classifier: {e}")
            return False

    def unload(self) -> None:
        """Unload classifier."""
        self._loaded = False

    def is_loaded(self) -> bool:
        """Check if classifier is loaded."""
        return self._loaded

    def classify(
        self,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any] = None,
        content_text: str = ""
    ) -> ClassificationResult:
        """Classify file content."""
        if not self._loaded:
            self.load()

        # Rule-based classification using file characteristics
        category, subcategory = self._rule_based_classification(
            file_path, file_type, metadata, content_text
        )

        # Extract entities and tags
        suggested_tags = self._extract_tags(content_text, file_type)
        entities = self._extract_entities(content_text)
        language = self._detect_language(content_text)

        return ClassificationResult(
            category=category,
            subcategory=subcategory,
            confidence=0.85,
            suggested_tags=suggested_tags,
            entities=entities,
            language=language
        )

    def _rule_based_classification(
        self,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any],
        content_text: str
    ) -> Tuple[str, str]:
        """Classify using rule-based approach."""
        filename = Path(file_path).stem.lower()
        content_lower = content_text.lower() if content_text else ""

        # Check for specific document types
        if "invoice" in filename or "inv_" in filename:
            return "document", "invoice"
        if "contract" in filename or "agreement" in filename:
            return "document", "contract"
        if "resume" in filename or "cv" in filename:
            return "document", "resume"
        if "report" in filename:
            return "document", "report"

        # Check content for classification
        if content_text:
            keywords = {
                "invoice": ["invoice", "billing", "payment", "amount due"],
                "contract": ["agreement", "terms", "conditions", "parties"],
                "resume": ["experience", "education", "skills", "employment"],
                "report": ["analysis", "findings", "conclusion", "recommendations"]
            }

            for doc_type, words in keywords.items():
                if any(word in content_lower for word in words):
                    return "document", doc_type

        return file_type or "unknown", "uncategorized"

    def _extract_tags(self, content: str, file_type: str) -> List[str]:
        """Extract suggested tags from content."""
        tags = set()
        content_lower = content.lower() if content else ""

        # Add file type as tag
        if file_type:
            tags.add(file_type)

        # Extract potential tags from content
        tag_patterns = {
            "date": r"\d{4}-\d{2}-\d{2}",
            "email": r"[\w.-]+@[\w.-]+\.\w+",
            "phone": r"\+?[\d\s\-\(\)]{10,}",
            "money": r"\$[\d,]+\.?\d*"
        }

        import re
        for tag_name, pattern in tag_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                tags.add(f"has_{tag_name}")

        return list(tags)

    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Extract named entities from content."""
        entities = []

        import re
        # Simple entity extraction (in production, use NER model)
        email_pattern = r"[\w.-]+@[\w.-]+\.\w+"
        for match in re.finditer(email_pattern, content):
            entities.append({
                "type": "email",
                "value": match.group()
            })

        return entities[:10]  # Limit to 10 entities

    def _detect_language(self, content: str) -> Optional[str]:
        """Detect language of content."""
        if not content:
            return None

        # Simple language detection based on common words
        english_words = {"the", "is", "are", "was", "were", "have", "has", "been"}
        spanish_words = {"el", "la", "es", "son", "fue", "fueron", "tiene", "tienen"}

        content_lower = content.lower()
        english_count = sum(1 for word in english_words if word in content_lower)
        spanish_count = sum(1 for word in spanish_words if word in content_lower)

        if english_count > spanish_count:
            return "en"
        elif spanish_count > english_count:
            return "es"

        return "en"  # Default to English


class AutoTagger:
    """Automatic tagging system combining multiple sources."""

    def __init__(self):
        """Initialize auto-tagger."""
        self.ocr = OCRProcessor()
        self.classifier = ContentClassifier()

    def analyze_and_tag(
        self,
        file_path: str,
        file_type: str,
        metadata: Dict[str, Any] = None,
        content_text: str = ""
    ) -> List[AutoTagSuggestion]:
        """Analyze file and generate tag suggestions."""
        suggestions = []

        # 1. OCR for images and PDFs
        if file_type in ["image", "document"]:
            if file_type == "image":
                ocr_result = self.ocr.process_image(file_path)
                if ocr_result.success and ocr_result.text:
                    suggestions.append(AutoTagSuggestion(
                        tag="has_ocr_text",
                        source="ocr",
                        confidence=ocr_result.confidence,
                        reason="OCR text extracted successfully"
                    ))

        # 2. ML Classification
        classification = self.classifier.classify(
            file_path, file_type, metadata, content_text
        )
        suggestions.append(AutoTagSuggestion(
            tag=f"category:{classification.category}",
            source="ml_classification",
            confidence=classification.confidence,
            reason=f"Classified as {classification.category}/{classification.subcategory}"
        ))

        # 3. Metadata-based tags
        if metadata:
            if metadata.get("width") and metadata.get("height"):
                suggestions.append(AutoTagSuggestion(
                    tag="has_dimensions",
                    source="metadata",
                    confidence=1.0,
                    reason=f"Image dimensions: {metadata['width']}x{metadata['height']}"
                ))

        # 4. Content analysis tags
        for tag in classification.suggested_tags:
            suggestions.append(AutoTagSuggestion(
                tag=tag,
                source="content_analysis",
                confidence=0.7,
                reason="Extracted from content analysis"
            ))

        return suggestions


# Global instances
ocr_processor = OCRProcessor()
content_classifier = ContentClassifier()
auto_tagger = AutoTagger()
