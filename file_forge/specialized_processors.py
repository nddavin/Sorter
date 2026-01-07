"""
Specialized file processors for enterprise and niche file formats.

Supports:
- CAD/Engineering Files (.dwg, .dxf, .step, .iges)
- E-books & Structured Docs (.epub, .mobi, .fb2, .html, .xhtml)
- Medical/Compliance Files (.dcm/DICOM, .hl7, PDF/A)
- Geospatial/Vector (.shp, .geojson, .svg, .kml)
- Disk Images & Binaries (.dmg, .iso, .fat)
- Email/Exchange (.eml, .msg, .pst)
"""

import hashlib
import json
import logging
import mimetypes
import os
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from io import BytesIO
import re

logger = logging.getLogger(__name__)


class CADProcessor:
    """Processor for CAD/Engineering files (dwg, dxf, step, iges)."""
    
    SUPPORTED_FORMATS = ['.dwg', '.dxf', '.step', '.iges', '.stp']
    
    def __init__(self):
        """Initialize CAD processor."""
        self.temp_dir = tempfile.mkdtemp()
    
    def __del__(self):
        """Cleanup temporary directory."""
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process CAD file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'cad',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'bom': [],
            'dimensions': {},
            'layers': [],
            'validation': {}
        }
        
        try:
            if ext in ['.dwg', '.dxf']:
                result['metadata'] = self._process_dwg_dxf(file_path, filename)
            elif ext in ['.step', '.stp']:
                result['metadata'] = self._process_step(file_path, filename)
            elif ext == '.iges':
                result['metadata'] = self._process_iges(file_path, filename)
            
            # Generate preview
            result['preview'] = self._generate_preview(file_path, ext)
            
        except Exception as e:
            logger.warning(f"Failed to process CAD file {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for CAD format."""
        mime_types = {
            '.dwg': 'application/acad',
            '.dxf': 'application/dxf',
            '.step': 'application/step',
            '.iges': 'application/iges'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_dwg_dxf(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process DWG/DXF file."""
        metadata = {
            'format': 'DWG/DXF',
            'entities_count': 0,
            'layers': [],
            'blocks': [],
            'line_types': []
        }
        
        try:
            # Try using ezdxf library
            import ezdxf
            doc = ezdxf.readfile(file_path)
            
            metadata['entities_count'] = len(doc.entities)
            metadata['layers'] = [layer.dxf.name for layer in doc.layers]
            metadata['blocks'] = list(doc.blocks.keys())
            metadata['dxf_version'] = doc.header.dxfversion
            
            # Extract bounding box
            msp = doc.modelspace()
            extents = msp.extents
            if extents:
                metadata['dimensions'] = {
                    'min_x': extents.extmin.x,
                    'min_y': extents.extmin.y,
                    'min_z': extents.extmin.z,
                    'max_x': extents.extmax.x,
                    'max_y': extents.extmax.y,
                    'max_z': extents.extmax.z
                }
                
        except ImportError:
            # Fallback: parse DXF header
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read(10000)
                # Extract basic info from DXF structure
                if '$ACADVER' in content:
                    metadata['dxf_version'] = content.split('$ACADVER')[1].split('\n')[1].strip()
                metadata['layers'] = self._extract_dxf_layers(content)
        
        return metadata
    
    def _process_step(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process STEP file."""
        metadata = {
            'format': 'STEP',
            'schema': '',
            'entities': [],
            'units': 'mm'
        }
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            # Extract STEP header info
            if 'FILE_SCHEMA' in content:
                schema_match = re.search(r"\(FILE_SCHEMA\s*\(\s*'([^']+)'\s*\)\)", content)
                if schema_match:
                    metadata['schema'] = schema_match.group(1)
            
            # Count entities
            entity_types = re.findall(r"#\d+\s*=\s*(\w+)", content)
            metadata['entities'] = list(set(entity_types))[:20]
            metadata['entity_counts'] = {e: entity_types.count(e) for e in set(entity_types)}
            
            # Extract units from header
            if 'UNIT' in content:
                unit_match = re.search(r"\(UNIT\s*\(\s*(\w+)", content)
                if unit_match:
                    metadata['units'] = unit_match.group(1)
                    
        except Exception as e:
            logger.warning(f"Failed to parse STEP file: {e}")
        
        return metadata
    
    def _process_iges(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process IGES file."""
        metadata = {
            'format': 'IGES',
            'version': '',
            'product_id': '',
            'entities': [],
            'units': 'mm'
        }
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read(2000)  # Read start of file
            
            # IGES has fixed-width format in first few lines
            if len(content) >= 72:
                metadata['product_id'] = content[0:72].strip()
                if len(content) >= 144:
                    metadata['units'] = content[72:80].strip()
        
        except Exception as e:
            logger.warning(f"Failed to parse IGES file: {e}")
        
        return metadata
    
    def _extract_dxf_layers(self, content: str) -> List[str]:
        """Extract layer names from DXF content."""
        layers = []
        pattern = r'\n0\nLAYER\n.*?\n2\n(.+?)\n'
        matches = re.findall(pattern, content, re.DOTALL)
        return [m.strip() for m in matches]
    
    def _generate_preview(self, file_path: str, ext: str) -> Optional[str]:
        """Generate preview image path."""
        preview_path = None
        try:
            # Use FreeCAD or ODA converter if available
            preview_path = os.path.join(self.temp_dir, f"preview_{Path(file_path).stem}.png")
            
            # Try FreeCAD
            subprocess.run([
                'freecad', '-c',
                f'import importlib; mod=importlib.import_module("importDXF"); mod.export("{file_path}", "{preview_path}")'
            ], capture_output=True, timeout=30)
            
            if not os.path.exists(preview_path):
                # Create placeholder
                from PIL import Image
                img = Image.new('RGB', (200, 200), color='white')
                img.save(preview_path)
                
        except Exception as e:
            logger.debug(f"Preview generation failed: {e}")
        
        return preview_path


class EBookProcessor:
    """Processor for e-books and structured documents."""
    
    SUPPORTED_FORMATS = ['.epub', '.mobi', '.fb2', '.html', '.xhtml', '.chm']
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process e-book file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'ebook',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'chapters': [],
            'toc': [],
            'text_content': ''
        }
        
        try:
            if ext == '.epub':
                result = self._process_epub(file_path, filename, result)
            elif ext == '.mobi':
                result = self._process_mobi(file_path, filename, result)
            elif ext == '.fb2':
                result = self._process_fb2(file_path, filename, result)
            elif ext in ['.html', '.xhtml']:
                result = self._process_html(file_path, filename, result)
            elif ext == '.chm':
                result = self._process_chm(file_path, filename, result)
                
        except Exception as e:
            logger.warning(f"Failed to process e-book {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for e-book format."""
        mime_types = {
            '.epub': 'application/epub+zip',
            '.mobi': 'application/x-mobipocket-ebook',
            '.fb2': 'application/fb2+xml',
            '.html': 'text/html',
            '.xhtml': 'application/xhtml+xml',
            '.chm': 'application/vnd.ms-htmlhelp'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_epub(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process EPUB file."""
        try:
            with zipfile.ZipFile(file_path, 'r') as epub:
                # Read container info
                container = epub.read('META-INF/container.xml')
                rootfiles = ET.fromstring(container).findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
                
                if rootfiles:
                    opf_path = rootfiles[0].get('full-path')
                    opf_content = epub.read(opf_path)
                    
                    # Parse OPF metadata
                    root = ET.fromstring(opf_content)
                    ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'opf': 'http://www.idpf.org/2007/opf'}
                    
                    metadata_el = root.find('opf:metadata', ns)
                    if metadata_el is None:
                        # Try without namespace
                        metadata_el = root.find('metadata')
                    
                    if metadata_el is not None:
                        # Extract Dublin Core metadata
                        for tag in ['title', 'creator', 'language', 'identifier', 'subject', 'description']:
                            elem = metadata_el.find(f'dc:{tag}', ns) or metadata_el.find(f'.//{tag}')
                            if elem is not None and elem.text:
                                result['metadata'][tag] = elem.text
                                if tag == 'creator':
                                    result['metadata']['author'] = elem.text
                    
                    # Extract chapters/Spine
                    manifest = {item.get('id'): item.get('href') for item in root.findall('.//{http://www.idpf.org/2007/opf}manifest/{http://www.idpf.org/2007/opf}item')}
                    spine = root.find('.//{http://www.idpf.org/2007/opf}spine')
                    if spine is not None:
                        for itemref in spine.findall('itemref'):
                            item_id = itemref.get('idref')
                            if item_id in manifest:
                                result['chapters'].append({
                                    'id': item_id,
                                    'href': manifest[item_id]
                                })
                    
                    # Build TOC from NCX if present
                    ncx_id = root.find('.//{http://www.idpf.org/2007/opf}item[@media-type="application/x-dtbncx+xml"]')
                    if ncx_id is not None:
                        ncx_path = opf_path.rsplit('/', 1)[0] + '/' + manifest.get(ncx_id.get('id'))
                        try:
                            ncx_content = epub.read(ncx_path)
                            ncx_root = ET.fromstring(ncx_content)
                            for navpoint in ncx_root.findall('.//{http://www.daisy.org/z3986/2005/ncx/}navPoint'):
                                label = navpoint.find('.//{http://www.daisy.org/z3986/2005/ncx/}text')
                                if label is not None:
                                    result['toc'].append({
                                        'title': label.text,
                                        'playOrder': navpoint.get('playOrder')
                                    })
                        except Exception as e:
                            logger.debug(f"Failed to parse NCX: {e}")
                    
                    # Extract text content from HTML files
                    text_content = []
                    for item_id, href in manifest.items():
                        if href.endswith(('.html', '.xhtml', '.htm')):
                            try:
                                content = epub.read(href).decode('utf-8', errors='ignore')
                                # Simple text extraction
                                text = re.sub(r'<[^>]+>', ' ', content)
                                text = re.sub(r'\s+', ' ', text).strip()
                                text_content.append(text)
                            except Exception:
                                pass
                    
                    result['text_content'] = ' '.join(text_content)[:10000]
                    result['metadata']['chapters_count'] = len(result['chapters'])
                    
        except Exception as e:
            logger.warning(f"EPUB parsing failed: {e}")
        
        return result
    
    def _process_mobi(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process MOBI file."""
        try:
            # Use mobi library if available
            from mobi import Mobi
            mobi = Mobi(file_path)
            result['metadata'] = mobi.metadata
            result['text_content'] = mobi.extract_text()[:10000]
            
        except ImportError:
            # Fallback: parse raw structure
            with open(file_path, 'rb') as f:
                header = f.read(2000)
                # Basic header parsing
                if b'EXTH' in header:
                    result['metadata']['has_exth'] = True
                if b'MOBI' in header:
                    result['metadata']['format'] = 'MOBI'
        
        return result
    
    def _process_fb2(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process FB2 (FictionBook) file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Extract metadata
            desc = root.find('.//fb:description', ns)
            if desc is not None:
                title_info = desc.find('.//fb:title-info', ns) or desc.find('title-info')
                if title_info is not None:
                    for tag in ['author', 'book-title', 'lang', 'genre']:
                        elem = title_info.find(f'.//fb:{tag}', ns) or title_info.find(tag)
                        if elem is not None:
                            if tag == 'author':
                                last_name = elem.find('.//fb:last-name', ns) or elem.find('last-name')
                                first_name = elem.find('.//fb:first-name', ns) or elem.find('first-name')
                                result['metadata']['author'] = f"{first_name.text if first_name is not None else ''} {last_name.text if last_name is not None else ''}".strip()
                            else:
                                result['metadata'][tag] = elem.text
            
            # Extract body sections (chapters)
            for body in root.findall('.//fb:body', ns) or root.findall('body'):
                for section in body.findall('.//fb:section', ns) or body.findall('section'):
                    titles = section.findall('.//fb:title', ns) or section.findall('title')
                    for title in titles:
                        title_text = ''.join(title.itertext()).strip()
                        if title_text:
                            result['chapters'].append({'title': title_text})
            
            # Extract all text
            text_parts = []
            for p in root.iter():
                if p.tag in ['p', 'strong', 'emphasis']:
                    text_parts.append(p.text or '')
            result['text_content'] = ' '.join(text_parts)[:10000]
            
        except Exception as e:
            logger.warning(f"FB2 parsing failed: {e}")
        
        return result
    
    def _process_html(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process HTML/XHTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse with BeautifulSoup-like approach
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata
            result['metadata'] = {
                'title': soup.title.string if soup.title else '',
                'description': soup.find('meta', attrs={'name': 'description'}).get('content', '') if soup.find('meta', attrs={'name': 'description'}) else '',
                'keywords': soup.find('meta', attrs={'name': 'keywords'}).get('content', '') if soup.find('meta', attrs={'name': 'keywords'}) else '',
            }
            
            # Extract headings
            result['chapters'] = []
            for i, h in enumerate(soup.find_all(['h1', 'h2', 'h3'])[:20]):
                result['chapters'].append({
                    'level': int(h.name[1]),
                    'text': h.get_text(strip=True)
                })
            
            # Extract text content
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            result['text_content'] = soup.get_text(separator=' ', strip=True)[:10000]
            
        except ImportError:
            # Fallback without BeautifulSoup
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                result['metadata']['title'] = title_match.group(1)
            
            result['text_content'] = re.sub(r'<[^>]+>', ' ', content)
            result['text_content'] = re.sub(r'\s+', ' ', result['text_content']).strip()[:10000]
        
        return result
    
    def _process_chm(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process CHM file."""
        try:
            import chm.chm as chm_module
            c = chm_module.CHMFile()
            c.LoadCHM(file_path)
            
            # Extract metadata
            result['metadata']['title'] = c.title or ''
            result['metadata']['topics'] = len(c.topics)
            
            # Extract table of contents
            result['toc'] = []
            for topic in c.topics[:50]:
                result['toc'].append({
                    'title': topic.title,
                    'path': topic.path
                })
            
            c.CloseCHM()
            
        except Exception as e:
            logger.warning(f"CHM parsing failed: {e}")
        
        return result


class MedicalProcessor:
    """Processor for medical and compliance files (DICOM, HL7, PDF/A)."""
    
    SUPPORTED_FORMATS = ['.dcm', '.dicom', '.hl7', '.xhl7', '.pdfa', '.pdf']
    
    def __init__(self):
        """Initialize medical processor."""
        self.phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{9}\b',  # SSN alternative
            r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b\d{3}[-]\d{2}[-]\d{4}\b',  # Another SSN format
        ]
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process medical/compliance file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'medical',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'phi_detected': False,
            'anonymized': False,
            'compliance': {}
        }
        
        try:
            if ext in ['.dcm', '.dicom']:
                result = self._process_dicom(file_path, filename, result)
            elif ext in ['.hl7', '.xhl7']:
                result = self._process_hl7(file_path, filename, result)
            elif ext in ['.pdfa', '.pdf']:
                result = self._process_pdfa(file_path, filename, result)
            
            # Check for PHI in text content
            if 'text_content' in result and result['text_content']:
                result['phi_detected'] = self._check_phi(result['text_content'])
            
            # Validate compliance
            result['compliance'] = self._validate_compliance(result)
            
        except Exception as e:
            logger.warning(f"Failed to process medical file {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for medical format."""
        mime_types = {
            '.dcm': 'application/dicom',
            '.dicom': 'application/dicom',
            '.hl7': 'application/hl7-v2',
            '.xhl7': 'application/hl7-v2+xml',
            '.pdfa': 'application/pdfa',
            '.pdf': 'application/pdf'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_dicom(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process DICOM file."""
        try:
            import pydicom
            ds = pydicom.dcmread(file_path)
            
            # Extract key DICOM tags
            tags_to_extract = [
                ('PatientName', 'patient_name'),
                ('PatientID', 'patient_id'),
                ('PatientBirthDate', 'patient_birth_date'),
                ('PatientSex', 'patient_sex'),
                ('StudyDate', 'study_date'),
                ('StudyTime', 'study_time'),
                ('Modality', 'modality'),
                ('Manufacturer', 'manufacturer'),
                ('InstitutionName', 'institution_name'),
                ('StudyDescription', 'study_description'),
                ('SeriesDescription', 'series_description'),
                ('BodyPartExamined', 'body_part_examined'),
                ('StudyInstanceUID', 'study_uid'),
                ('SeriesInstanceUID', 'series_uid'),
            ]
            
            for tag, key in tags_to_extract:
                if tag in ds:
                    result['metadata'][key] = str(ds[tag].value)
            
            # Check for pixel data
            if 'PixelData' in ds:
                result['metadata']['has_pixel_data'] = True
                result['metadata']['rows'] = ds.Rows if 'Rows' in ds else None
                result['metadata']['columns'] = ds.Columns if 'Columns' in ds else None
            
            # Generate preview
            try:
                import pydicom
                from pydicom.encaps import decode_data_sequence
                import numpy as np
                arr = ds.pixel_array
                result['metadata']['pixel_array_shape'] = arr.shape
            except Exception:
                pass
            
            result['metadata']['sop_instance_uid'] = str(ds.SOPInstanceUID) if 'SOPInstanceUID' in ds else ''
            
        except ImportError:
            logger.warning("pydicom not installed, basic DICOM parsing only")
        
        return result
    
    def _process_hl7(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process HL7 v2.x message."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # HL7 segment parsing
            segments = content.strip().split('|')
            
            # Extract MSH (Message Header)
            if len(segments) > 0:
                msh = segments[0]
                fields = msh.split('^')
                if len(fields) >= 11:
                    result['metadata'] = {
                        'message_type': fields[8] if len(fields) > 8 else '',
                        'message_control_id': fields[9] if len(fields) > 9 else '',
                        'sending_facility': fields[2] if len(fields) > 2 else '',
                        'receiving_facility': fields[4] if len(fields) > 4 else ''
                    }
            
            # Parse other segments
            result['segments'] = []
            for i, segment in enumerate(segments[:50]):
                if segment:
                    segment_type = segment.split('|')[0] if segment else ''
                    if segment_type:
                        result['segments'].append({
                            'type': segment_type,
                            'raw': segment[:200]
                        })
            
            # Detect message type
            for segment in segments:
                if segment.startswith('MSH'):
                    if 'ADT' in segment:
                        result['metadata']['message_type'] = 'ADT'
                    elif 'ORM' in segment:
                        result['metadata']['message_type'] = 'ORM'
                    elif 'ORU' in segment:
                        result['metadata']['message_type'] = 'ORU'
                    elif 'SIU' in segment:
                        result['metadata']['message_type'] = 'SIU'
                    break
            
            result['text_content'] = content[:5000]
            
        except Exception as e:
            logger.warning(f"HL7 parsing failed: {e}")
        
        return result
    
    def _process_pdfa(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process PDF/A file."""
        try:
            import PyPDF2
            from pdfminer.high_level import extract_text
            
            # Check if PDF/A compliant
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                metadata = pdf.metadata
                
                result['metadata'] = {
                    'pages': len(pdf.pages),
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'creation_date': str(metadata.get('/CreationDate', '')),
                    'modification_date': str(metadata.get('/ModDate', ''))
                }
                
                # Check for PDF/A conformance
                result['metadata']['is_pdfa'] = '/PDF/A' in str(metadata) or 'PDF/A' in str(metadata)
            
            # Extract text
            result['text_content'] = extract_text(file_path)[:10000]
            
            # Try OCR if no text extracted
            if not result['text_content'].strip():
                try:
                    import pytesseract
                    from PIL import Image
                    
                    images = []
                    for page_num in range(min(5, len(pdf.pages))):
                        page = pdf.pages[page_num]
                        # Convert to image (simplified)
                        result['text_content'] = "[OCR Required - No text layer]"
                except ImportError:
                    pass
            
        except ImportError:
            # Fallback to basic PyPDF2
            try:
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    result['metadata'] = {'pages': len(pdf.pages)}
                    result['text_content'] = ''
                    for page in pdf.pages[:10]:
                        result['text_content'] += page.extract_text() or ''
            except Exception as e:
                logger.warning(f"PDF parsing failed: {e}")
        
        return result
    
    def _check_phi(self, text: str) -> bool:
        """Check if text contains potential PHI."""
        for pattern in self.phi_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _validate_compliance(self, result: Dict) -> Dict:
        """Validate compliance status."""
        compliance = {
            'hipaa_compliant': True,
            'issues': []
        }
        
        if result.get('phi_detected'):
            compliance['hipaa_compliant'] = False
            compliance['issues'].append('Potential PHI detected - requires review')
        
        if result['metadata'].get('is_pdfa') == False:
            compliance['issues'].append('PDF not PDF/A compliant')
        
        return compliance


class GeospatialProcessor:
    """Processor for geospatial and vector files."""
    
    SUPPORTED_FORMATS = ['.shp', '.geojson', '.svg', '.kml', '.kmz', '.gpx', '.gml']
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process geospatial file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'geospatial',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'bounds': {},
            'projection': None,
            'layers': []
        }
        
        try:
            if ext == '.shp':
                result = self._process_shapefile(file_path, filename, result)
            elif ext == '.geojson':
                result = self._process_geojson(file_path, filename, result)
            elif ext == '.svg':
                result = self._process_svg(file_path, filename, result)
            elif ext in ['.kml', '.kmz']:
                result = self._process_kml(file_path, filename, result)
            elif ext == '.gpx':
                result = self._process_gpx(file_path, filename, result)
                
        except Exception as e:
            logger.warning(f"Failed to process geospatial file {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for geospatial format."""
        mime_types = {
            '.shp': 'application/shapefile',
            '.geojson': 'application/geo+json',
            '.svg': 'image/svg+xml',
            '.kml': 'application/vnd.google-earth.kml+xml',
            '.kmz': 'application/vnd.google-earth.kmz',
            '.gpx': 'application/gpx+xml',
            '.gml': 'application/gml+xml'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_shapefile(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process Shapefile."""
        try:
            import geopandas as gpd
            gdf = gpd.read_file(file_path)
            
            result['metadata'] = {
                'geometry_type': str(gdf.geom_type.iloc[0]) if len(gdf) > 0 else '',
                'features_count': len(gdf),
                'columns': list(gdf.columns),
                'crs': str(gdf.crs) if gdf.crs else 'unknown'
            }
            
            # Calculate bounds
            if len(gdf) > 0:
                bounds = gdf.total_bounds
                result['bounds'] = {
                    'min_x': float(bounds[0]),
                    'min_y': float(bounds[1]),
                    'max_x': float(bounds[2]),
                    'max_y': float(bounds[3])
                }
            
            result['projection'] = str(gdf.crs) if gdf.crs else None
            
        except ImportError:
            # Basic shapefile parsing
            with open(file_path, 'rb') as f:
                header = f.read(100)
                if len(header) >= 28:
                    # Parse shapefile main file header
                    file_code = struct.unpack('>i', header[0:4])[0]
                    if file_code == 9994:  # Shapefile magic number
                        result['metadata'] = {'format': 'ESRI Shapefile'}
                        
                        # Try to read dbf for attribute info
                        dbf_path = file_path.replace('.shp', '.dbf')
                        if os.path.exists(dbf_path):
                            result['metadata']['has_dbf'] = True
        
        return result
    
    def _process_geojson(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process GeoJSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check GeoJSON type
            if 'type' in data:
                result['metadata']['geojson_type'] = data['type']
            
            if 'crs' in data:
                result['metadata']['crs'] = data['crs']
            
            # Count features
            if data.get('type') == 'FeatureCollection':
                features = data.get('features', [])
                result['metadata']['features_count'] = len(features)
                result['layers'] = [{'name': 'features', 'count': len(features)}]
                
                # Calculate bounds
                all_coords = []
                for feature in features:
                    geom = feature.get('geometry', {})
                    all_coords.extend(self._extract_coords(geom))
                
                if all_coords:
                    result['bounds'] = {
                        'min_x': min(c[0] for c in all_coords),
                        'min_y': min(c[1] for c in all_coords),
                        'max_x': max(c[0] for c in all_coords),
                        'max_y': max(c[1] for c in all_coords)
                    }
                    
            elif data.get('type') == 'Feature':
                result['metadata']['features_count'] = 1
                result['layers'] = [{'name': 'feature', 'count': 1}]
            
            result['projection'] = 'EPSG:4326'  # Default for GeoJSON
            
        except Exception as e:
            logger.warning(f"GeoJSON parsing failed: {e}")
        
        return result
    
    def _extract_coords(self, geometry: Dict) -> List[Tuple]:
        """Extract coordinates from geometry."""
        coords = []
        if not geometry:
            return coords
        
        geom_type = geometry.get('type', '')
        coordinates = geometry.get('coordinates', [])
        
        if geom_type == 'Point':
            coords.append(tuple(coordinates))
        elif geom_type == 'LineString':
            coords.extend(coordinates)
        elif geom_type == 'Polygon':
            for ring in coordinates:
                coords.extend(ring)
        elif geom_type == 'MultiPolygon':
            for polygon in coordinates:
                for ring in polygon:
                    coords.extend(ring)
        
        return coords
    
    def _process_svg(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process SVG file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle SVG namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Extract dimensions
            width = root.get('width', root.get('{http://www.w3.org/1999/xlink}width', ''))
            height = root.get('height', root.get('{http://www.w3.org/1999/xlink}height', ''))
            viewbox = root.get('viewBox', '')
            
            result['metadata'] = {
                'width': width,
                'height': height,
                'viewbox': viewbox,
                'title': root.find('svg:title', ns).text if root.find('svg:title', ns) else '',
            }
            
            # Count elements
            result['layers'] = []
            for tag in ['rect', 'circle', 'path', 'text', 'g', 'line', 'polygon', 'polyline']:
                elements = root.findall(f'.//svg:{tag}', ns) or root.findall(f'.//{tag}')
                if elements:
                    result['layers'].append({
                        'name': tag,
                        'count': len(elements)
                    })
            
            # Check if it's a map (has geographic data)
            if result['metadata'].get('viewbox') and -180 <= float(result['metadata']['viewbox'].split()[0]) <= 180:
                result['metadata']['is_geographic'] = True
            
        except Exception as e:
            logger.warning(f"SVG parsing failed: {e}")
        
        return result
    
    def _process_kml(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process KML/KMZ file."""
        try:
            if filename.endswith('.kmz'):
                with zipfile.ZipFile(file_path, 'r') as kmz:
                    # Look for doc.kml
                    for name in kmz.namelist():
                        if name.endswith('.kml'):
                            content = kmz.read(name).decode('utf-8')
                            break
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            root = ET.fromstring(content)
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Extract document name
            doc = root.find('.//kml:Document', ns) or root.find('.//Document')
            if doc is not None:
                name_elem = doc.find('kml:name', ns) or doc.find('name')
                if name_elem is not None and name_elem.text:
                    result['metadata']['name'] = name_elem.text
            
            # Count placemarks
            placemarks = root.findall('.//kml:Placemark', ns) or root.findall('.//Placemark')
            result['metadata']['placemarks_count'] = len(placemarks)
            result['layers'] = [{'name': 'placemarks', 'count': len(placemarks)}]
            
            # Extract bounds from coordinates
            coords = root.findall('.//kml:coordinates', ns) or root.findall('.//coordinates')
            all_coords = []
            for coord_elem in coords:
                if coord_elem.text:
                    for coord_group in coord_elem.text.strip().split():
                        parts = coord_group.split(',')
                        if len(parts) >= 2:
                            try:
                                all_coords.append((float(parts[0]), float(parts[1])))
                            except ValueError:
                                pass
            
            if all_coords:
                result['bounds'] = {
                    'min_x': min(c[0] for c in all_coords),
                    'min_y': min(c[1] for c in all_coords),
                    'max_x': max(c[0] for c in all_coords),
                    'max_y': max(c[1] for c in all_coords)
                }
            
        except Exception as e:
            logger.warning(f"KML parsing failed: {e}")
        
        return result
    
    def _process_gpx(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process GPX file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
            
            # Extract metadata
            metadata = root.find('gpx:metadata', ns) or root.find('metadata')
            if metadata is not None:
                name_elem = metadata.find('gpx:name', ns) or metadata.find('name')
                if name_elem is not None:
                    result['metadata']['name'] = name_elem.text
            
            # Count waypoints, routes, tracks
            waypoints = root.findall('.//gpx:wpt', ns) or root.findall('.//wpt')
            routes = root.findall('.//gpx:rte', ns) or root.findall('.//rte')
            tracks = root.findall('.//gpx:trk', ns) or root.findall('.//trk')
            
            result['metadata'] = {
                'waypoints_count': len(waypoints),
                'routes_count': len(routes),
                'tracks_count': len(tracks)
            }
            result['layers'] = [
                {'name': 'waypoints', 'count': len(waypoints)},
                {'name': 'routes', 'count': len(routes)},
                {'name': 'tracks', 'count': len(tracks)}
            ]
            
        except Exception as e:
            logger.warning(f"GPX parsing failed: {e}")
        
        return result


class DiskImageProcessor:
    """Processor for disk images and binaries."""
    
    SUPPORTED_FORMATS = ['.dmg', '.iso', '.img', '.vhd', '.vmdk', '.bin']
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process disk image file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'disk_image',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'file_listing': [],
            'total_files': 0,
            'total_dirs': 0
        }
        
        try:
            if ext == '.iso':
                result = self._process_iso(file_path, filename, result)
            elif ext == '.dmg':
                result = self._process_dmg(file_path, filename, result)
            elif ext in ['.img', '.bin']:
                result = self._process_img(file_path, filename, result)
            elif ext in ['.vhd', '.vmdk']:
                result = self._process_virtual_disk(file_path, filename, result)
                
        except Exception as e:
            logger.warning(f"Failed to process disk image {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for disk image format."""
        mime_types = {
            '.dmg': 'application/x-apple-diskimage',
            '.iso': 'application/x-iso9660-image',
            '.img': 'application/x-raw-disk-image',
            '.vhd': 'application/x-virtualbox-vhd',
            '.vmdk': 'application/x-virtualbox-vmdk',
            '.bin': 'application/octet-stream'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_iso(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process ISO file."""
        try:
            import pycdlib
            
            iso = pycdlib.PyCdLib()
            iso.open(file_path)
            
            # Get ISO info
            result['metadata'] = {
                'volume_id': iso.pvd.volume_identifier.decode('utf-8', errors='ignore') if hasattr(iso.pvd, 'volume_identifier') else '',
                'application_id': iso.pvd.application_identifier.decode('utf-8', errors='ignore') if hasattr(iso.pvd, 'application_identifier') else '',
                'publisher': iso.pvd.preparer_identifier.decode('utf-8', errors='ignore') if hasattr(iso.pvd, 'preparer_identifier') else ''
            }
            
            # Walk directory tree
            file_listing = []
            total_files = 0
            total_dirs = 0
            
            for root, dirs, files in iso.walk(iso.pvd.root_dir_record):
                for d in dirs:
                    total_dirs += 1
                    file_listing.append({
                        'type': 'directory',
                        'path': os.path.join(root, d)
                    })
                for f in files:
                    total_files += 1
                    file_listing.append({
                        'type': 'file',
                        'path': os.path.join(root, f),
                        'size': files[f]
                    })
            
            result['file_listing'] = file_listing[:100]  # Limit listing
            result['total_files'] = total_files
            result['total_dirs'] = total_dirs
            
            iso.close()
            
        except ImportError:
            result = self._basic_iso_analysis(file_path, result)
        except Exception as e:
            logger.warning(f"ISO parsing failed: {e}")
        
        return result
    
    def _basic_iso_analysis(self, file_path: str, result: Dict) -> Dict:
        """Basic ISO analysis without pycdlib."""
        with open(file_path, 'rb') as f:
            header = f.read(32768)
            
        # Check for ISO 9660 signature
        if b'CD001' in header:
            result['metadata']['format'] = 'ISO 9660'
            result['metadata']['has_filesystem'] = True
        
        # Look for directory entries
        if b'\x00' in header[32768:]:
            result['metadata']['contains_data'] = True
        
        return result
    
    def _process_dmg(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process DMG file."""
        try:
            # Try using libdmg-hfsplus
            result['metadata']['format'] = 'Apple DMG'
            
            # Basic structure analysis
            with open(file_path, 'rb') as f:
                header = f.read(8192)
            
            if b'koly' in header:
                result['metadata']['has_koly_block'] = True
                result['metadata']['encryption'] = 'encrypted' if b'encrypted' in header.lower() else 'none'
            
            # Try to extract structure
            import subprocess
            try:
                result['temp_dir'] = tempfile.mkdtemp()
                result['file_listing'] = []
                
                # Use 7z if available
                subprocess.run(['7z', 'e', '-y', file_path, f'-o{result["temp_dir"]}'], 
                              capture_output=True, timeout=30)
                
                for root, dirs, files in os.walk(result['temp_dir']):
                    for f in files:
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, result['temp_dir'])
                        size = os.path.getsize(full_path)
                        result['file_listing'].append({
                            'type': 'file',
                            'path': rel_path,
                            'size': size
                        })
                
                result['total_files'] = len(result['file_listing'])
                
            except Exception:
                pass
            
        except Exception as e:
            logger.warning(f"DMG parsing failed: {e}")
        
        return result
    
    def _process_img(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process raw disk image."""
        try:
            file_size = os.path.getsize(file_path)
            result['metadata'] = {
                'size_bytes': file_size,
                'format': 'raw disk image'
            }
            
            # Try to identify filesystem
            with open(file_path, 'rb') as f:
                header = f.read(8192)
            
            if b'FAT' in header[:512]:
                result['metadata']['filesystem'] = 'FAT'
                result['metadata']['fat_type'] = 'FAT32' if b'FAT32' in header else 'FAT16'
            elif header[510:512] == b'\x55\xaa':
                result['metadata']['filesystem'] = 'DOS/MBR'
            elif b'\xef\x53\xf8' in header[:1024]:
                result['metadata']['filesystem'] = 'NTFS'
            elif header[:8] == b'\x00\x00\x00\x00':
                result['metadata']['filesystem'] = 'ext2/3/4 (possible)'
            
        except Exception as e:
            logger.warning(f"IMG parsing failed: {e}")
        
        return result
    
    def _process_virtual_disk(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process VHD/VMDK virtual disk."""
        try:
            file_size = os.path.getsize(file_path)
            ext = Path(filename).suffix.lower()
            
            result['metadata'] = {
                'format': 'VHD' if ext == '.vhd' else 'VMDK',
                'size_bytes': file_size
            }
            
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Check for VHD footer
            if header[0:4] == b'conectix':
                result['metadata']['type'] = 'dynamic' if header[512:516] == b'dy' else 'fixed'
            
            # Check for VMDK descriptor
            if b'VMDK' in header or b'VMware' in header:
                result['metadata']['creator'] = 'VMware'
            
        except Exception as e:
            logger.warning(f"Virtual disk parsing failed: {e}")
        
        return result


class EmailProcessor:
    """Processor for email files (EML, MSG, PST)."""
    
    SUPPORTED_FORMATS = ['.eml', '.msg', '.pst', '.mbox']
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process email file and extract metadata."""
        ext = Path(filename).suffix.lower()
        result = {
            'filename': filename,
            'file_type': 'email',
            'mime_type': self._get_mime_type(ext),
            'metadata': {},
            'content': {},
            'headers': {},
            'attachments': [],
            'text_content': ''
        }
        
        try:
            if ext == '.eml':
                result = self._process_eml(file_path, filename, result)
            elif ext == '.msg':
                result = self._process_msg(file_path, filename, result)
            elif ext == '.pst':
                result = self._process_pst(file_path, filename, result)
            elif ext == '.mbox':
                result = self._process_mbox(file_path, filename, result)
                
        except Exception as e:
            logger.warning(f"Failed to process email file {filename}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for email format."""
        mime_types = {
            '.eml': 'message/rfc822',
            '.msg': 'application/vnd.ms-outlook',
            '.pst': 'application/vnd.ms-outlook',
            '.mbox': 'application/mbox'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _process_eml(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process EML file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Split headers and body
            if '\n\n' in content or '\r\n\r\n' in content:
                sep = '\n\n' if '\n\n' in content else '\r\n\r\n'
                headers_raw, body = content.split(sep, 1)
            else:
                headers_raw, body = content, ''
            
            # Parse headers
            result['headers'] = self._parse_headers(headers_raw)
            result['metadata'] = {
                'from': result['headers'].get('From', ''),
                'to': result['headers'].get('To', ''),
                'subject': result['headers'].get('Subject', ''),
                'date': result['headers'].get('Date', ''),
                'cc': result['headers'].get('Cc', ''),
                'message_id': result['headers'].get('Message-ID', '')
            }
            
            # Extract body
            result['text_content'] = self._extract_body(body, result['headers'])
            
            # Extract attachments
            result['attachments'] = self._extract_attachments(content)
            
            # Sentiment analysis
            result['content']['sentiment'] = self._analyze_sentiment(result['text_content'])
            
        except Exception as e:
            logger.warning(f"EML parsing failed: {e}")
        
        return result
    
    def _parse_headers(self, headers_raw: str) -> Dict[str, str]:
        """Parse email headers."""
        headers = {}
        current_key = None
        
        for line in headers_raw.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
            if line and (line[0].isalnum() or line[0] == '_'):
                if ':' in line:
                    parts = line.split(':', 1)
                    current_key = parts[0].strip()
                    headers[current_key] = parts[1].strip()
                elif current_key and line:
                    headers[current_key] += ' ' + line
            elif line.startswith(' ') and current_key:
                headers[current_key] += ' ' + line.strip()
        
        return headers
    
    def _extract_body(self, body: str, headers: Dict) -> str:
        """Extract email body."""
        content_type = headers.get('Content-Type', '').lower()
        
        if 'text/plain' in content_type:
            # Plain text - remove MIME boundaries
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].split(';')[0].strip('"\'')
                body = body.split('--' + boundary)[0]
            return body.strip()
        
        elif 'text/html' in content_type:
            # HTML - convert to text
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(body, 'html.parser')
                for tag in soup(['script', 'style', 'nav']):
                    tag.decompose()
                return soup.get_text(separator=' ', strip=True)
            except ImportError:
                # Strip HTML tags
                text = re.sub(r'<[^>]+>', ' ', body)
                return re.sub(r'\s+', ' ', text).strip()
        
        return body[:2000]
    
    def _extract_attachments(self, content: str) -> List[Dict]:
        """Extract attachment info from email."""
        attachments = []
        
        # Pattern for Content-Disposition headers
        pattern = r'Content-Disposition:\s*attachment[^;]*;\s*filename="([^"]+)"'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for filename in matches:
            attachments.append({
                'filename': filename,
                'type': 'attachment'
            })
        
        return attachments
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'thank', 'thanks', 'appreciate']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'wrong', 'problem', 'issue', 'fail', 'disappointed']
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            sentiment = 'positive'
        elif neg_count > pos_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'positive_score': pos_count,
            'negative_score': neg_count
        }
    
    def _process_msg(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process MSG file (Outlook)."""
        try:
            import extract_msg
            
            msg = extract_msg.openMsg(file_path)
            
            result['metadata'] = {
                'subject': msg.subject,
                'sender': msg.sender,
                'to': msg.to,
                'cc': msg.cc,
                'date': msg.date,
                'importance': msg.importance
            }
            
            result['headers'] = {
                'From': msg.sender,
                'To': msg.to,
                'Subject': msg.subject,
                'Date': msg.date
            }
            
            result['text_content'] = msg.body or ''
            
            # Extract attachments
            for attachment in msg.attachments:
                result['attachments'].append({
                    'filename': attachment.getFilename(),
                    'size': attachment.getSize(),
                    'type': 'attachment'
                })
            
        except ImportError:
            result = self._basic_msg_analysis(file_path, result)
        except Exception as e:
            logger.warning(f"MSG parsing failed: {e}")
        
        return result
    
    def _basic_msg_analysis(self, file_path: str, result: Dict) -> Dict:
        """Basic MSG analysis without extract_msg."""
        with open(file_path, 'rb') as f:
            content = f.read(4096)
        
        # Look for common Outlook patterns
        if b'\x00T\x00o\x00p\x00i\x00c' in content:
            result['metadata']['is_outlook_msg'] = True
        
        return result
    
    def _process_pst(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process PST file."""
        try:
            import pypff
            
            pst = pypff.file()
            pst.open(file_path)
            
            result['metadata'] = {
                'message_count': 0,
                'folder_count': 0
            }
            
            # Walk folders
            def walk_folder(folder, depth=0):
                result['metadata']['folder_count'] += 1
                for sub_folder in folder.sub_folders:
                    walk_folder(sub_folder, depth + 1)
                
                for message in folder.messages:
                    result['metadata']['message_count'] += 1
            
            walk_folder(pst.root_folder)
            
            pst.close()
            
        except ImportError:
            result['metadata']['requires_pypff'] = True
        except Exception as e:
            logger.warning(f"PST parsing failed: {e}")
        
        return result
    
    def _process_mbox(self, file_path: str, filename: str, result: Dict) -> Dict:
        """Process MBOX file."""
        try:
            import mailbox
            
            mbox = mailbox.mbox(file_path)
            
            result['metadata'] = {
                'message_count': len(mbox)
            }
            
            # Sample first few messages
            sample_messages = []
            for i, message in enumerate(mbox):
                if i >= 10:
                    break
                sample_messages.append({
                    'from': message.get('From', ''),
                    'subject': message.get('Subject', ''),
                    'date': message.get('Date', '')
                })
            
            result['sample_messages'] = sample_messages
            
        except Exception as e:
            logger.warning(f"MBOX parsing failed: {e}")
        
        return result


class SpecializedProcessor:
    """Main processor for specialized file types."""
    
    def __init__(self):
        """Initialize specialized processor with all sub-processors."""
        self.processors = {
            'cad': CADProcessor(),
            'ebook': EBookProcessor(),
            'medical': MedicalProcessor(),
            'geospatial': GeospatialProcessor(),
            'disk_image': DiskImageProcessor(),
            'email': EmailProcessor()
        }
        
        # All supported extensions
        self.all_extensions = []
        for processor in self.processors.values():
            self.all_extensions.extend(processor.SUPPORTED_FORMATS)
        self.all_extensions = list(set(self.all_extensions))
    
    def can_process(self, filename: str) -> bool:
        """Check if file can be processed."""
        ext = Path(filename).suffix.lower()
        return ext in self.all_extensions
    
    def get_file_type(self, filename: str) -> Optional[str]:
        """Get file type for filename."""
        ext = Path(filename).suffix.lower()
        for processor_type, processor in self.processors.items():
            if ext in processor.SUPPORTED_FORMATS:
                return processor_type
        return None
    
    def process(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process file using appropriate processor."""
        file_type = self.get_file_type(filename)
        
        if file_type is None:
            return {
                'error': f'Unsupported file type: {filename}',
                'supported_extensions': self.all_extensions
            }
        
        return self.processors[file_type].process(file_path, filename)


# Global instance
specialized_processor = SpecializedProcessor()
