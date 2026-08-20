# MetaClean

**Universal Metadata Inspection & Sanitization**

A cross-platform, privacy-first CLI tool that detects and analyzes file metadata, explains what’s contained within each file, and generates sanitized copies with sensitive metadata removed. It works without modifying or overwriting the original files, giving users a safer way to inspect, understand, and share files while keeping their original data completely untouched.

```
                    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⠀⠀⠀⢀⣤⡶⠁⣠⣴⣾⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⢀⣴⣿⣿⣴⣿⠿⠋⣁⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⣰⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⣠⣾⣿⡿⠟⠋⠉⠀⣀⣀⣀⣨⣭⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⣤⣤⣤⣴⠂
                    ⠈⠉⠁⠀⠀⣀⣴⣾⣿⣿⡿⠟⠛⠉⠉⠉⠉⠉⠛⠻⠿⠿⠿⠿⠿⠿⠟⠋⠁⠀
                    ⠀⠀⠀⢀⣴⣿⣿⣿⡿⠁⠀⢀⣀⣤⣤⣤⣤⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⣾⣿⣿⣿⡿⠁⢀⣴⣿⠋⠉⠉⠉⠉⠛⣿⣿⣶⣤⣤⣤⣤⣶⠖⠀⠀⠀
                    ⠀⠀⢸⣿⣿⣿⣿⡇⢀⣿⣿⣇⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀
                    ⠀⠀⠸⣿⣿⣿⣿⡇⠈⢿⣿⣿⠇⠀⠀⠀⠀⠀⢠⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⢿⣿⣿⣿⣷⡀⠀⠉⠉⠀⠀⠀⠀⠀⢀⣾⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⠀⠙⢿⣿⣿⣷⣄⡀⠀⠀⠀⠀⣀⣴⣿⣿⣿⣋⣠⡤⠄⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⠀⠀⠀⠈⠙⠛⠛⠿⠿⠿⠿⠿⠿⠟⠛⠛⠛⠉⠁

                    METACLEAN - v1.0.0 : Universal Metadata Sanitizer
```

---

## Install

### Quick install (recommended)

**Linux / macOS / Termux / WSL:**
```bash
git clone https://github.com/Anonycodexia/MetaClean
cd MetaClean
chmod +x install.sh
./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/Anonycodexia/MetaClean
cd MetaClean
.\install.ps1
```

The installer automatically:
- Copies `metaclean.py` to your system
- Creates a `metaclean` command on your PATH
- Detects and installs missing tools (exiftool, ffmpeg, qpdf)

Open a new terminal after install, then run `metaclean` from anywhere.

### Manual install (no installer)

```bash
git clone https://github.com/Anonycodexia/MetaClean
cd MetaClean

# Run directly
python3 metaclean.py --help

# Or install as a Python package
pip install .
```

### From PyPI (if published)

```bash
pip install metaclean
```

### Uninstall

```bash
# Unix
rm ~/.local/bin/metaclean
rm -rf ~/.local/share/metaclean

# Or use the uninstaller
./uninstall.sh
```

---

## Usage

### Interactive mode (default)

```bash
metaclean
```

MetaClean starts, detects your platform, checks tools, then asks:

```
> Enter the Path of the file : /storage/emulated/0/Download/photo.jpg
```

After scanning metadata:

```
> Do you want to delete Metadata (y/n) : y
```

### Direct inspection

```bash
metaclean photo.jpg
metaclean --scan photo.jpg
```

### Direct cleaning (non-interactive)

```bash
metaclean --clean --yes photo.jpg
```

### Specify output path

```bash
metaclean --clean --output /tmp/safe.jpg photo.jpg
```

### Dry run

```bash
metaclean --dry-run photo.jpg
```

### JSON output

```bash
metaclean --json photo.jpg
```

### All options

```bash
metaclean --help
```

| Option | Description |
|--------|-------------|
| `file` | Path to the file |
| `--scan` | Inspect only, no cleaning |
| `--clean` | Clean without prompting |
| `--dry-run` | Show what would happen |
| `--output PATH` | Custom output path |
| `--json` | Machine-readable JSON |
| `--yes` | Auto-yes to all prompts |
| `--recursive` | Directory preview |
| `--no-color` | Disable colors |
| `--no-animation` | Disable progress bars |
| `--verbose` | Show all metadata |
| `--debug` | Show errors with tracebacks |
| `--version` | Print version |

---

## Supported Formats

| Type | Formats | Engine |
|------|---------|--------|
| Images | JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC, AVIF, PSD, RAW | ExifTool |
| Video | MP4, MOV, MKV, AVI, WebM, 3GP, MTS, FLV, WMV | FFmpeg |
| Audio | MP3, FLAC, WAV, AAC, M4A, OGG, OPUS, WMA, AIFF | FFmpeg |
| PDF | PDF | qpdf |
| Text/Source | .py, .js, .txt, .json, .xml, etc. | None (no embedded metadata) |

---

## External Tools

MetaClean auto-installs these if missing:

| Tool | Used for | Install |
|------|----------|---------|
| ExifTool | Image metadata | `apt install libimage-exiftool-perl` / `brew install exiftool` |
| FFmpeg | Media containers | `apt install ffmpeg` / `brew install ffmpeg` |
| qpdf | PDF rewriting | `apt install qpdf` / `brew install qpdf` |

---

## Platform Support

| Platform | Package Manager |
|----------|----------------|
| Termux | `pkg` |
| Linux (Debian/Ubuntu) | `apt` |
| Linux (Fedora/RHEL) | `dnf` |
| Linux (Arch) | `pacman` |
| Linux (openSUSE) | `zypper` |
| Linux (Alpine) | `apk` |
| macOS | `brew` |
| Windows | `winget` / `choco` / `scoop` |

---

## Build from Source

```bash
git clone https://github.com/Anonycodexia/MetaClean
cd MetaClean

# Run modular version
python3 -m metaclean.main --help

# Run standalone version
python3 metaclean.py --help

# Install as package
pip install .

# Build distributions
python3 -m build
```

---

## How It Works

```
DETECT → UNDERSTAND → SELECT ENGINE → INSPECT → ASK → COPY → VERIFY → REPORT
```

1. Detects file type from magic bytes, not just extension
2. Selects the right engine (ExifTool / FFmpeg / qpdf)
3. Shows metadata and privacy-sensitive fields
4. Asks permission before cleaning
5. Creates a `.cleaned` copy (original is never modified)
6. Re-scans the output to verify what was removed
7. Reports honestly what remains

---

## Security

- No network requests during cleaning
- No file uploads
- Original file is never modified
- No code execution on input files
- All subprocess calls use argument arrays (no `shell=True`)

---

## License

MIT License

This project is licensed under the MIT License, a permissive open-source license that allows others to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software.

The main requirement is that the original copyright notice and license text are included with copies or substantial portions of the software. The MIT License also provides the software without warranty, meaning the author is not responsible for damages arising from its use.

In short, you are giving people broad permission to use and modify your code, including in commercial projects, while asking them to keep the original license and copyright notice.

For the complete terms, see the "LICENSE" file in this repository.
