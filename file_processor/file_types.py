"""
File type definitions and sorting configurations for comprehensive file processing.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path


class FileTypeManager:
    """Manages file type definitions and sorting capabilities."""

    def __init__(self):
        """Initialize file type manager with comprehensive type definitions."""
        self.file_types = self._initialize_file_types()
        self.sorting_criteria = self._initialize_sorting_criteria()

    def _initialize_file_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive file type definitions."""
        return {
            # Documents
            "document": {
                "name": "Documents",
                "description": "Word files, PDFs, spreadsheets, presentations, text files",
                "extensions": [
                    ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx",
                    ".txt", ".rtf", ".odt", ".ods", ".odp", ".csv", ".tsv"
                ],
                "mime_types": [
                    "application/pdf", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-powerpoint",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "text/plain", "text/csv", "text/rtf"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "author", "title", "subject", "keywords", "language"
                ],
                "metadata_extractors": ["document_metadata", "text_content"],
                "processing_priority": "high"
            },

            # Images
            "image": {
                "name": "Images",
                "description": "Photos and graphics in various formats",
                "extensions": [
                    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
                    ".webp", ".svg", ".ico", ".raw", ".cr2", ".nef", ".arw"
                ],
                "mime_types": [
                    "image/jpeg", "image/png", "image/gif", "image/bmp",
                    "image/tiff", "image/webp", "image/svg+xml"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "width", "height", "resolution", "color_depth", "camera_model",
                    "iso", "aperture", "shutter_speed", "focal_length"
                ],
                "metadata_extractors": ["image_metadata", "exif_data"],
                "processing_priority": "medium"
            },

            # Videos
            "video": {
                "name": "Videos",
                "description": "Video files in various formats",
                "extensions": [
                    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
                    ".m4v", ".3gp", ".mpg", ".mpeg", ".ts", ".mts"
                ],
                "mime_types": [
                    "video/mp4", "video/avi", "video/quicktime", "video/x-matroska",
                    "video/webm", "video/mpeg"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "duration", "width", "height", "frame_rate", "bitrate",
                    "codec", "audio_channels", "audio_sample_rate"
                ],
                "metadata_extractors": ["video_metadata", "audio_metadata"],
                "processing_priority": "high"
            },

            # Audio
            "audio": {
                "name": "Audio Files",
                "description": "Music and audio recordings",
                "extensions": [
                    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
                    ".aiff", ".au", ".ra", ".ape", ".opus"
                ],
                "mime_types": [
                    "audio/mpeg", "audio/wav", "audio/flac", "audio/aac",
                    "audio/ogg", "audio/x-ms-wma"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "duration", "bitrate", "sample_rate", "channels",
                    "artist", "album", "title", "genre", "year", "track_number"
                ],
                "metadata_extractors": ["audio_metadata", "id3_tags"],
                "processing_priority": "medium"
            },

            # Archives
            "archive": {
                "name": "Archives",
                "description": "Compressed and archived files",
                "extensions": [
                    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
                    ".tgz", ".tbz2", ".txz", ".cab", ".iso"
                ],
                "mime_types": [
                    "application/zip", "application/x-rar-compressed",
                    "application/x-7z-compressed", "application/x-tar",
                    "application/gzip", "application/x-bzip2"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "compression_ratio", "contents_count", "archive_type"
                ],
                "metadata_extractors": ["archive_metadata", "contents_list"],
                "processing_priority": "low"
            },

            # Code and Scripts
            "code": {
                "name": "Code & Scripts",
                "description": "Source code and script files",
                "extensions": [
                    ".py", ".js", ".java", ".cpp", ".c", ".cs", ".php", ".rb",
                    ".go", ".rs", ".swift", ".kt", ".scala", ".clj", ".hs",
                    ".sh", ".bash", ".ps1", ".sql", ".html", ".css", ".xml",
                    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"
                ],
                "mime_types": [
                    "text/x-python", "application/javascript", "text/x-java-source",
                    "text/x-c++src", "text/x-csrc", "text/x-csharp", "application/x-php",
                    "application/x-ruby", "text/x-go", "text/x-rust",
                    "text/html", "text/css", "application/json", "application/xml"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "language", "project", "filename_pattern", "line_count",
                    "complexity", "imports", "functions", "classes"
                ],
                "metadata_extractors": ["code_metadata", "syntax_analysis"],
                "processing_priority": "medium"
            },

            # Logs
            "log": {
                "name": "Log Files",
                "description": "Application and system log files",
                "extensions": [
                    ".log", ".txt", ".out", ".err", ".debug", ".trace",
                    ".access", ".error", ".syslog", ".journal"
                ],
                "mime_types": ["text/plain", "text/x-log"],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "timestamp_range", "severity_levels", "source",
                    "log_type", "entries_count", "error_count"
                ],
                "metadata_extractors": ["log_metadata", "log_analysis"],
                "processing_priority": "low"
            },

            # Business Files
            "business": {
                "name": "Business Files",
                "description": "Reports, invoices, and business documents",
                "extensions": [
                    ".xlsx", ".xls", ".pdf", ".docx", ".doc", ".pptx", ".ppt",
                    ".csv", ".xml", ".json", ".txt", ".rtf"
                ],
                "mime_types": [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel", "application/pdf",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "text/csv", "application/xml", "application/json"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "document_type", "date_range", "amount", "reference_number",
                    "department", "project", "status", "priority"
                ],
                "metadata_extractors": ["business_metadata", "content_analysis"],
                "processing_priority": "high"
            },

            # CAD/Engineering Files
            "cad": {
                "name": "CAD/Engineering Files",
                "description": "CAD drawings and 3D models (DWG, DXF, STEP, IGES)",
                "extensions": [
                    ".dwg", ".dxf", ".step", ".stp", ".iges"
                ],
                "mime_types": [
                    "application/acad", "application/dxf", "application/step",
                    "application/iges", "model/iges", "model/step"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "entities_count", "layers_count", "dxf_version", "schema"
                ],
                "metadata_extractors": ["cad_metadata", "bom_extraction", "dimension_extraction"],
                "processing_priority": "high"
            },

            # E-books & Structured Documents
            "ebook": {
                "name": "E-books & Documents",
                "description": "E-books and structured documents (EPUB, MOBI, FB2, HTML)",
                "extensions": [
                    ".epub", ".mobi", ".fb2", ".html", ".xhtml", ".chm"
                ],
                "mime_types": [
                    "application/epub+zip", "application/x-mobipocket-ebook",
                    "application/fb2+xml", "text/html", "application/xhtml+xml",
                    "application/vnd.ms-htmlhelp"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "title", "author", "language", "chapters_count"
                ],
                "metadata_extractors": ["ebook_metadata", "toc_extraction", "text_content"],
                "processing_priority": "medium"
            },

            # Medical/Compliance Files
            "medical": {
                "name": "Medical & Compliance Files",
                "description": "Medical imaging and compliance documents (DICOM, HL7, PDF/A)",
                "extensions": [
                    ".dcm", ".dicom", ".hl7", ".xhl7", ".pdfa", ".pdf"
                ],
                "mime_types": [
                    "application/dicom", "application/hl7-v2", "application/hl7-v2+xml",
                    "application/pdfa", "application/pdf"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "patient_id", "study_date", "modality", "phi_detected",
                    "hipaa_compliant"
                ],
                "metadata_extractors": ["medical_metadata", "phi_detection", "compliance_validation"],
                "processing_priority": "critical"
            },

            # Geospatial Files
            "geospatial": {
                "name": "Geospatial Files",
                "description": "Geographic and spatial data (Shapefile, GeoJSON, KML, GPX)",
                "extensions": [
                    ".shp", ".geojson", ".svg", ".kml", ".kmz", ".gpx", ".gml"
                ],
                "mime_types": [
                    "application/shapefile", "application/geo+json", "image/svg+xml",
                    "application/vnd.google-earth.kml+xml",
                    "application/vnd.google-earth.kmz", "application/gpx+xml",
                    "application/gml+xml"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "features_count", "projection", "bounds", "layers_count"
                ],
                "metadata_extractors": ["geospatial_metadata", "bounds_extraction", "projection_info"],
                "processing_priority": "high"
            },

            # Disk Images
            "disk_image": {
                "name": "Disk Images",
                "description": "Disk image files and virtual disks (ISO, DMG, VHD, VMDK)",
                "extensions": [
                    ".dmg", ".iso", ".img", ".vhd", ".vmdk", ".bin"
                ],
                "mime_types": [
                    "application/x-apple-diskimage", "application/x-iso9660-image",
                    "application/x-raw-disk-image", "application/x-virtualbox-vhd",
                    "application/x-virtualbox-vmdk"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "total_files", "total_dirs", "filesystem", "format"
                ],
                "metadata_extractors": ["disk_metadata", "filesystem_detection", "contents_listing"],
                "processing_priority": "low"
            },

            # Email Files
            "email": {
                "name": "Email Files",
                "description": "Email files and archives (EML, MSG, PST, MBOX)",
                "extensions": [
                    ".eml", ".msg", ".pst", ".mbox"
                ],
                "mime_types": [
                    "message/rfc822", "application/vnd.ms-outlook", "application/mbox"
                ],
                "sorting_fields": [
                    "file_type", "file_size", "created_at", "modified_time",
                    "sender", "recipient", "date", "attachments_count",
                    "message_count"
                ],
                "metadata_extractors": ["email_metadata", "attachment_extraction", "sentiment_analysis"],
                "processing_priority": "medium"
            }
        }

    def _initialize_sorting_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sorting criteria for different file types."""
        return {
            "alphabetical": {
                "name": "Alphabetical",
                "description": "Sort by filename alphabetically",
                "field": "filename",
                "direction": "asc",
                "applicable_types": ["all"]
            },
            "date_created": {
                "name": "Date Created",
                "description": "Sort by file creation date",
                "field": "created_at",
                "direction": "desc",
                "applicable_types": ["all"]
            },
            "date_modified": {
                "name": "Date Modified",
                "description": "Sort by file modification date",
                "field": "modified_time",
                "direction": "desc",
                "applicable_types": ["all"]
            },
            "file_size": {
                "name": "File Size",
                "description": "Sort by file size",
                "field": "file_size",
                "direction": "desc",
                "applicable_types": ["all"]
            },
            "file_type": {
                "name": "File Type",
                "description": "Sort by file extension/type",
                "field": "file_type",
                "direction": "asc",
                "applicable_types": ["all"]
            },
            "resolution": {
                "name": "Resolution",
                "description": "Sort images by resolution (width × height)",
                "field": "resolution",
                "direction": "desc",
                "applicable_types": ["image", "video"]
            },
            "duration": {
                "name": "Duration",
                "description": "Sort audio/video by duration",
                "field": "duration",
                "direction": "desc",
                "applicable_types": ["audio", "video"]
            },
            "artist": {
                "name": "Artist",
                "description": "Sort audio files by artist",
                "field": "artist",
                "direction": "asc",
                "applicable_types": ["audio"]
            },
            "author": {
                "name": "Author",
                "description": "Sort documents by author",
                "field": "author",
                "direction": "asc",
                "applicable_types": ["document", "business"]
            },
            "language": {
                "name": "Programming Language",
                "description": "Sort code files by programming language",
                "field": "language",
                "direction": "asc",
                "applicable_types": ["code"]
            },
            "severity": {
                "name": "Log Severity",
                "description": "Sort log files by severity level",
                "field": "severity",
                "direction": "desc",
                "applicable_types": ["log"]
            },
            "amount": {
                "name": "Amount",
                "description": "Sort business files by monetary amount",
                "field": "amount",
                "direction": "desc",
                "applicable_types": ["business"]
            }
        }

    def get_file_type(self, filename: str, mime_type: Optional[str] = None) -> str:
        """Determine file type from filename and MIME type."""
        ext = Path(filename).suffix.lower()

        # First try extension matching
        for file_type, config in self.file_types.items():
            if ext in config["extensions"]:
                return file_type

        # Fallback to MIME type matching
        if mime_type:
            for file_type, config in self.file_types.items():
                if mime_type in config["mime_types"]:
                    return file_type

        return "unknown"

    def get_sorting_options(self, file_type: str) -> List[Dict[str, Any]]:
        """Get available sorting options for a file type."""
        options = []

        for criterion_key, criterion in self.sorting_criteria.items():
            if "all" in criterion["applicable_types"] or file_type in criterion["applicable_types"]:
                options.append({
                    "key": criterion_key,
                    "name": criterion["name"],
                    "description": criterion["description"],
                    "field": criterion["field"],
                    "direction": criterion["direction"]
                })

        return options

    def get_file_type_config(self, file_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific file type."""
        return self.file_types.get(file_type)

    def get_all_file_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all file type configurations."""
        return self.file_types

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions."""
        extensions = []
        for config in self.file_types.values():
            extensions.extend(config["extensions"])
        return list(set(extensions))  # Remove duplicates

    def validate_file_type(self, filename: str, mime_type: Optional[str] = None) -> bool:
        """Validate if file type is supported."""
        file_type = self.get_file_type(filename, mime_type)
        return file_type != "unknown"

    def get_processing_priority(self, file_type: str) -> str:
        """Get processing priority for file type."""
        config = self.get_file_type_config(file_type)
        return config.get("processing_priority", "medium") if config else "low"

    def get_metadata_extractors(self, file_type: str) -> List[str]:
        """Get metadata extractors for file type."""
        config = self.get_file_type_config(file_type)
        return config.get("metadata_extractors", []) if config else []

    def suggest_sorting_rules(self, file_type: str) -> List[Dict[str, Any]]:
        """Suggest intelligent sorting rules based on file type."""
        suggestions = []

        if file_type == "document":
            suggestions.extend([
                {
                    "name": "Recent Documents First",
                    "criteria": [{"field": "created_at", "direction": "desc"}],
                    "description": "Sort documents by creation date, newest first"
                },
                {
                    "name": "By Author",
                    "criteria": [{"field": "author", "direction": "asc"}],
                    "description": "Group documents by author"
                }
            ])

        elif file_type == "image":
            suggestions.extend([
                {
                    "name": "High Resolution First",
                    "criteria": [{"field": "resolution", "direction": "desc"}],
                    "description": "Sort images by resolution, highest first"
                },
                {
                    "name": "Recent Photos",
                    "criteria": [{"field": "created_at", "direction": "desc"}],
                    "description": "Sort photos by capture date, newest first"
                }
            ])

        elif file_type == "video":
            suggestions.extend([
                {
                    "name": "Longest Videos First",
                    "criteria": [{"field": "duration", "direction": "desc"}],
                    "description": "Sort videos by duration, longest first"
                },
                {
                    "name": "High Quality First",
                    "criteria": [{"field": "resolution", "direction": "desc"}],
                    "description": "Sort videos by resolution quality"
                }
            ])

        elif file_type == "audio":
            suggestions.extend([
                {
                    "name": "By Artist",
                    "criteria": [{"field": "artist", "direction": "asc"}],
                    "description": "Group audio files by artist"
                },
                {
                    "name": "Longest Tracks",
                    "criteria": [{"field": "duration", "direction": "desc"}],
                    "description": "Sort by track duration, longest first"
                }
            ])

        elif file_type == "code":
            suggestions.extend([
                {
                    "name": "By Language",
                    "criteria": [{"field": "language", "direction": "asc"}],
                    "description": "Group code files by programming language"
                },
                {
                    "name": "Recently Modified",
                    "criteria": [{"field": "modified_time", "direction": "desc"}],
                    "description": "Sort by last modification date"
                }
            ])

        elif file_type == "business":
            suggestions.extend([
                {
                    "name": "Recent Documents",
                    "criteria": [{"field": "created_at", "direction": "desc"}],
                    "description": "Sort business documents by date, newest first"
                },
                {
                    "name": "By Amount",
                    "criteria": [{"field": "amount", "direction": "desc"}],
                    "description": "Sort financial documents by amount"
                }
            ])

        # Add common suggestions for all types
        suggestions.extend([
            {
                "name": "Alphabetical",
                "criteria": [{"field": "filename", "direction": "asc"}],
                "description": "Sort alphabetically by filename"
            },
            {
                "name": "Largest Files First",
                "criteria": [{"field": "file_size", "direction": "desc"}],
                "description": "Sort by file size, largest first"
            }
        ])

        return suggestions


# Global file type manager instance
file_type_manager = FileTypeManager()