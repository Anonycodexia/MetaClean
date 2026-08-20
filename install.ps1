# install.ps1 - MetaClean installer for Windows
# Run from PowerShell:  .\install.ps1
# Automatically installs exiftool, ffmpeg, and qpdf if missing.

$ErrorActionPreference = "Stop"

function Print-Banner {
    @'
  __  __      _ ____              _
 |  \/  | ___| | ___   _ _ __ ___| |__   ___ _ __ ___
 | |\/| |/ _ \ | | | | | | '__/ __| '_ \ / _ \ '__/ __|
 | |  | |  __/ | | |_| | | | | (__| | | |  __/ |  \__ \
 |_|  |_|\___|_|_|\__,_|_|_|  \___|_| |_|\___|_|  |___/

              Universal Metadata Sanitizer - Installer
                  (auto-installs all dependencies)
'@ | Write-Host
}

Print-Banner

$InstallDir = Join-Path $env:LOCALAPPDATA "MetaClean"
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }

$Standalone = Join-Path $ScriptDir "metaclean.py"
if (-not (Test-Path $Standalone)) {
    Write-Host "ERROR: metaclean.py not found in $ScriptDir" -ForegroundColor Red
    Write-Host "Run this installer from the directory containing metaclean.py"
    exit 1
}

$PythonCmd = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.(\d+)") {
            $minor = [int]$matches[1]
            if ($minor -ge 10) {
                $PythonCmd = $candidate
                break
            }
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "ERROR: Python 3.10+ is required but was not found on PATH." -ForegroundColor Red
    Write-Host "Install Python from https://www.python.org/downloads/windows/"
    Write-Host "or run: winget install Python.Python.3.12"
    exit 1
}

$PyVersion = & $PythonCmd --version
Write-Host "[+] Python detected: $PyVersion"

Write-Host "[+] Install dir: $InstallDir"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "[+] Copying metaclean.py"
Copy-Item $Standalone (Join-Path $InstallDir "metaclean.py") -Force

$WrapperPath = Join-Path $InstallDir "metaclean.cmd"
$WrapperContent = @"
@echo off
"$PythonCmd" "$InstallDir\metaclean.py" %*
"@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding ASCII
Write-Host "[+] Created wrapper: $WrapperPath"

$PsWrapperPath = Join-Path $InstallDir "metaclean.ps1"
$PsWrapperContent = @"
& "$PythonCmd" "$InstallDir\metaclean.py" @args
exit `$LASTEXITCODE
"@
Set-Content -Path $PsWrapperPath -Value $PsWrapperContent -Encoding UTF8
Write-Host "[+] Created PowerShell wrapper: $PsWrapperPath"

$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentUserPath -notlike "*$InstallDir*") {
    $newPath = if ($currentUserPath) { "$currentUserPath;$InstallDir" } else { $InstallDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[+] Added $InstallDir to user PATH"
} else {
    Write-Host "[+] $InstallDir already on user PATH"
}

$env:Path = "$env:Path;$InstallDir"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Checking external dependencies..." -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$MissingTools = @()

function Test-Tool($name) {
    $found = $null
    try {
        $found = Get-Command $name -ErrorAction Stop
    } catch {}
    if ($found) {
        Write-Host "[+] ${name}: found ($($found.Source))"
        return $true
    } else {
        Write-Host "[!] ${name}: NOT found" -ForegroundColor Yellow
        return $false
    }
}

if (-not (Test-Tool "exiftool")) { $MissingTools += "exiftool" }
if (-not (Test-Tool "ffmpeg"))   { $MissingTools += "ffmpeg" }
if (-not (Test-Tool "qpdf"))     { $MissingTools += "qpdf" }

if ($MissingTools.Count -eq 0) {
    Write-Host ""
    Write-Host "[+] All external dependencies are already installed." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Missing tools: $($MissingTools -join ', ')"
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Auto-installing missing dependencies..." -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""

    $WingetAvailable = $false
    try {
        $w = Get-Command winget -ErrorAction Stop
        $WingetAvailable = $true
    } catch {}

    $ChocoAvailable = $false
    try {
        $c = Get-Command choco -ErrorAction Stop
        $ChocoAvailable = $true
    } catch {}

    $ScoopAvailable = $false
    try {
        $s = Get-Command scoop -ErrorAction Stop
        $ScoopAvailable = $true
    } catch {}

    foreach ($tool in $MissingTools) {
        $installed = $false

        if ($WingetAvailable) {
            $wingetId = switch ($tool) {
                "exiftool" { "Oliver.Bettenworth.ExifTool" }
                "ffmpeg"   { "Gyan.FFmpeg" }
                "qpdf"     { "QPDF.QPDF" }
            }
            Write-Host "[*] Installing $tool via winget (ID: $wingetId)..."
            try {
                & winget install --silent --accept-source-agreements --accept-package-agreements $wingetId 2>&1 | Out-Host
                if ($LASTEXITCODE -eq 0) { $installed = $true }
            } catch {
                Write-Host "[!] winget install failed for $tool" -ForegroundColor Yellow
            }
        }

        if (-not $installed -and $ChocoAvailable) {
            Write-Host "[*] Installing $tool via chocolatey..."
            try {
                & choco install $tool -y 2>&1 | Out-Host
                if ($LASTEXITCODE -eq 0) { $installed = $true }
            } catch {
                Write-Host "[!] choco install failed for $tool" -ForegroundColor Yellow
            }
        }

        if (-not $installed -and $ScoopAvailable) {
            Write-Host "[*] Installing $tool via scoop..."
            try {
                & scoop install $tool 2>&1 | Out-Host
                if ($LASTEXITCODE -eq 0) { $installed = $true }
            } catch {
                Write-Host "[!] scoop install failed for $tool" -ForegroundColor Yellow
            }
        }

        if (-not $installed) {
            Write-Host "[!] Could not auto-install $tool" -ForegroundColor Yellow
            Write-Host "    Please install $tool manually:"
            switch ($tool) {
                "exiftool" {
                    Write-Host "    Download from: https://exiftool.org/"
                    Write-Host "    Rename exiftool(-k).exe to exiftool.exe and place on PATH"
                }
                "ffmpeg"   { Write-Host "    Download from: https://www.gyan.dev/ffmpeg/builds/" }
                "qpdf"     { Write-Host "    Download from: https://github.com/qpdf/qpdf/releases" }
            }
        }
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Verifying installations..." -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan

    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    foreach ($tool in $MissingTools) {
        try {
            $found = Get-Command $tool -ErrorAction Stop
            Write-Host "[+] ${tool}: installed successfully" -ForegroundColor Green
        } catch {
            Write-Host "[!] ${tool}: may need a new terminal window or manual PATH refresh" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "  MetaClean installation complete!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installed to: $InstallDir\metaclean.py"
Write-Host "Command:      metaclean"
Write-Host ""

try {
    $versionOutput = & $PythonCmd "$InstallDir\metaclean.py" --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[+] Verification: $versionOutput" -ForegroundColor Green
    }
} catch {
    Write-Host "[!] Could not verify installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To start using metaclean in THIS terminal, run:"
Write-Host "  `$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + `$env:Path"
Write-Host ""
Write-Host "Or simply open a NEW PowerShell / CMD window, then:"
Write-Host "  metaclean                          # interactive mode"
Write-Host "  metaclean photo.jpg                # inspect + offer to clean"
Write-Host "  metaclean --scan photo.jpg         # scan only"
Write-Host "  metaclean --clean -y photo.jpg     # non-interactive clean"
Write-Host "  metaclean --help                   # full options"
Write-Host ""
Write-Host "To uninstall later: Remove-Item -Recurse $InstallDir"
Write-Host "And remove $InstallDir from your user PATH (System Properties > Environment Variables)"
