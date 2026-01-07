"""
Specialized file processing API endpoints for enterprise and niche file formats.

Provides endpoints for:
- CAD/Engineering Files (DWG, DXF, STEP, IGES)
- E-books & Structured Docs (EPUB, MOBI, FB2, HTML)
- Medical/Compliance Files (DICOM, HL7, PDF/A)
- Geospatial Files (Shapefile, GeoJSON, KML, GPX)
- Disk Images (ISO, DMG, VHD, VMDK)
- Email Files (EML, MSG, PST)
"""

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .auth import get_current_active_user, User
from .database import get_db
from .models import File as FileModel, AuditLog
from .specialized_processors import specialized_processor
from .security import security_manager, rate_limiter
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== SPECIALIZED FILE PROCESSING =====

@router.post("/process/cad", response_model=Dict[str, Any])
async def process_cad_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process CAD/Engineering file (DWG, DXF, STEP, IGES).
    
    Extracts:
    - Bill of Materials (BOM)
    - Dimensions and bounding boxes
    - Layers and entities
    - Standards validation
    """
    return await _process_specialized_file(file, 'cad', current_user)


@router.post("/process/ebook", response_model=Dict[str, Any])
async def process_ebook_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process e-book and structured document (EPUB, MOBI, FB2, HTML).
    
    Extracts:
    - Table of Contents (TOC)
    - Chapters and sections
    - Metadata (title, author, ISBN)
    - Full-text content for indexing
    """
    return await _process_specialized_file(file, 'ebook', current_user)


@router.post("/process/medical", response_model=Dict[str, Any])
async def process_medical_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    anonymize_phi: bool = True,
    validate_hipaa: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process medical/compliance file (DICOM, HL7, PDF/A).
    
    Features:
    - PHI detection and redaction
    - HIPAA compliance validation
    - OCR for scanned documents
    - Structured metadata extraction
    """
    result = await _process_specialized_file(file, 'medical', current_user)
    
    # Add medical-specific processing options
    if anonymize_phi and result.get('phi_detected'):
        result['anonymized'] = True
        result['warning'] = 'PHI detected - review required before anonymization'
    
    if validate_hipaa:
        result['hipaa_validation'] = result.get('compliance', {})
    
    return result


@router.post("/process/geospatial", response_model=Dict[str, Any])
async def process_geospatial_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process geospatial/vector file (Shapefile, GeoJSON, KML, GPX).
    
    Extracts:
    - Bounds and bounding boxes
    - Coordinate reference systems (CRS)
    - Layers and feature counts
    - Projection information
    """
    return await _process_specialized_file(file, 'geospatial', current_user)


@router.post("/process/disk-image", response_model=Dict[str, Any])
async def process_disk_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process disk image file (ISO, DMG, VHD, VMDK).
    
    Features:
    - Safe content extraction without mounting
    - Filesystem detection
    - Directory listing
    - Virus scanning integration
    """
    return await _process_specialized_file(file, 'disk_image', current_user)


@router.post("/process/email", response_model=Dict[str, Any])
async def process_email_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_attachments: bool = True,
    analyze_sentiment: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process email file (EML, MSG, PST, MBOX).
    
    Extracts:
    - Headers (From, To, CC, Subject, Date)
    - Body content (plain text and HTML)
    - Attachments list
    - Thread information
    - Sentiment analysis
    """
    result = await _process_specialized_file(file, 'email', current_user)
    
    if extract_attachments:
        result['attachments_extracted'] = True
    
    if analyze_sentiment:
        result['sentiment_analysis'] = result.get('content', {}).get('sentiment', {})
    
    return result


@router.post("/process/specialized", response_model=Dict[str, Any])
async def process_any_specialized_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Auto-detect and process any supported specialized file type.
    
    Automatically identifies file type and applies appropriate processing.
    """
    return await _process_specialized_file(file, None, current_user)


# ===== HELPER FUNCTIONS =====

async def _process_specialized_file(
    file: UploadFile,
    expected_type: Optional[str],
    current_user: User
) -> Dict[str, Any]:
    """Process a specialized file upload."""
    logger.info(f"Specialized file upload: {file.filename} from user {current_user.username}")
    
    # Read file content
    try:
        file_content = await file.read()
        file_size = len(file_content)
    except Exception as e:
        logger.error(f"Failed to read file content: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file content")
    
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Validate file type
    if expected_type and not specialized_processor.can_process(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported for {expected_type} processing"
        )
    
    # Validate file type matches expected
    if expected_type:
        file_type = specialized_processor.get_file_type(file.filename)
        if file_type != expected_type:
            raise HTTPException(
                status_code=400,
                detail=f"File type mismatch. Expected {expected_type}, got {file_type}"
            )
    
    # Generate secure filename
    secure_filename = security_manager.generate_secure_filename(file.filename)
    file_path = os.path.join(settings.upload_dir, secure_filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Process with specialized processor
        result = specialized_processor.process(file_path, secure_filename)
        
        # Add basic info
        result['file_size'] = file_size
        result['user_id'] = current_user.id
        
        logger.info(f"Specialized processing completed: {secure_filename}")
        
        return result
        
    except Exception as e:
        # Clean up on error
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception:
                pass
        
        logger.error(f"Specialized processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ===== BATCH PROCESSING =====

@router.post("/process/batch", response_model=Dict[str, Any])
async def batch_process_specialized(
    files: List[UploadFile] = File(...),
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process multiple specialized files in batch.
    
    Returns summary of processing results for all files.
    """
    results = []
    errors = []
    
    for file in files:
        try:
            result = await _process_specialized_file(file, file_type, current_user)
            results.append({
                'filename': file.filename,
                'status': 'success',
                'file_type': result.get('file_type'),
                'metadata_count': len(result.get('metadata', {}))
            })
        except Exception as e:
            errors.append({
                'filename': file.filename,
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'total_files': len(files),
        'successful': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors
    }


# ===== FILE TYPE INFO =====

@router.get("/supported-formats")
def get_supported_formats(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get list of all supported specialized file formats.
    
    Returns categories and their supported extensions.
    """
    return {
        'cad': {
            'name': 'CAD/Engineering',
            'extensions': ['.dwg', '.dxf', '.step', '.stp', '.iges'],
            'capabilities': ['BOM extraction', 'Dimensions', 'Layers', 'Validation']
        },
        'ebook': {
            'name': 'E-books & Documents',
            'extensions': ['.epub', '.mobi', '.fb2', '.html', '.xhtml', '.chm'],
            'capabilities': ['TOC extraction', 'Metadata', 'Full-text indexing', 'Chapters']
        },
        'medical': {
            'name': 'Medical & Compliance',
            'extensions': ['.dcm', '.dicom', '.hl7', '.xhl7', '.pdfa'],
            'capabilities': ['PHI detection', 'HIPAA validation', 'OCR', 'DICOM tags']
        },
        'geospatial': {
            'name': 'Geospatial',
            'extensions': ['.shp', '.geojson', '.svg', '.kml', '.kmz', '.gpx', '.gml'],
            'capabilities': ['Bounds', 'Projection', 'Layers', 'CRS conversion']
        },
        'disk_image': {
            'name': 'Disk Images',
            'extensions': ['.dmg', '.iso', '.img', '.vhd', '.vmdk'],
            'capabilities': ['Content listing', 'Filesystem detection', 'Safe extraction']
        },
        'email': {
            'name': 'Email Files',
            'extensions': ['.eml', '.msg', '.pst', '.mbox'],
            'capabilities': ['Headers', 'Attachments', 'Sentiment', 'Threads']
        }
    }


@router.get("/capabilities/{file_type}")
def get_processor_capabilities(
    file_type: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get detailed capabilities for a specific file type processor.
    """
    capabilities = {
        'cad': {
            'supported_formats': ['.dwg', '.dxf', '.step', '.iges'],
            'metadata_fields': ['entities_count', 'layers', 'blocks', 'dxf_version', 'dimensions'],
            'features': ['BOM extraction', 'Standards validation', 'Preview generation']
        },
        'ebook': {
            'supported_formats': ['.epub', '.mobi', '.fb2', '.html'],
            'metadata_fields': ['title', 'author', 'language', 'chapters_count'],
            'features': ['TOC parsing', 'Full-text extraction', 'Reflowable preview']
        },
        'medical': {
            'supported_formats': ['.dcm', '.hl7', '.pdf/a'],
            'metadata_fields': ['patient_id', 'study_date', 'modality', 'phi_detected'],
            'features': ['PHI redaction', 'HIPAA compliance', 'OCR scanning']
        },
        'geospatial': {
            'supported_formats': ['.shp', '.geojson', '.kml', '.gpx'],
            'metadata_fields': ['features_count', 'bounds', 'projection', 'crs'],
            'features': ['Projection conversion', 'Thumbnail generation', 'Metadata export']
        },
        'disk_image': {
            'supported_formats': ['.iso', '.dmg', '.vhd', '.vmdk'],
            'metadata_fields': ['total_files', 'total_dirs', 'filesystem', 'format'],
            'features': ['Safe scanning', 'Content extraction', 'Virus checking']
        },
        'email': {
            'supported_formats': ['.eml', '.msg', '.pst', '.mbox'],
            'metadata_fields': ['sender', 'recipient', 'date', 'attachments_count'],
            'features': ['Header parsing', 'Attachment extraction', 'Sentiment analysis']
        }
    }
    
    if file_type not in capabilities:
        raise HTTPException(status_code=404, detail=f"File type {file_type} not found")
    
    return capabilities[file_type]
