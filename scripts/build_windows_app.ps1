param(
    [string]$DistPath = "dist/windows"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

$IconPath = Join-Path $RepoRoot "build/windows/Pocket-TTS.ico"

uv sync --extra desktop --extra build-windows
if ($LASTEXITCODE -ne 0) { throw "uv sync failed with exit code $LASTEXITCODE" }

uv run python scripts/create_windows_icon.py --out $IconPath
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed with exit code $LASTEXITCODE" }

uv run pyinstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "Pocket TTS" `
    --icon $IconPath `
    --specpath "build/windows" `
    --workpath "build/windows/pyinstaller" `
    --distpath $DistPath `
    --collect-data "pocket_tts" `
    "pocket_tts/windows_app.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

uv sync --extra desktop
if ($LASTEXITCODE -ne 0) { throw "Post-build desktop sync failed with exit code $LASTEXITCODE" }
