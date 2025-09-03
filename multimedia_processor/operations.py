# multimedia_processor/operations.py
from .api import MediaProcessorFactory, MediaProcessingConfig, MediaType, ProcessingStrategy, FileMetadata
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import json
from datetime import datetime

class AdvancedMediaOperations:
    """Advanced operations for multimedia processing"""
    
    def __init__(self):
        self.factory = MediaProcessorFactory()
    
    def batch_process_files(self, file_paths: List[Path], 
                          config: MediaProcessingConfig) -> Dict[Path, Dict[str, Any]]:
        """Process multiple files in batch"""
        results = {}
        
        if config.parallel_processing:
            results = self._process_parallel(file_paths, config)
        else:
            results = self._process_sequential(file_paths, config)
        
        return results
    
    def _process_parallel(self, file_paths: List[Path], 
                        config: MediaProcessingConfig) -> Dict[Path, Dict[str, Any]]:
        """Process files in parallel"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_file, file_path, config): file_path
                for file_path in file_paths
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_file), 
                             total=len(file_paths), desc="Processing files"):
                file_path = future_to_file[future]
                try:
                    results[file_path] = future.result()
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results[file_path] = {'error': str(e)}
        
        return results
    
    def _process_sequential(self, file_paths: List[Path], 
                          config: MediaProcessingConfig) -> Dict[Path, Dict[str, Any]]:
        """Process files sequentially"""
        results = {}
        
        for file_path in tqdm(file_paths, desc="Processing files"):
            try:
                results[file_path] = self._process_single_file(file_path, config)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results[file_path] = {'error': str(e)}
        
        return results
    
    def _process_single_file(self, file_path: Path, 
                           config: MediaProcessingConfig) -> Dict[str, Any]:
        """Process a single file"""
        processor = self.factory.create_processor(file_path)
        
        result = {
            'metadata': processor.extract_metadata(file_path).__dict__,
            'analysis': processor.analyze_content(file_path, config),
            'validation': processor.validate_file(file_path),
            'processed_at': datetime.now().isoformat()
        }
        
        return result
    
    def find_duplicates(self, directory: Path, 
                       config: MediaProcessingConfig) -> Dict[str, List[Path]]:
        """Find duplicate files in a directory"""
        all_files = self._find_files_recursive(directory)
        duplicates = {}
        
        for media_type in MediaType:
            type_files = [f for f in all_files if 
                         self.factory.detect_media_type(f) == media_type]
            
            if type_files:
                processor = self.factory.create_processor(type_files[0])
                unique_files = processor.deduplicate(type_files, config)
                
                if len(unique_files) < len(type_files):
                    duplicates[media_type.value] = [
                        f for f in type_files if f not in unique_files
                    ]
        
        return duplicates
    
    def convert_batch(self, file_paths: List[Path], output_format: str,
                     config: MediaProcessingConfig) -> Dict[Path, Path]:
        """Convert multiple files to different format"""
        results = {}
        
        for file_path in tqdm(file_paths, desc="Converting files"):
            try:
                processor = self.factory.create_processor(file_path)
                output_path = processor.convert_format(file_path, output_format, config)
                results[file_path] = output_path
            except Exception as e:
                logger.error(f"Conversion failed for {file_path}: {e}")
                results[file_path] = None
        
        return results
    
    def _find_files_recursive(self, directory: Path) -> List[Path]:
        """Find all files recursively in directory"""
        files = []
        for pattern in ['*.*', '*/*.*', '*/*/*.*']:  # Limit depth
            files.extend(directory.glob(pattern))
        return [f for f in files if f.is_file()]
    
    def generate_report(self, processing_results: Dict[Path, Dict[str, Any]], 
                       output_path: Path) -> None:
        """Generate comprehensive processing report"""
        report = {
            'summary': self._generate_summary(processing_results),
            'details': processing_results,
            'generated_at': datetime.now().isoformat(),
            'total_files': len(processing_results)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
    
    def _generate_summary(self, results: Dict[Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            'total_size': 0,
            'by_media_type': {},
            'processing_errors': 0,
            'earliest_created': None,
            'latest_modified': None
        }
        
        for file_data in results.values():
            if 'error' in file_data:
                summary['processing_errors'] += 1
                continue
            
            metadata = file_data.get('metadata', {})
            file_type = metadata.get('file_type')
            file_size = metadata.get('file_size', 0)
            
            summary['total_size'] += file_size
            
            if file_type:
                if file_type not in summary['by_media_type']:
                    summary['by_media_type'][file_type] = {
                        'count': 0, 'total_size': 0
                    }
                summary['by_media_type'][file_type]['count'] += 1
                summary['by_media_type'][file_type]['total_size'] += file_size
            
            # Track dates
            created = metadata.get('created')
            modified = metadata.get('modified')
            
            if created:
                if summary['earliest_created'] is None or created < summary['earliest_created']:
                    summary['earliest_created'] = created
            
            if modified:
                if summary['latest_modified'] is None or modified > summary['latest_modified']:
                    summary['latest_modified'] = modified
        
        return summary