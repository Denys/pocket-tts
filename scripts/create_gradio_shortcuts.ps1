param(
    [ValidateSet("english", "italian", "spanish", "german", "portuguese", "french_24l")]
    [string]$Language = "italian",
    [switch]$Launch
)

$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $Repo "Pocket-TTS-Gradio.bat"
$Icon = Join-Path $Repo "build\windows\Pocket-TTS.ico"

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Launcher not found: $Launcher"
}

$DesktopValue = (Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" -Name Desktop).Desktop
$Desktop = [Environment]::ExpandEnvironmentVariables($DesktopValue)
if (-not $Desktop) {
    $Desktop = Join-Path $env:USERPROFILE "Desktop"
}

$Startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
New-Item -ItemType Directory -Force -Path $Desktop, $Startup | Out-Null

$Shell = New-Object -ComObject WScript.Shell

function New-PocketShortcut {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $Shortcut = $Shell.CreateShortcut($Path)
    $Shortcut.TargetPath = $Launcher
    $Shortcut.Arguments = "--language $Language"
    $Shortcut.WorkingDirectory = $Repo
    if (Test-Path -LiteralPath $Icon) {
        $Shortcut.IconLocation = $Icon
    }
    $Shortcut.WindowStyle = 7
    $Shortcut.Description = "Start Pocket TTS Gradio ($Language) on http://127.0.0.1:7860"
    $Shortcut.Save()
}

$DesktopShortcut = Join-Path $Desktop "Pocket TTS Gradio.lnk"
$StartupShortcut = Join-Path $Startup "Pocket TTS Gradio.lnk"

New-PocketShortcut -Path $DesktopShortcut
New-PocketShortcut -Path $StartupShortcut

if ($Launch) {
    Start-Process -FilePath $Launcher -ArgumentList "--language $Language" -WorkingDirectory $Repo -WindowStyle Minimized
}

[PSCustomObject]@{
    DesktopShortcut = $DesktopShortcut
    StartupShortcut = $StartupShortcut
    Launcher = $Launcher
    Language = $Language
}
