# 🗂️ File Organizer (Item Organizer)

A high-performance, parallelized file organizer designed for efficient sorting of large collections of files into categorized directories. Ideal for cleaning up downloads, media folders, and data dumps, with advanced features like checksum comparison, logging, reporting, and customizable file type categorization.

## 📦 Features

* Organizes files into predefined or custom categories (e.g., images, documents, scripts, etc.)
* Uses checksum (MD5) to detect and handle duplicate files
* Supports parallel processing using `ThreadPoolExecutor`
* Generates detailed operation reports and logs
* Automatically creates destination subdirectories
* Configurable conflict resolution strategies (`rename`, `overwrite`, `skip`)
* Supports custom category mappings via JSON configuration

## 🚀 Usage

### 📥 Installation

No installation required. This is a standalone Python script.

### ▶️ Running the Script

```bash
python file_organizer.py <source_directory> <destination_directory> [--workers N] [--config config.json]
```

### 🔧 Arguments

| Argument      | Description                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| `source`      | Path to the directory containing files to be organized.                      |
| `destination` | Path to the directory where organized files will be placed.                  |
| `--workers`   | *(Optional)* Number of parallel threads to use. Default is `4`.              |
| `--config`    | *(Optional)* Path to a JSON file to override default file extension mapping. |

### 📝 Example

```bash
python file_organizer.py ~/Downloads ~/Organized --workers 8 --config custom_categories.json
```

**Sample `custom_categories.json`:**

```json
{
  "music": [".mp3", ".flac"],
  "photos": [".jpg", ".png"],
  "scripts": [".py", ".sh"]
}
```

## 📄 Output

* `file_organizer.log`: Detailed log of all operations performed
* `organization_report.txt`: Summary report including file counts, skipped files, errors, and stats

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## ⚠️ Disclaimer

This script **moves** (not copies) files and deletes them from the source directory after transferring. Use caution, especially when pointing to important or system directories. Always test with a backup or sample folder before full-scale usage.

This software is provided "as is" without warranty of any kind, express or implied. The authors are not responsible for any legal implications of generated license files or repository management actions.  **This is a personal project intended for educational purposes. The developer makes no guarantees about the reliability or security of this software. Use at your own risk.**
