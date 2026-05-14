# Apple Music ALAC downloader + 16bit/44.1kHz FLAC conversion + synced lyrics embedding.
#
# Prerequisites:
#   - WSL2 Ubuntu + Wrapper installed (D:\tools\wrapper-prebuilt\setup-wsl.sh ran inside WSL)
#   - Wrapper running in WSL: cd /opt/wrapper && ./wrapper -H 0.0.0.0
#   - D:\tools\gamdl\cookies.txt present (Apple Music subscription cookies)
#
# Usage:
#   .\get-alac.ps1 -Url "https://music.apple.com/jp/album/.../...?i=..."
#   .\get-alac.ps1 -Url "..." -Output "D:\music\FLAC" -NoFlacConvert -KeepM4a

param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [string]$Output = 'D:\music',
    [switch]$NoFlacConvert,
    [switch]$KeepM4a,
    [string]$WrapperHost = '127.0.0.1',
    [int]$WrapperPort = 10020
)

$ErrorActionPreference = 'Stop'

# 1. Wrapper liveness check.
$wrapperUp = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect($WrapperHost, $WrapperPort)
    $tcp.Close()
    $wrapperUp = $true
} catch {}

if (-not $wrapperUp) {
    Write-Host "Wrapper not reachable on ${WrapperHost}:${WrapperPort}." -ForegroundColor Red
    Write-Host ''
    Write-Host 'Start it inside WSL2:' -ForegroundColor Yellow
    Write-Host '  wsl -d Ubuntu-AM'
    Write-Host '  cd /opt/wrapper'
    Write-Host '  ./wrapper -H 0.0.0.0'
    Write-Host '  # (re-login) ./wrapper -L "EMAIL:PASSWORD" -F -H 0.0.0.0'
    Write-Host ''
    exit 1
}

# 2. Ensure output dir.
New-Item -ItemType Directory -Force -Path $Output | Out-Null

# 3. Snapshot existing .m4a so we can detect new files.
$before = @()
if (Test-Path $Output) {
    $before = Get-ChildItem -Path $Output -Recurse -Filter '*.m4a' -ErrorAction SilentlyContinue |
              ForEach-Object { $_.FullName }
}

# 4. Run gamdl in ALAC mode through Wrapper.
$env:PYTHONPATH = 'D:\tools\gamdl'
$gamdlArgs = @(
    '-m', 'gamdl',
    '--cookies-path', 'D:\tools\gamdl\cookies.txt',
    '--output-path', $Output,
    '--no-config-file',
    '--use-wrapper',
    '--wrapper-decrypt-ip', "${WrapperHost}:${WrapperPort}",
    '--song-codec-priority', 'alac',
    '--album-folder-template', '',
    '--compilation-folder-template', '',
    '--no-album-folder-template', '',
    '--single-disc-file-template', '{title}',
    '--multi-disc-file-template', '{title}',
    '--playlist-file-template', '{title}',
    '--no-album-file-template', '{title}',
    $Url
)
& python @gamdlArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "gamdl failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Diff before/after, transcode each new file.
$after = Get-ChildItem -Path $Output -Recurse -Filter '*.m4a' -ErrorAction SilentlyContinue |
         ForEach-Object { $_.FullName }
$newM4a = $after | Where-Object { $before -notcontains $_ }

if (-not $newM4a) {
    Write-Host 'No new .m4a files detected (already existed or template path unexpected).' -ForegroundColor Yellow
    exit 0
}

foreach ($m4a in $newM4a) {
    Write-Host ''
    Write-Host "DL: $m4a" -ForegroundColor Green

    if ($NoFlacConvert) { continue }

    $flac = [System.IO.Path]::ChangeExtension($m4a, '.flac')
    $lrc  = [System.IO.Path]::ChangeExtension($m4a, '.lrc')

    Write-Host "->  $flac" -ForegroundColor Cyan

    # Build ffmpeg args: downsample to 16bit/44.1kHz, copy cover art, preserve all tags.
    $ffArgs = @(
        '-hide_banner', '-loglevel', 'error', '-y',
        '-i', $m4a,
        '-map', '0', '-map_metadata', '0',
        '-c:a', 'flac', '-compression_level', '8',
        '-ar', '44100', '-sample_fmt', 's16',
        '-c:v', 'copy'
    )

    # Embed synced lyrics (.lrc) as SYNCEDLYRICS tag if present.
    if (Test-Path $lrc) {
        $lrcContent = [System.IO.File]::ReadAllText($lrc, [System.Text.Encoding]::UTF8)
        $ffArgs += @('-metadata', "SYNCEDLYRICS=$lrcContent")
        Write-Host "  embedding synced lyrics from $([System.IO.Path]::GetFileName($lrc))" -ForegroundColor DarkCyan
    }

    $ffArgs += $flac
    & ffmpeg @ffArgs

    if (Test-Path $flac) {
        $sizeM4a  = (Get-Item $m4a).Length
        $sizeFlac = (Get-Item $flac).Length
        Write-Host ('  m4a={0:N1}MB -> flac={1:N1}MB' -f ($sizeM4a / 1MB), ($sizeFlac / 1MB))

        if (-not $KeepM4a) {
            Remove-Item $m4a
            Write-Host '  m4a removed' -ForegroundColor DarkGray
        }

        # Remove .lrc since lyrics are now embedded in the FLAC.
        if (Test-Path $lrc) {
            Remove-Item $lrc
            Write-Host '  .lrc removed (embedded)' -ForegroundColor DarkGray
        }
    } else {
        Write-Host "ffmpeg failed for $m4a" -ForegroundColor Red
    }
}
