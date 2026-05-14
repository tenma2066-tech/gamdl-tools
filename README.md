# gamdl-tools

Apple Music download tools built on top of [gamdl](https://github.com/glomatico/gamdl).

## Files

| File | Description |
|---|---|
| `gamdl-gui.exe` | GUI downloader (double-click to run, no Python needed) |
| `gamdl-dl.exe` | CLI downloader (no Python needed) |
| `gamdl_gui.py` | GUI source (requires Python + gamdl installed) |
| `gamdl_dl.py` | CLI entry point source |
| `get-alac.ps1` | ALAC download + FLAC conversion helper (requires WSL2 + Wrapper) |
| `amget.ps1` | Interactive loop wrapper for gamdl |
| `flatten-music.ps1` | Flatten Artist/Album subfolders into a single directory |

## Requirements

### AAC 256kbps (GUI or CLI exe)
- `cookies.txt` — export from `music.apple.com` using [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) Chrome extension
- Place `cookies.txt` in the same folder as the `.exe`

### ALAC lossless (`get-alac.ps1`)
- WSL2 with Ubuntu (`Ubuntu-AM` distro)
- [WorldObservationLog/wrapper](https://github.com/WorldObservationLog/wrapper) running in WSL2
- `ffmpeg` on PATH

## Quick Start (GUI)

1. Export `cookies.txt` from `music.apple.com`
2. Place `cookies.txt` next to `gamdl-gui.exe`
3. Double-click `gamdl-gui.exe`
4. Paste Apple Music URL, choose output folder, click **Download**

## Quick Start (CLI)

```powershell
set PYTHONUTF8=1
gamdl-dl.exe --output-path D:\music --song-codec-priority aac-legacy "https://music.apple.com/jp/..."
```

## Build from Source

Requires Python 3.12+.

```powershell
python -m venv build-env
build-env\Scripts\pip install gamdl==3.5.1 pyinstaller

# CLI
build-env\Scripts\pyinstaller --onefile --name gamdl-dl `
  --collect-all gamdl --collect-all yt_dlp --collect-all mutagen `
  --collect-all httpx --collect-all click `
  --hidden-import construct --hidden-import pywidevine gamdl_dl.py

# GUI
build-env\Scripts\pyinstaller --onefile --windowed --name gamdl-gui `
  --collect-all gamdl --collect-all yt_dlp --collect-all mutagen `
  --collect-all httpx --collect-all click `
  --hidden-import construct --hidden-import pywidevine gamdl_gui.py
```

## Notes

- Set `PYTHONUTF8=1` to avoid encoding errors with Japanese/Chinese track titles on Windows
- `--album-folder-template ''` does not work in PowerShell (empty string is dropped); use `flatten-music.ps1` to flatten output instead
- cookies.txt expires every few days — re-export when you get a 403 error
- This tool is for personal use with an active Apple Music subscription
