import os
import shutil
import logging
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import hashlib
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime

# Constants
DEFAULT_CATEGORIES = {
    'audios': ['.mp3', '.ogg', '.wav', '.flac', '.aac'],
    'videos': ['.webm', '.mov', '.mp4', '.mkv', '.avi', '.flv'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff'],
    'documents': ['.txt', '.doc', '.docx', '.xlsx', '.pptx', '.pdf', '.csv', '.rtf'],
    'formats': ['.sql', '.json', '.xml', '.yaml', '.yml'],
    'scripts': ['.ps1', '.sh', '.py', '.js', '.rb', '.php', '.pl', '.bat', '.cmd'],
    'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'executables': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm'],
    'general': []
}

# Data Classes
@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    modified_time: float
    created_time: float
    checksum: Optional[str] = None

    @property
    def extension(self) -> str:
        return os.path.splitext(self.name)[1].lower()

    def calculate_checksum(self, algorithm='md5', chunk_size=8192) -> None:
        """Calculate file checksum using specified algorithm"""
        hash_algo = hashlib.new(algorithm)
        with open(self.path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_algo.update(chunk)
        self.checksum = hash_algo.hexdigest()

class DirectoryManager:
    """Handles directory operations with thread safety"""
    
    def __init__(self, path: str):
        self.path = path
    
    def create(self) -> bool:
        """Create directory with parents if not exists"""
        try:
            os.makedirs(self.path, exist_ok=True)
            os.chmod(self.path, 0o755)  # Set appropriate permissions
            return True
        except (OSError, PermissionError) as e:
            logging.error(f"Failed to create directory {self.path}: {str(e)}")
            return False
    
    def is_empty(self) -> bool:
        """Check if directory is empty"""
        try:
            return not bool(os.listdir(self.path))
        except (OSError, PermissionError):
            return False

class FileOrganizer:
    """Main file organization class with industrial-grade features"""
    
    def __init__(self, source_path: str, destination_path: str, config: Optional[Dict] = None):
        self.source_path = os.path.abspath(source_path)
        self.destination_path = os.path.abspath(destination_path)
        self.categories = config if config else DEFAULT_CATEGORIES
        self.file_counters = {category: 0 for category in self.categories}
        self.error_count = 0
        self.skip_count = 0
        self.overwrite_count = 0
        self.log_file = os.path.join(destination_path, 'file_organizer.log')
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """Configure logging with both console and file output"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def validate_paths(self) -> bool:
        """Validate source and destination paths"""
        if not os.path.exists(self.source_path):
            logging.error(f"Source path does not exist: {self.source_path}")
            return False
        
        if not os.path.isdir(self.source_path):
            logging.error(f"Source path is not a directory: {self.source_path}")
            return False
        
        try:
            DirectoryManager(self.destination_path).create()
        except Exception as e:
            logging.error(f"Failed to validate/create destination path: {str(e)}")
            return False
        
        if os.path.samefile(self.source_path, self.destination_path):
            logging.error("Source and destination paths cannot be the same")
            return False
        
        return True
    
    def prepare_destination(self) -> None:
        """Create all category directories in destination"""
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for category in self.categories:
                    dir_path = os.path.join(self.destination_path, category)
                    futures.append(executor.submit(DirectoryManager(dir_path).create))
                
                for future in futures:
                    if not future.result():
                        raise RuntimeError("Failed to create one or more directories")
        except Exception as e:
            logging.error(f"Failed to prepare destination: {str(e)}")
            raise
    
    def get_file_info(self, file_name: str) -> Optional[FileInfo]:
        """Get detailed file information"""
        file_path = os.path.join(self.source_path, file_name)
        try:
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                file_info = FileInfo(
                    name=file_name,
                    path=file_path,
                    size=stat.st_size,
                    modified_time=stat.st_mtime,
                    created_time=stat.st_ctime
                )
                # Only calculate checksum for files larger than 1MB
                if file_info.size > 1024 * 1024:
                    file_info.calculate_checksum()
                return file_info
            return None
        except (OSError, PermissionError) as e:
            logging.warning(f"Could not access file {file_name}: {str(e)}")
            self.error_count += 1
            return None
    
    def categorize_file(self, file_info: FileInfo) -> str:
        """Determine the category for a file based on its extension"""
        for category, extensions in self.categories.items():
            if file_info.extension in extensions:
                return category
        return 'general'
    
    def handle_file_conflict(self, dest_path: str, file_info: FileInfo) -> bool:
        """
        Handle file naming conflicts with multiple resolution strategies
        Returns True if file should be overwritten/moved, False if skipped
        """
        if not os.path.exists(dest_path):
            return True
        
        # Compare files
        dest_file_info = self.get_file_info(os.path.basename(dest_path))
        if dest_file_info and file_info.checksum and dest_file_info.checksum:
            if file_info.checksum == dest_file_info.checksum:
                logging.info(f"Duplicate file detected (same checksum): {file_info.name}")
                self.skip_count += 1
                return False
        
        # Resolution strategies (could be configurable)
        resolution = 'rename'  # or 'overwrite', 'skip'
        
        if resolution == 'rename':
            base, ext = os.path.splitext(file_info.name)
            counter = 1
            while True:
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(os.path.dirname(dest_path), new_name)
                if not os.path.exists(new_path):
                    file_info.name = new_name
                    return True
                counter += 1
        elif resolution == 'overwrite':
            self.overwrite_count += 1
            return True
        else:  # skip
            self.skip_count += 1
            return False
    
    def move_file(self, file_info: FileInfo, category: str) -> bool:
        """Safely move file to destination category"""
        dest_dir = os.path.join(self.destination_path, category)
        dest_path = os.path.join(dest_dir, file_info.name)
        
        if not self.handle_file_conflict(dest_path, file_info):
            return False
        
        try:
            # Use copy + delete for more reliable moving
            shutil.copy2(file_info.path, dest_path)
            os.remove(file_info.path)
            
            # Preserve original timestamps
            os.utime(dest_path, (file_info.created_time, file_info.modified_time))
            
            self.file_counters[category] += 1
            logging.info(f"Moved {file_info.name} to {category}")
            return True
        except Exception as e:
            logging.error(f"Failed to move {file_info.name}: {str(e)}")
            self.error_count += 1
            return False
    
    def process_files(self, max_workers: int = 4) -> None:
        """Process all files in source directory with parallel processing"""
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for file_name in os.listdir(self.source_path):
                    futures.append(executor.submit(self.get_file_info, file_name))
                
                for future in futures:
                    file_info = future.result()
                    if file_info:
                        category = self.categorize_file(file_info)
                        self.move_file(file_info, category)
        except Exception as e:
            logging.error(f"Error during file processing: {str(e)}")
            raise
    
    def generate_report(self) -> None:
        """Generate a summary report of the operation"""
        report = [
            "\n=== File Organization Report ===",
            f"Source: {self.source_path}",
            f"Destination: {self.destination_path}",
            f"Processing time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\nFiles Processed by Category:"
        ]
        
        for category, count in self.file_counters.items():
            report.append(f"{category.capitalize()}: {count}")
        
        report.extend([
            "\nStatistics:",
            f"Total files moved: {sum(self.file_counters.values())}",
            f"Files skipped: {self.skip_count}",
            f"Files overwritten: {self.overwrite_count}",
            f"Errors encountered: {self.error_count}",
            "\nOperation completed."
        ])
        
        report_text = "\n".join(report)
        logging.info(report_text)
        
        # Write report to file
        report_file = os.path.join(self.destination_path, 'organization_report.txt')
        with open(report_file, 'w') as f:
            f.write(report_text)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Industrial-grade file organization tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'source',
        help="Source directory containing files to organize"
    )
    
    parser.add_argument(
        'destination',
        help="Destination directory where files will be organized"
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help="Number of worker threads for parallel processing"
    )
    
    parser.add_argument(
        '--config',
        help="Path to JSON configuration file for custom categories"
    )
    
    return parser.parse_args()

def main() -> None:
    """Main entry point for the file organizer"""
    args = parse_arguments()
    
    try:
        # Load custom config if provided
        config = None
        if args.config:
            import json
            with open(args.config) as f:
                config = json.load(f)
        
        organizer = FileOrganizer(args.source, args.destination, config)
        
        if not organizer.validate_paths():
            sys.exit(1)
        
        organizer.prepare_destination()
        organizer.process_files(max_workers=args.workers)
        organizer.generate_report()
        
        if organizer.error_count > 0:
            sys.exit(2)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
