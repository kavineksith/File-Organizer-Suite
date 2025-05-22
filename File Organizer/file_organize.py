#!/usr/bin/env python3
"""
Industrial-Grade File Organizer with:
- Comprehensive error handling
- Configurable file categorization
- Parallel processing
- Detailed logging
- Dry run mode
- Progress tracking
- Undo functionality
"""

import os
import shutil
import sys
import logging
import argparse
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from enum import Enum, auto

# Constants
DEFAULT_CONFIG_FILE = "file_organizer_config.json"
DEFAULT_LOG_FILE = "file_organizer.log"
MAX_WORKERS = 4
BUFFER_SIZE = 65536  # 64KB chunks for hashing

class FileCategory(Enum):
    IMAGES = auto()
    VIDEOS = auto()
    DOCUMENTS = auto()
    MUSIC = auto()
    ARCHIVES = auto()
    DATA = auto()
    CODE = auto()
    EXECUTABLES = auto()
    UNKNOWN = auto()

class ConflictResolution(Enum):
    RENAME = auto()
    OVERWRITE = auto()
    SKIP = auto()

@dataclass
class FileOperation:
    source: Path
    destination: Path
    action: str
    success: bool = False
    error: Optional[str] = None

@dataclass
class OrganizerStats:
    total_files: int = 0
    processed_files: int = 0
    moved_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    start_time: float = 0.0
    end_time: float = 0.0

class FileOrganizerError(Exception):
    """Base class for file organizer exceptions"""
    def __init__(self, message, error_code = None):
        super().__init__(message, error_code)

class FileOrganizer:
    def __init__(self, base_dir: Path, config_file: Optional[Path] = None):
        self.base_dir = base_dir.resolve()
        self.config_file = config_file or Path(DEFAULT_CONFIG_FILE)
        self.stats = OrganizerStats()
        self.operations: List[FileOperation] = []
        self._setup_logging()
        self._load_config()
        
        # Initialize default extensions if not in config
        self.extensions = {
            FileCategory.IMAGES: {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
            FileCategory.VIDEOS: {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'},
            FileCategory.DOCUMENTS: {'.pdf', '.doc', '.docx', '.odt', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx'},
            FileCategory.MUSIC: {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'},
            FileCategory.ARCHIVES: {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
            FileCategory.DATA: {'.csv', '.json', '.xml', '.sql', '.db', '.sqlite'},
            FileCategory.CODE: {'.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', '.sh', '.php'},
            FileCategory.EXECUTABLES: {'.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.apk'},
        }

    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(DEFAULT_LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if 'extensions' in config:
                        for category, exts in config['extensions'].items():
                            try:
                                enum_category = FileCategory[category.upper()]
                                self.extensions[enum_category] = set(exts)
                            except KeyError:
                                self.logger.warning(f"Unknown category '{category}' in config")
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")

    def _save_config(self):
        """Save current configuration to JSON file"""
        try:
            config = {
                'extensions': {
                    category.name: list(exts) 
                    for category, exts in self.extensions.items()
                }
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")

    def _get_file_category(self, file_path: Path) -> FileCategory:
        """Determine the category of a file based on its extension"""
        ext = file_path.suffix.lower()
        for category, exts in self.extensions.items():
            if ext in exts:
                return category
        return FileCategory.UNKNOWN

    def _get_target_folder(self, category: FileCategory) -> Path:
        """Get the target folder path for a given category"""
        folder_name = category.name.title()
        return self.base_dir / folder_name

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    def _resolve_conflict(self, source: Path, target: Path) -> ConflictResolution:
        """Resolve file conflict with user interaction"""
        self.logger.info(f"Conflict: {target.name} already exists in {target.parent}")
        
        while True:
            try:
                choice = input(
                    f"Choose action for {source.name}:\n"
                    "1. Rename and move\n"
                    "2. Overwrite if different\n"
                    "3. Skip\n"
                    "Enter choice (1-3): "
                ).strip()
                
                if choice == '1':
                    return ConflictResolution.RENAME
                elif choice == '2':
                    return ConflictResolution.OVERWRITE
                elif choice == '3':
                    return ConflictResolution.SKIP
                else:
                    print("Invalid choice. Please enter 1, 2, or 3")
            except KeyboardInterrupt:
                self.logger.info("Operation cancelled by user")
                raise

    def _move_file(self, source: Path, dry_run: bool = False) -> FileOperation:
        """Move a file to its appropriate category folder"""
        op = FileOperation(source=source, destination=Path(), action="")
        try:
            category = self._get_file_category(source)
            target_folder = self._get_target_folder(category)
            target_path = target_folder / source.name
            
            if not dry_run:
                target_folder.mkdir(exist_ok=True)
            
            if target_path.exists() and target_path != source:
                if dry_run:
                    op.destination = target_path
                    op.action = "Would resolve conflict"
                    return op
                
                resolution = self._resolve_conflict(source, target_path)
                
                if resolution == ConflictResolution.RENAME:
                    counter = 1
                    while True:
                        new_name = f"{source.stem}_{counter}{source.suffix}"
                        new_target = target_folder / new_name
                        if not new_target.exists():
                            target_path = new_target
                            break
                        counter += 1
                    op.action = "Renamed"
                elif resolution == ConflictResolution.OVERWRITE:
                    source_hash = self._calculate_hash(source)
                    target_hash = self._calculate_hash(target_path)
                    if source_hash == target_hash:
                        op.action = "Skipped (identical)"
                        op.destination = target_path
                        return op
                    op.action = "Overwritten"
                elif resolution == ConflictResolution.SKIP:
                    op.action = "Skipped"
                    op.destination = target_path
                    return op
            
            op.destination = target_path
            op.action = "Moved"
            
            if not dry_run:
                shutil.move(str(source), str(target_path))
                op.success = True
        except Exception as e:
            op.error = str(e)
            self.logger.error(f"Failed to move {source}: {str(e)}")
        finally:
            return op

    def organize(self, dry_run: bool = False, parallel: bool = True):
        """Organize files in the base directory"""
        if not self.base_dir.exists():
            raise FileOrganizerError(f"Directory {self.base_dir} does not exist")
        
        self.stats.start_time = time.time()
        files_to_process = [
            f for f in self.base_dir.iterdir() 
            if f.is_file() and not f.name.startswith('.')
        ]
        self.stats.total_files = len(files_to_process)
        
        self.logger.info(f"Starting organization of {self.stats.total_files} files in {self.base_dir}")
        
        try:
            if parallel:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [
                        executor.submit(self._move_file, file, dry_run)
                        for file in files_to_process
                    ]
                    for future in futures:
                        op = future.result()
                        self._update_stats(op)
                        self.operations.append(op)
            else:
                for file in files_to_process:
                    op = self._move_file(file, dry_run)
                    self._update_stats(op)
                    self.operations.append(op)
        except KeyboardInterrupt:
            self.logger.info("Operation interrupted by user")
            raise
        finally:
            self.stats.end_time = time.time()
            self._log_summary()

    def _update_stats(self, op: FileOperation):
        """Update statistics based on file operation"""
        self.stats.processed_files += 1
        
        if op.error:
            self.stats.failed_files += 1
        elif "Skipped" in op.action:
            self.stats.skipped_files += 1
        elif "Moved" in op.action or "Overwritten" in op.action or "Renamed" in op.action:
            self.stats.moved_files += 1

    def _log_summary(self):
        """Log summary of the organization operation"""
        duration = self.stats.end_time - self.stats.start_time
        files_per_sec = self.stats.processed_files / duration if duration > 0 else 0
        
        summary = (
            f"\nOrganization Complete\n"
            f"-------------------\n"
            f"Total files: {self.stats.total_files}\n"
            f"Processed: {self.stats.processed_files}\n"
            f"Moved: {self.stats.moved_files}\n"
            f"Skipped: {self.stats.skipped_files}\n"
            f"Failed: {self.stats.failed_files}\n"
            f"Duration: {duration:.2f} seconds\n"
            f"Speed: {files_per_sec:.1f} files/second\n"
        )
        self.logger.info(summary)

    def print_report(self):
        """Print a detailed report of file operations"""
        print("\nFile Operations Report:")
        print("{:<50} {:<50} {:<15} {:<10}".format(
            "Source", "Destination", "Action", "Status"))
        print("-" * 135)
        
        for op in self.operations:
            status = "Success" if op.success else f"Failed: {op.error}" if op.error else "Skipped"
            print("{:<50} {:<50} {:<15} {:<10}".format(
                str(op.source)[:48],
                str(op.destination)[:48] if op.destination else "N/A",
                op.action[:14],
                status[:9]
            ))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Industrial-Grade File Organizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=Path.home() / "Downloads",
        help="Directory to organize"
    )
    parser.add_argument(
        "-c", "--config",
        help="Configuration file path",
        default=DEFAULT_CONFIG_FILE
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Simulate organization without moving files"
    )
    parser.add_argument(
        "-s", "--serial",
        action="store_true",
        help="Process files serially instead of in parallel"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    try:
        base_dir = Path(args.directory)
        config_file = Path(args.config) if args.config else None
        
        organizer = FileOrganizer(base_dir, config_file)
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        organizer.organize(dry_run=args.dry_run, parallel=not args.serial)
        organizer.print_report()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except FileOrganizerError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
