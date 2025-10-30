"""
Intelligent file sorting system with type-specific sorting capabilities.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import re

from .models import File as FileModel, SortingRule
from .file_types import file_type_manager

logger = logging.getLogger(__name__)


class SmartSorter:
    """Intelligent file sorting with type-specific logic."""

    def __init__(self):
        """Initialize smart sorter."""
        self.sort_functions = self._initialize_sort_functions()

    def _initialize_sort_functions(self) -> Dict[str, Callable]:
        """Initialize sorting functions for different criteria."""
        return {
            "filename": self._sort_by_filename,
            "file_size": self._sort_by_file_size,
            "created_at": self._sort_by_created_at,
            "modified_time": self._sort_by_modified_time,
            "file_type": self._sort_by_file_type,
            "resolution": self._sort_by_resolution,
            "duration": self._sort_by_duration,
            "artist": self._sort_by_artist,
            "author": self._sort_by_author,
            "language": self._sort_by_language,
            "severity": self._sort_by_severity,
            "amount": self._sort_by_amount,
            "width": self._sort_by_width,
            "height": self._sort_by_height,
            "bitrate": self._sort_by_bitrate,
            "sample_rate": self._sort_by_sample_rate,
            "channels": self._sort_by_channels,
            "genre": self._sort_by_genre,
            "year": self._sort_by_year,
            "track_number": self._sort_by_track_number,
            "compression_ratio": self._sort_by_compression_ratio,
            "contents_count": self._sort_by_contents_count,
            "line_count": self._sort_by_line_count,
            "complexity": self._sort_by_complexity,
            "timestamp_range": self._sort_by_timestamp_range,
            "entries_count": self._sort_by_entries_count,
            "error_count": self._sort_by_error_count,
            "document_type": self._sort_by_document_type,
            "reference_number": self._sort_by_reference_number,
            "department": self._sort_by_department,
            "project": self._sort_by_project,
            "status": self._sort_by_status,
            "priority": self._sort_by_priority
        }

    def sort_files(self, files: List[FileModel], criteria: List[Dict[str, Any]]) -> List[FileModel]:
        """
        Sort files using multiple criteria with intelligent type-specific logic.

        Args:
            files: List of file objects to sort
            criteria: List of sorting criteria, each with 'field' and 'direction'

        Returns:
            Sorted list of files
        """
        if not criteria:
            return files

        sorted_files = files.copy()

        # Apply sorting criteria in order (primary, secondary, etc.)
        for criterion in criteria:
            field = criterion.get('field')
            direction = criterion.get('direction', 'asc')

            if field in self.sort_functions:
                try:
                    sorted_files = self.sort_functions[field](sorted_files, direction)
                except Exception as e:
                    logger.warning(f"Failed to sort by {field}: {e}")
                    continue

        return sorted_files

    def _sort_by_filename(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by filename alphabetically."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: f.filename.lower(), reverse=reverse)

    def _sort_by_file_size(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by file size."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: f.file_size, reverse=reverse)

    def _sort_by_created_at(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by creation date."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: f.created_at or datetime.min, reverse=reverse)

    def _sort_by_modified_time(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by modification time from metadata."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'modified_time', datetime.min), reverse=reverse)

    def _sort_by_file_type(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by file type."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: f.file_type, reverse=reverse)

    def _sort_by_resolution(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort images/videos by resolution (width × height)."""
        reverse = direction == 'desc'
        def get_resolution(file):
            width = self._get_metadata_value(file, 'width', 0)
            height = self._get_metadata_value(file, 'height', 0)
            return width * height
        return sorted(files, key=get_resolution, reverse=reverse)

    def _sort_by_width(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by image/video width."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'width', 0), reverse=reverse)

    def _sort_by_height(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort by image/video height."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'height', 0), reverse=reverse)

    def _sort_by_duration(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio/video by duration."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'duration', 0), reverse=reverse)

    def _sort_by_artist(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio files by artist."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'artist', '').lower(), reverse=reverse)

    def _sort_by_author(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort documents by author."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'author', '').lower(), reverse=reverse)

    def _sort_by_language(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort code files by programming language."""
        reverse = direction == 'desc'
        def get_language(file):
            # Try to detect language from extension
            ext = Path(file.filename).suffix.lower()
            lang_map = {
                '.py': 'Python', '.js': 'JavaScript', '.java': 'Java',
                '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.php': 'PHP',
                '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust'
            }
            return lang_map.get(ext, 'Unknown')
        return sorted(files, key=get_language, reverse=reverse)

    def _sort_by_severity(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort log files by severity level."""
        reverse = direction == 'desc'
        severity_order = {'debug': 1, 'info': 2, 'warning': 3, 'error': 4, 'critical': 5}

        def get_severity(file):
            severity = self._get_metadata_value(file, 'severity', 'info').lower()
            return severity_order.get(severity, 2)

        return sorted(files, key=get_severity, reverse=reverse)

    def _sort_by_amount(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by monetary amount."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'amount', 0), reverse=reverse)

    def _sort_by_bitrate(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio/video by bitrate."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'bitrate', 0), reverse=reverse)

    def _sort_by_sample_rate(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio by sample rate."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'sample_rate', 0), reverse=reverse)

    def _sort_by_channels(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio by number of channels."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'channels', 0), reverse=reverse)

    def _sort_by_genre(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio by genre."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'genre', '').lower(), reverse=reverse)

    def _sort_by_year(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio by release year."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'year', 0), reverse=reverse)

    def _sort_by_track_number(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort audio by track number."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'track_number', 0), reverse=reverse)

    def _sort_by_compression_ratio(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort archives by compression ratio."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'compression_ratio', 0), reverse=reverse)

    def _sort_by_contents_count(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort archives by number of contained files."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'contents_count', 0), reverse=reverse)

    def _sort_by_line_count(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort code files by line count."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'line_count', 0), reverse=reverse)

    def _sort_by_complexity(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort code files by complexity score."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'complexity', 0), reverse=reverse)

    def _sort_by_timestamp_range(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort logs by timestamp range."""
        reverse = direction == 'desc'
        def get_timestamp_range(file):
            # Extract earliest timestamp from log content
            content = file.content or ''
            timestamps = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', content)
            if timestamps:
                try:
                    return min(datetime.fromisoformat(ts.replace(' ', 'T')) for ts in timestamps)
                except:
                    pass
            return datetime.min
        return sorted(files, key=get_timestamp_range, reverse=reverse)

    def _sort_by_entries_count(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort logs by number of entries."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'entries_count', 0), reverse=reverse)

    def _sort_by_error_count(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort logs by error count."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'error_count', 0), reverse=reverse)

    def _sort_by_document_type(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by document type."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'document_type', '').lower(), reverse=reverse)

    def _sort_by_reference_number(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by reference number."""
        reverse = direction == 'desc'
        def get_ref_number(file):
            ref = self._get_metadata_value(file, 'reference_number', '')
            # Extract numeric part for sorting
            numbers = re.findall(r'\d+', ref)
            return int(numbers[0]) if numbers else 0
        return sorted(files, key=get_ref_number, reverse=reverse)

    def _sort_by_department(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by department."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'department', '').lower(), reverse=reverse)

    def _sort_by_project(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by project."""
        reverse = direction == 'desc'
        return sorted(files, key=lambda f: self._get_metadata_value(f, 'project', '').lower(), reverse=reverse)

    def _sort_by_status(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by status."""
        reverse = direction == 'desc'
        status_order = {'draft': 1, 'pending': 2, 'approved': 3, 'completed': 4, 'archived': 5}
        def get_status_order(file):
            status = self._get_metadata_value(file, 'status', 'draft').lower()
            return status_order.get(status, 1)
        return sorted(files, key=get_status_order, reverse=reverse)

    def _sort_by_priority(self, files: List[FileModel], direction: str) -> List[FileModel]:
        """Sort business files by priority."""
        reverse = direction == 'desc'
        priority_order = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        def get_priority_order(file):
            priority = self._get_metadata_value(file, 'priority', 'medium').lower()
            return priority_order.get(priority, 2)
        return sorted(files, key=get_priority_order, reverse=reverse)

    def _get_metadata_value(self, file: FileModel, key: str, default: Any) -> Any:
        """Safely get metadata value from file."""
        if not file.metadata:
            return default
        return file.metadata.get(key, default)

    def get_sorting_suggestions(self, file_type: str) -> List[Dict[str, Any]]:
        """Get intelligent sorting suggestions for a file type."""
        return file_type_manager.suggest_sorting_rules(file_type)

    def create_smart_sorting_rule(self, file_type: str, rule_name: str) -> Optional[Dict[str, Any]]:
        """Create a smart sorting rule based on file type characteristics."""
        suggestions = self.get_sorting_suggestions(file_type)
        for suggestion in suggestions:
            if suggestion['name'].lower() == rule_name.lower():
                return {
                    'name': suggestion['name'],
                    'description': suggestion['description'],
                    'conditions': [{'type': 'file_type', 'file_type': file_type}],
                    'actions': [{
                        'type': 'sort',
                        'criteria': suggestion['criteria']
                    }]
                }
        return None

    def apply_type_specific_sorting(self, files: List[FileModel], file_type: str) -> List[FileModel]:
        """Apply intelligent type-specific sorting."""
        if not files:
            return files

        # Get the most appropriate sorting for this file type
        suggestions = self.get_sorting_suggestions(file_type)
        if suggestions:
            # Use the first (most recommended) suggestion
            primary_suggestion = suggestions[0]
            criteria = primary_suggestion.get('criteria', [])
            return self.sort_files(files, criteria)

        # Fallback to alphabetical sorting
        return self._sort_by_filename(files, 'asc')


# Global smart sorter instance
smart_sorter = SmartSorter()