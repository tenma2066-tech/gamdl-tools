#!/bin/sh
#
# amget.sh - Interactive Apple Music downloader for iPhone (iSH / Alpine Linux)
#
# AAC 256kbps only. ALAC/FLAC needs the Wrapper decryption server, which cannot
# run on iPhone, so this script sticks to the aac-legacy path that works fully
# on-device.
#
# Usage (inside iSH):
#     sh amget.sh                       # interactive: paste URLs one per line
#     sh amget.sh "https://music.apple.com/jp/album/..."   # one-shot
#
# Environment overrides:
#     COOKIES=/path/to/cookies.txt      (default: $HOME/cookies.txt)
#     OUTPUT=/path/to/output            (default: $HOME/music)
#
COOKIES="${COOKIES:-$HOME/cookies.txt}"
OUTPUT="${OUTPUT:-$HOME/music}"

# Resolve how gamdl is invoked (console script or python module)
if command -v gamdl >/dev/null 2>&1; then
    GAMDL="gamdl"
else
    GAMDL="python3 -m gamdl"
fi

mkdir -p "$OUTPUT"

if [ ! -f "$COOKIES" ]; then
    echo "[ERROR] cookies.txt not found: $COOKIES"
    echo "        Export it on the iPhone (see docs/IPHONE.md) and put it there."
    echo "        Or run:  COOKIES=/path/to/cookies.txt sh amget.sh"
    exit 1
fi

download() {
    url="$1"
    echo
    echo "[amget] AAC-Legacy 256kbps  ->  $OUTPUT"
    echo "[amget] $url"
    echo
    # shellcheck disable=SC2086
    $GAMDL \
        --cookies-path "$COOKIES" \
        --output-path "$OUTPUT" \
        --no-config-file \
        --song-codec-priority aac-legacy \
        --single-disc-file-template '{title}' \
        --multi-disc-file-template '{title}' \
        --no-album-file-template '{title}' \
        "$url"
    code=$?
    if [ "$code" -ne 0 ]; then
        echo "[amget] gamdl exited with code $code"
    fi
    return $code
}

# One-shot mode: URL passed as an argument
if [ -n "$1" ]; then
    download "$1"
    exit $?
fi

# Interactive mode
echo "=================================================="
echo "  amget - Apple Music Downloader (iPhone)"
echo "=================================================="
echo "  Output : $OUTPUT"
echo "  Cookies: $COOKIES"
echo "  Paste a URL and press Enter. Empty line or 'q' quits."
echo "=================================================="

while true; do
    printf '[URL] '
    read -r url || break
    case "$url" in
        ''|q|Q) echo "Bye."; break ;;
        *) download "$url" ;;
    esac
done
