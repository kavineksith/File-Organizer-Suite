# File Organizer Suite

## 📂 Overview

A collection of robust file organization tools designed to efficiently categorize and manage files with advanced features like parallel processing, conflict resolution, and detailed reporting.

## 🛠️ Tools Included

1. **Basic File Organizer**
   - Categorizes files by type (images, documents, code, etc.)
   - Supports dry-run simulations and verbose logging
   - Configurable extension mapping via JSON

2. **Advanced Item Organizer**
   - Parallel processing with thread pooling
   - MD5 checksum-based duplicate detection
   - Customizable conflict resolution strategies
   - Detailed operation reports and logs

## ✨ Key Features

- **Flexible Categorization**: Predefined categories with customizable overrides
- **Safe Operations**: Dry-run mode and conflict resolution options
- **High Performance**: Parallel processing for large file collections
- **Comprehensive Logging**: Detailed operation logs and summary reports
- **Duplicate Handling**: Checksum verification for identical files

## 🚀 Usage

### Basic Organizer
```bash
python3 file_organizer.py [directory] [options]
```

### Advanced Organizer
```bash
python file_organizer.py <source> <destination> [--workers N] [--config config.json]
```

### Common Options
- `-c/--config`: Specify custom category mappings
- `-d/--dry-run`: Simulate without making changes
- `-v/--verbose`: Enable detailed logging

## ⚙️ Configuration

Customize file categories via JSON configuration:
```json
{
  "images": [".jpg", ".png"],
  "documents": [".pdf", ".docx"],
  "code": [".py", ".js"]
}
```

## 📊 Outputs
- Operation logs (`file_organizer.log`)
- Summary reports (console and/or file)
- Organized directory structure

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided **"as is"** without any warranty of any kind. It is intended for educational, personal, or professional use in environments where validation and review are standard.

**Use in production systems is at your own risk.**

This software is provided "as is" without warranty of any kind, express or implied. The authors are not responsible for any legal implications of generated license files or repository management actions.  **This is a personal project intended for educational purposes. The developer makes no guarantees about the reliability or security of this software. Use at your own risk.**


**Important:** These tools modify file locations. Always:
- Backup important files before use
- Test with dry-run mode first
- Verify configurations before execution

This software is provided "as is" without warranty. The developers are not responsible for any data loss or unintended modifications. **Use at your own risk.**

For both tools:
- Designed for educational and professional use
- Not guaranteed to be bug-free
- Users are responsible for verifying results
- Always validate in test environments before production use
