#!/bin/sh
#
# setup.sh - One-time gamdl install for iPhone (inside the iSH app / Alpine Linux)
#
# gamdl 3.5.1 bundles its own Widevine device and decrypts songs in pure Python,
# so on iPhone you only need Python + ffmpeg + gamdl. No PC, no .wvd file,
# no mp4decrypt/N_m3u8DL-RE.
#
# Run this ONCE inside iSH:
#     wget -O setup.sh https://raw.githubusercontent.com/tenma2066-tech/gamdl-tools/master/ios/setup.sh
#     sh setup.sh
#
# x86 emulation in iSH is slow: the first install can take 10-30 minutes.
# Leave the app in the foreground with the screen on until it finishes.
#
set -e

GAMDL_VERSION="${GAMDL_VERSION:-3.5.1}"
MUSIC_DIR="$HOME/music"

echo "=================================================="
echo "  gamdl setup for iPhone (iSH / Alpine Linux)"
echo "=================================================="

echo "[1/5] Updating Alpine package index..."
apk update

# Prebuilt packages so pip does not have to compile the heavy C extensions
# (Pillow, pycryptodome, cryptography) under slow x86 emulation. build-base and
# the -dev packages are the fallback compiler toolchain in case a wheel is missing.
echo "[2/5] Installing system packages (python, ffmpeg, build tools)..."
apk add --no-cache \
    python3 py3-pip \
    ffmpeg git \
    py3-pillow py3-pycryptodome py3-cryptography py3-lxml \
    build-base python3-dev jpeg-dev zlib-dev libffi-dev openssl-dev

echo "[3/5] Upgrading pip..."
python3 -m pip install --break-system-packages --upgrade pip

echo "[4/5] Installing gamdl==$GAMDL_VERSION (this is the slow step)..."
# --break-system-packages: install into the system site so it can reuse the
# apk-provided C extensions above instead of rebuilding them.
python3 -m pip install --break-system-packages "gamdl==$GAMDL_VERSION"

echo "[5/5] Creating music folder: $MUSIC_DIR"
mkdir -p "$MUSIC_DIR"

echo
echo "=================================================="
echo "  Done."
echo "=================================================="
if command -v gamdl >/dev/null 2>&1; then
    echo "  gamdl: $(command -v gamdl)"
else
    echo "  gamdl installed as a module (run with: python3 -m gamdl)"
fi
echo "  Music will be saved to: $MUSIC_DIR"
echo "  (visible in the iOS Files app under 'iSH')"
echo
echo "  Next:"
echo "    1. Put your cookies.txt in \$HOME  (see docs/IPHONE.md)"
echo "    2. Run:  sh amget.sh"
echo "=================================================="
