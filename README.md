# gamdl-tools

Apple Music download tools built on top of [gamdl](https://github.com/glomatico/gamdl).

## Files

| File | Description |
|---|---|
| `gamdl-gui.exe` | GUI downloader (double-click to run, no Python needed) |
| `gamdl-dl.exe` | CLI downloader (no Python needed) |
| `gamdl_gui.py` | GUI source (requires Python + gamdl installed) |
| `ios/setup.sh` | **iPhone-only install** (run inside the iSH app — no PC needed) |
| `ios/amget.sh` | **iPhone-only interactive downloader** (run inside iSH) |
| `gamdl_web.py` | Web UI — control a PC's downloads from a phone browser (requires a PC) |
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

## Use on an iPhone — no PC (`ios/`)

You can run gamdl **entirely on the iPhone**, no computer required. gamdl 3.5.1
ships with a built-in Widevine device and decrypts songs in pure Python, so on
iOS you only need Python + ffmpeg, which the free **iSH** app (Alpine Linux)
provides.

**→ Full step-by-step guide (Japanese): [`docs/IPHONE.md`](docs/IPHONE.md)**

Short version:

1. Install the **iSH Shell** app (App Store, free).
2. Get `cookies.txt` on the phone with the **Orion Browser** + the
   *Get cookies.txt LOCALLY* extension, and drop it into iSH's home folder.
3. In iSH:
   ```sh
   wget -O setup.sh https://raw.githubusercontent.com/tenma2066-tech/gamdl-tools/master/ios/setup.sh
   wget -O amget.sh https://raw.githubusercontent.com/tenma2066-tech/gamdl-tools/master/ios/amget.sh
   sh setup.sh      # one-time install (slow under emulation: 10-30 min)
   sh amget.sh      # paste an Apple Music URL and download
   ```
4. Files land in `~/music`, visible in the iOS **Files app → iSH → music**.

> iPhone-only mode is **AAC 256kbps** only. ALAC/FLAC needs the Wrapper
> decryption server, which cannot run on iOS — use a PC for lossless.

## Control a PC from a phone browser (`gamdl_web.py`)

If you *do* have a PC, you can also run gamdl on the PC and drive it from the
iPhone browser. The download runs on the PC and is saved there; the phone is
just a remote control.

### On the PC (one-time)

1. Install Python 3.12+ and gamdl: `pip install gamdl==3.5.1`
2. Place `cookies.txt` next to `gamdl_web.py` (see [AAC requirements](#aac-256kbps-gui-or-cli-exe))
3. Start the server:

   ```powershell
   set PYTHONUTF8=1
   python gamdl_web.py
   ```

   It prints two URLs, e.g.:

   ```
   On this PC:      http://localhost:8765
   On your iPhone:  http://192.168.1.23:8765
   ```

4. Allow the port through the firewall if Windows asks (choose **Private networks**).

### On the iPhone

1. Connect to the **same Wi-Fi** as the PC.
2. Open the `http://192.168.1.23:8765` URL (from the PC console) in Safari.
   Tap **Share → Add to Home Screen** to keep it handy like an app.
3. Paste the Apple Music URL(s), pick a codec, tap **ダウンロード**. Live logs
   stream to the phone; files land in the PC's output folder.

### Options

```powershell
python gamdl_web.py --port 9000 --output D:\music --cookies D:\tools\cookies.txt
```

> The server binds to `0.0.0.0` (all interfaces) and has no authentication —
> use it only on a trusted home network, not on public Wi-Fi.

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
