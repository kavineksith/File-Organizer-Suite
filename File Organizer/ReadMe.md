# 🗂️ File Organizer

A robust and configurable command-line tool to intelligently organize your files by type with features like parallel processing, conflict resolution, dry-run simulation, undo capability (via logging), and detailed reports. Designed for power users, developers, and sysadmins who want control and performance.

## 🔍 Features

* ✅ **Categorizes files** (images, videos, documents, code, etc.)
* ⚙️ **Configurable extension mapping** via JSON
* ⚡ **Parallel file processing** (with optional serial mode)
* 🧪 **Dry-run mode** to simulate actions without changes
* 🔄 **Conflict resolution**: rename, overwrite, or skip
* 📋 **Detailed report** after execution
* 🪵 **Logging** to file and console
* 🧠 **Smart handling** of duplicate content via SHA256 hashes
* 🧯 **Graceful exit** on keyboard interrupt
* 🧼 Ignores hidden files and operates in-place

## 🚀 Usage

### 🔧 Command-line

```bash
python3 file_organizer.py [directory] [options]
```

### 📌 Options

| Option            | Description                                    |
| ----------------- | ---------------------------------------------- |
| `directory`       | Directory to organize (default: `~/Downloads`) |
| `-c`, `--config`  | Path to custom JSON config file                |
| `-d`, `--dry-run` | Simulate actions without moving files          |
| `-s`, `--serial`  | Use serial processing instead of threads       |
| `-v`, `--verbose` | Enable verbose logging to console              |

### ✅ Example

```bash
python3 file_organizer.py ~/Downloads -d -v
```

Simulates organizing the `~/Downloads` folder with verbose logging enabled.

## 🧰 Configuration

You can define or override file type associations by editing or supplying a config file (`file_organizer_config.json`). Example:

```json
{
  "extensions": {
    "images": [".jpg", ".jpeg", ".png", ".webp"],
    "code": [".py", ".js", ".html"]
  }
}
```

The script will create this file if it doesn't exist.


## 📄 Output

* 📝 **Log File**: `file_organizer.log`
* 📊 **Operation Summary** and a **tabular report** of each file operation in the terminal.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool **modifies file locations**, and while it includes a dry-run and conflict resolution, **use at your own risk**. Always backup critical files before running automated tools that move data.

This software is provided "as is" without warranty of any kind, express or implied. The authors are not responsible for any legal implications of generated license files or repository management actions.  **This is a personal project intended for educational purposes. The developer makes no guarantees about the reliability or security of this software. Use at your own risk.**
