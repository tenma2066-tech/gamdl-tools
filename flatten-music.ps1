# Post-process D:\music: flatten subfolders + strip track-number prefix + embed orphan .lrc
param(
    [string]$Root = 'D:\music'
)

$ErrorActionPreference = 'Stop'

# 1. Embed orphaned .lrc into corresponding .flac (same stem in same dir)
$lrcFiles = Get-ChildItem -Path $Root -Recurse -Filter '*.lrc' -ErrorAction SilentlyContinue
foreach ($lrc in $lrcFiles) {
    $flacName = [System.IO.Path]::ChangeExtension($lrc.Name, '.flac')
    $flacPath = Join-Path $lrc.DirectoryName $flacName
    if (Test-Path $flacPath) {
        $lrcContent = [System.IO.File]::ReadAllText($lrc.FullName, [System.Text.Encoding]::UTF8)
        Write-Host "Embedding lrc -> $flacName" -ForegroundColor Cyan
        & ffmpeg -hide_banner -loglevel error -y `
            -i $flacPath `
            -map 0 -map_metadata 0 `
            -c:a copy -c:v copy `
            "-metadata" "SYNCEDLYRICS=$lrcContent" `
            "$flacPath.tmp.flac"
        if (Test-Path "$flacPath.tmp.flac") {
            Remove-Item $flacPath
            Rename-Item "$flacPath.tmp.flac" $flacName
            Remove-Item $lrc.FullName
            Write-Host "  done" -ForegroundColor Green
        } else {
            Write-Host "  ffmpeg failed, lrc left in place" -ForegroundColor Yellow
        }
    }
}

# 2. Move all .flac from subfolders to $Root (flatten), strip "NN " prefix
$moved = 0; $renamed = 0; $skipped = 0
Get-ChildItem -Path $Root -Recurse -Filter '*.flac' -ErrorAction SilentlyContinue |
Where-Object { $_.DirectoryName -ne $Root } |
ForEach-Object {
    $srcPath  = $_.FullName
    $destName = $_.Name -replace '^\d{2,3} ', ''
    $destPath = Join-Path $Root $destName
    if (Test-Path $destPath) {
        Write-Host "SKIP (exists): $destName" -ForegroundColor Yellow
        $skipped++
        return
    }
    Move-Item -LiteralPath $srcPath -Destination $destPath
    if ($_.Name -ne $destName) {
        Write-Host "  $($_.Name) -> $destName" -ForegroundColor Green
        $renamed++
    } else {
        Write-Host "  moved: $destName" -ForegroundColor Green
    }
    $moved++
}

# 3. Clean up empty subdirs
Get-ChildItem -Path $Root -Recurse -Directory -ErrorAction SilentlyContinue |
Sort-Object FullName -Descending |
Where-Object { (Get-ChildItem $_.FullName -ErrorAction SilentlyContinue).Count -eq 0 } |
ForEach-Object {
    Remove-Item $_.FullName
    Write-Host "  rmdir: $($_.Name)" -ForegroundColor DarkGray
}

# 4. Rename already-flat files that still have "NN " prefix
Get-ChildItem -Path $Root -Filter '*.flac' -ErrorAction SilentlyContinue |
Where-Object { $_.Name -match '^\d{2,3} ' } |
ForEach-Object {
    $newName = $_.Name -replace '^\d{2,3} ', ''
    $newPath = Join-Path $Root $newName
    if (-not (Test-Path $newPath)) {
        Rename-Item -LiteralPath $_.FullName -NewName $newName
        Write-Host "  rename: $($_.Name) -> $newName"
        $renamed++
    }
}

Write-Host ""
Write-Host "Done. moved=$moved renamed=$renamed skipped=$skipped" -ForegroundColor Green
