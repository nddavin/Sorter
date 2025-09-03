# multimedia_processor/main.py
from .api import MediaProcessorFactory, MediaProcessingConfig, MediaType, ProcessingStrategy, ProcessingLevel
from .operations import AdvancedMediaOperations
from typing import List, Dict, Any, Optional
from pathlib import Path

class UniversalMediaProcessor:
    """Main API interface for multimedia processing"""
    
    def __init__(self):
        self.factory = MediaProcessorFactory()
        self.advanced_ops = AdvancedMediaOperations()
    
    def process_file(self, file_path: Path, 
                    config: Optional[MediaProcessingConfig] = None) -> Dict[str, Any]:
        """Process a single multimedia file"""
        if config is None:
            config = MediaProcessingConfig()
        
        processor = self.factory.create_processor(file_path)
        
        return {
            'metadata': processor.extract_metadata(file_path).__dict__,
            'content_analysis': processor.analyze_content(file_path, config),
            'is_valid': processor.validate_file(file_path),
            'media_type': self.factory.detect_media_type(file_path).value
        }
    
    def process_directory(self, directory: Path, 
                         config: Optional[MediaProcessingConfig] = None) -> Dict[Path, Dict[str, Any]]:
        """Process all files in a directory"""
        if config is None:
            config = MediaProcessingConfig()
        
        all_files = self._get_all_files(directory)
        return self.advanced_ops.batch_process_files(all_files, config)
    
    def find_duplicates(self, directory: Path, 
                       config: Optional[MediaProcessingConfig] = None) -> Dict[str, List[Path]]:
        """Find duplicate files in directory"""
        if config is None:
            config = MediaProcessingConfig()
        
        return self.advanced_ops.find_duplicates(directory, config)
    
    def convert_files(self, file_paths: List[Path], output_format: str,
                     config: Optional[MediaProcessingConfig] = None) -> Dict[Path, Path]:
        """Convert files to different format"""
        if config is None:
            config = MediaProcessingConfig()
            config.target_directory = file_paths[0].parent if file_paths else Path.cwd()
        
        return self.advanced_ops.convert_batch(file_paths, output_format, config)
    
    def generate_report(self, directory: Path, 
                       output_file: Path,
                       config: Optional[MediaProcessingConfig] = None) -> None:
        """Generate comprehensive media analysis report"""
        if config is None:
            config = MediaProcessingConfig()
        
        results = self.process_directory(directory, config)
        self.advanced_ops.generate_report(results, output_file)
    
    def _get_all_files(self, directory: Path) -> List[Path]:
        """Get all files from directory recursively"""
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")
        
        return list(directory.rglob('*.*'))

# Singleton instance
media_processor = UniversalMediaProcessor()

# Shortcut functions
def process_media(file_path: Path, **kwargs) -> Dict[str, Any]:
    config = MediaProcessingConfig(**kwargs)
    return media_processor.process_file(file_path, config)

def process_directory_media(directory: Path, **kwargs) -> Dict[Path, Dict[str, Any]]:
    config = MediaProcessingConfig(**kwargs)
    return media_processor.process_directory(directory, config)

def find_media_duplicates(directory: Path, **kwargs) -> Dict[str, List[Path]]:
    config = MediaProcessingConfig(**kwargs)
    return media_processor.find_duplicates(directory, config)