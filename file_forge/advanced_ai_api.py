"""
Advanced AI API Endpoints

Provides AI-powered classification, summarization, anomaly detection,
smart search with RAG, and multimodal analysis endpoints.
"""

import os
import logging
import hashlib
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .auth import get_current_active_user, get_current_admin_user, User
from .database import get_db
from .models import File as FileModel, AuditLog
from .advanced_ai import (
    clip_classifier,
    ai_classifier,
    content_summarizer,
    anomaly_detector,
    faiss_vector_search,
    langchain_rag,
    multimodal_analyzer,
    predictive_engine,
    init_ai_modules
)
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/classify")
async def classify_content(
    file_id: int,
    use_clip: bool = Query(False, description="Use CLIP model instead of transformer"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered content classification using transformer models.
    Auto-categorizes files by content semantics, not just metadata.
    """
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        classifier = clip_classifier if use_clip else ai_classifier
        result = await classifier.predict_async(file.content or "")
        
        # Update file with AI classification
        file.category = result.category
        file.metadata = {
            **(file.metadata or {}),
            "ai_classification": {
                "model": "clip" if use_clip else "transformer",
                "category": result.category,
                "subcategory": result.subcategory,
                "confidence": result.confidence,
                "all_predictions": result.all_predictions,
                "timestamp": str(datetime.utcnow())
            }
        }
        db.commit()
        
        return {
            "file_id": file_id,
            "classification": {
                "model": "clip" if use_clip else "transformer",
                "category": result.category,
                "subcategory": result.subcategory,
                "confidence": result.confidence,
                "all_predictions": result.all_predictions
            },
            "processing_time": result.processing_time
        }
    except Exception as e:
        logger.error(f"AI classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/summarize")
async def summarize_content(
    file_id: int,
    max_length: int = Query(500, ge=100, le=2000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered content summarization using GPT or extractive methods.
    Generates executive summaries from documents/videos.
    """
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        result = await content_summarizer.predict_async(
            content=file.content or "",
            max_length=max_length
        )
        
        # Store summary in metadata
        file.metadata = {
            **(file.metadata or {}),
            "ai_summary": {
                "summary": result.summary,
                "key_points": result.key_points,
                "word_count": result.word_count,
                "language": result.language,
                "timestamp": str(datetime.utcnow())
            }
        }
        db.commit()
        
        return {
            "file_id": file_id,
            "summary": {
                "text": result.summary,
                "key_points": result.key_points,
                "word_count": result.word_count,
                "language": result.language
            },
            "processing_time": result.processing_time
        }
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/anomaly-detect")
async def detect_anomalies(
    file_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    ML-based anomaly detection to flag unusual files.
    Detects potential malware, policy violations, or suspicious patterns.
    """
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        result = await anomaly_detector.predict_async(
            filename=file.filename,
            file_size=file.file_size,
            file_type=file.file_type,
            metadata=file.metadata
        )
        
        # Log anomaly detection
        if result.is_anomaly:
            audit = AuditLog(
                user_id=current_user.id,
                action="anomaly_detected",
                resource_type="file",
                resource_id=str(file_id),
                details={
                    "anomaly_score": result.anomaly_score,
                    "anomaly_type": result.anomaly_type,
                    "severity": result.severity,
                    "details": result.details
                },
                success=True
            )
            db.add(audit)
            db.commit()
            
            # Send alert if critical
            if result.severity in ["critical", "high"]:
                logger.warning(f"Anomaly detected: {file.filename} - {result.anomaly_type}")
        
        return {
            "file_id": file_id,
            "is_anomaly": result.is_anomaly,
            "anomaly_score": result.anomaly_score,
            "anomaly_type": result.anomaly_type,
            "severity": result.severity,
            "details": result.details
        }
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/index-vector")
def index_for_vector_search(
    file_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Index file content for semantic search with RAG.
    Uses vector embeddings for natural language queries.
    """
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        faiss_vector_search.index_file(
            file_id=file_id,
            content=file.content or "",
            metadata={
                "filename": file.filename,
                "file_type": file.file_type,
                "category": file.category,
                "tags": file.tags
            }
        )
        
        return {
            "file_id": file_id,
            "message": "File indexed for vector search",
            "indexed_documents": len(faiss_vector_search.file_mappings)
        }
    except Exception as e:
        logger.error(f"Vector indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/search-vector")
def semantic_search(
    query: str,
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user)
):
    """
    Natural language search using vector embeddings (RAG).
    Retrieves semantically similar content from indexed files.
    """
    try:
        results = faiss_vector_search.search(query=query, top_k=top_k)
        
        return {
            "query": query,
            "results": [
                {
                    "file_id": r.file_id,
                    "filename": r.filename,
                    "similarity": r.similarity,
                    "content_snippet": r.content_snippet,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/rag-query")
async def rag_query(
    question: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Query using Retrieval-Augmented Generation (RAG).
    Provides intelligent answers based on indexed content.
    """
    if not langchain_rag._loaded:
        raise HTTPException(status_code=503, detail="RAG not initialized")
    
    try:
        result = langchain_rag.query(question)
        return result
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/predict-workflow")
async def predict_workflow(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered workflow prediction.
    Recommends sorting rules or approvals based on user history and file context.
    """
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        import time
        start = time.time()

        prediction = predictive_engine.predict_action(
            user_id=current_user.id,
            file_category=file.category or "unknown",
            file_size=file.file_size
        )

        # Record the prediction for learning
        predictive_engine.record_action(
            user_id=current_user.id,
            file_id=file_id,
            action="prediction_requested",
            outcome=True
        )

        return {
            "file_id": file_id,
            "prediction": prediction,
            "processing_time": time.time() - start
        }
    except Exception as e:
        logger.error(f"Workflow prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/multimodal-analyze")
async def analyze_multimodal(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Multimodal analysis for images, video, and audio.
    Includes OCR, object detection, captioning, and transcription.
    """
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    try:
        result = await multimodal_analyzer.predict_async(
            file_path=file.file_path,
            file_type=file.file_type
        )
        
        # Store analysis in metadata
        file.metadata = {
            **(file.metadata or {}),
            "multimodal_analysis": {
                "type": result.type,
                "caption": result.caption,
                "objects": result.objects,
                "text_content": result.text_content,
                "duration": result.duration,
                "transcript": result.transcript,
                "timestamp": str(datetime.utcnow())
            }
        }
        db.commit()
        
        return {
            "file_id": file_id,
            "file_type": file.file_type,
            "analysis": {
                "type": result.type,
                "caption": result.caption,
                "objects": result.objects,
                "text_content": result.text_content,
                "duration": result.duration,
                "transcript": result.transcript
            },
            "processing_time": result.processing_time
        }
    except Exception as e:
        logger.error(f"Multimodal analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/status")
def ai_status(
    current_user: User = Depends(get_current_admin_user)
):
    """Get AI module status."""
    return {
        "classifier": {
            "clip": {
                "loaded": clip_classifier._loaded,
                "model": clip_classifier.model_name
            },
            "transformer": {
                "loaded": ai_classifier._loaded,
                "model": ai_classifier.model_name
            }
        },
        "summarizer": {
            "loaded": content_summarizer._loaded,
            "provider": content_summarizer.provider
        },
        "anomaly_detector": {
            "loaded": anomaly_detector._loaded,
            "model": "IsolationForest"
        },
        "vector_search": {
            "loaded": faiss_vector_search._loaded,
            "indexed_files": len(faiss_vector_search.file_mappings),
            "model": faiss_vector_search.embedding_model,
            "engine": "FAISS"
        },
        "rag": {
            "loaded": langchain_rag._loaded,
            "enabled": bool(settings.openai_api_key)
        },
        "multimodal": {
            "loaded": multimodal_analyzer._loaded
        },
        "predictive": {
            "loaded": predictive_engine._loaded,
            "user_history_entries": sum(len(v) for v in predictive_engine.user_history.values())
        },
        "configuration": {
            "openai_enabled": bool(settings.openai_api_key),
            "transformers_enabled": True
        }
    }


@router.post("/ai/init")
def init_ai(
    current_user: User = Depends(get_current_admin_user)
):
    """Initialize all AI modules."""
    try:
        init_ai_modules()
        return {"message": "All AI modules initialized successfully"}
    except Exception as e:
        logger.error(f"AI initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/batch-process")
async def batch_ai_process(
    file_ids: List[int],
    operations: List[str] = ["classify", "summarize"],
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Batch process multiple files with AI operations.
    Returns job ID for tracking.
    """
    from datetime import datetime
    
    # Validate operations
    valid_operations = {"classify", "summarize", "anomaly_detect", "multimodal_analyze"}
    operations = [op for op in operations if op in valid_operations]
    
    if not operations:
        raise HTTPException(status_code=400, detail="No valid operations specified")
    
    # Create batch job record
    job_id = hashlib.md5(f"{current_user.id}{datetime.utcnow()}".encode()).hexdigest()[:8]
    
    # For now, process synchronously (in production, use Celery)
    results = []
    for file_id in file_ids:
        file = db.query(FileModel).filter(
            and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
        ).first()
        
        if not file:
            continue
            
        file_results = {"file_id": file_id, "operations": {}}
        
        for op in operations:
            try:
                if op == "classify":
                    result = await ai_classifier.predict_async(file.content or "")
                    file_results["operations"]["classify"] = {
                        "category": result.category,
                        "confidence": result.confidence
                    }
                elif op == "summarize":
                    result = await content_summarizer.predict_async(file.content or "")
                    file_results["operations"]["summarize"] = {
                        "summary_length": len(result.summary)
                    }
            except Exception as e:
                file_results["operations"][op] = {"error": str(e)}
        
        results.append(file_results)
    
    return {
        "job_id": job_id,
        "total_files": len(file_ids),
        "processed": len(results),
        "results": results
    }


@router.post("/ai/feedback")
async def submit_feedback(
    file_id: int,
    action_taken: str,
    was_helpful: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on AI predictions for continuous improvement.
    """
    file = db.query(FileModel).filter(
        and_(FileModel.id == file_id, FileModel.owner_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Record feedback
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="ai_feedback",
        details={
            "file_id": file_id,
            "action_taken": action_taken,
            "was_helpful": was_helpful
        }
    )
    db.add(activity)
    db.commit()
    
    return {"message": "Feedback recorded, thank you!"}
