#
# amget.ps1 - Interactive Apple Music downloader
#
# Quality auto-select:
#   Wrapper UP  (port 10020) -> ALAC -> FLAC
#   Wrapper DOWN             -> AAC-Legacy 256kbps
#
# Usage:
#   .\amget.ps1
#   .\amget.ps1 -Output D:\music\FLAC
#   .\amget.ps1 -Url "https://music.apple.com/jp/album/..."   (non-interactive)
#
param(
    [string]   $Url         = '',
    [string]   $Output      = 'D:\music',
    [string]   $GamdlDir    = 'D:\tools\gamdl',
    [string]   $WrapperHost = '127.0.0.1',
    [int]      $WrapperPort = 10020,
    [switch]   $AlacOnly,
    [switch]   $AacOnly,
    [switch]   $KeepM4a
)

$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = $GamdlDir

# ---- helpers ---------------------------------------------------------------

function Test-WrapperUp {
    if ($AacOnly) { return $false }
    try {
        $t = New-Object System.Net.Sockets.TcpClient
        $t.Connect($WrapperHost, $WrapperPort)
        $t.Close()
        return $true
    } catch { return $false }
}

function Show-Banner($alac) {
    Write-Host ''
    Write-Host '==========================================' -ForegroundColor DarkCyan
    Write-Host '  amget - Apple Music Downloader'          -ForegroundColor Cyan
    Write-Host '==========================================' -ForegroundColor DarkCyan
    if ($alac) {
        Write-Host '  Quality : ALAC -> FLAC  [Wrapper UP]'  -ForegroundColor Green
    } else {
        Write-Host '  Quality : AAC-Legacy 256kbps  [Wrapper DOWN]' -ForegroundColor Yellow
        Write-Host '  Tip     : run Wrapper then restart amget for ALAC' -ForegroundColor DarkGray
        Write-Host "            Start-Process wsl.exe -ArgumentList @('-d','Ubuntu-AM','--','bash','/tmp/run-wrapper.sh') -WindowStyle Minimized" -ForegroundColor DarkGray
    }
    Write-Host "  Output  : $Output"                        -ForegroundColor Gray
    Write-Host '  Empty URL or q -> quit'                   -ForegroundColor DarkGray
    Write-Host '==========================================' -ForegroundColor DarkCyan
    Write-Host ''
}

function Get-M4aSet($dir) {
    if (-not (Test-Path $dir)) { return @() }
    Get-ChildItem -Path $dir -Recurse -Filter '*.m4a' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName }
}

function Convert-ToFlac($m4a) {
    $flac = [System.IO.Path]::ChangeExtension($m4a, '.flac')
    & ffmpeg -hide_banner -loglevel error -y `
        -i $m4a `
        -map 0 -map_metadata 0 `
        -c:a flac -compression_level 8 `
        -c:v copy `
        $flac
    return $flac
}

function Invoke-Download {
    param([string]$url, [bool]$alac)

    $before = Get-M4aSet $Output

    $gamdlArgs = @(
        '-m', 'gamdl',
        '--cookies-path', "$GamdlDir\cookies.txt",
        '--output-path', $Output,
        '--no-config-file',
        '--single-disc-file-template', '{title}',
        '--multi-disc-file-template', '{disc}-{title}',
        '--no-album-file-template', '{title}',
        '--playlist-file-template', '{title}'
    )
    if ($alac) {
        $gamdlArgs += @(
            '--use-wrapper',
            '--wrapper-decrypt-ip', "${WrapperHost}:${WrapperPort}",
            '--song-codec-priority', 'alac'
        )
    } else {
        $gamdlArgs += '--song-codec-priority', 'aac-legacy'
    }
    $gamdlArgs += $url

    Write-Host ''
    & python @gamdlArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERR] gamdl exited with code $LASTEXITCODE" -ForegroundColor Red
        return
    }

    $after  = Get-M4aSet $Output
    $newM4a = $after | Where-Object { $before -notcontains $_ }

    if (-not $newM4a) {
        Write-Host '  [SKIP] No new files (already exist or nothing matched)' -ForegroundColor Yellow
        return
    }

    $count = @($newM4a).Count

    if ($alac) {
        $ok = 0
        foreach ($m4a in $newM4a) {
            $flac = Convert-ToFlac $m4a
            if (Test-Path $flac) {
                $sz = '{0:N1} MB' -f ((Get-Item $flac).Length / 1MB)
                Write-Host ("  [FLAC] {0}  ({1})" -f (Split-Path $flac -Leaf), $sz) -ForegroundColor Green
                if (-not $KeepM4a) { Remove-Item $m4a }
                $ok++
            } else {
                Write-Host "  [ERR] ffmpeg failed: $m4a" -ForegroundColor Red
            }
        }
        Write-Host ("  -> {0}/{1} file(s) converted to FLAC in {2}" -f $ok, $count, $Output) -ForegroundColor Cyan
    } else {
        foreach ($m4a in $newM4a) {
            $sz = '{0:N1} MB' -f ((Get-Item $m4a).Length / 1MB)
            Write-Host ("  [AAC ] {0}  ({1})" -f (Split-Path $m4a -Leaf), $sz) -ForegroundColor Green
        }
        Write-Host ("  -> {0} file(s) in {1}" -f $count, $Output) -ForegroundColor Cyan
    }
}

# ---- main ------------------------------------------------------------------

New-Item -ItemType Directory -Force -Path $Output | Out-Null

# Non-interactive mode: URL passed as argument
if ($Url) {
    $alac = Test-WrapperUp
    $mode = if ($alac) { 'ALAC->FLAC' } else { 'AAC-Legacy' }
    Write-Host "[amget] $mode  $Url" -ForegroundColor Cyan
    Invoke-Download $Url $alac
    exit 0
}

# Interactive mode
$alac = Test-WrapperUp
Show-Banner $alac

while ($true) {
    # Re-check wrapper each iteration (handles wrapper coming up mid-session)
    $alac = Test-WrapperUp
    $modeLabel = if ($alac) { '[ALAC]' } else { '[AAC ]' }
    $color     = if ($alac) { 'Green' } else { 'Yellow' }

    Write-Host $modeLabel -ForegroundColor $color -NoNewline
    $url = Read-Host ' URL'

    if ([string]::IsNullOrWhiteSpace($url) -or $url -eq 'q') {
        Write-Host 'Bye.' -ForegroundColor DarkGray
        break
    }

    Invoke-Download $url.Trim() $alac
    Write-Host ''
}
