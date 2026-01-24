# build.ps1 - Build script for the OPC UA server (server/)
# This script copies your modified server_json_config.c to the open62541 repo,
# builds it, and copies the new executable back.

$ErrorActionPreference = "Stop"

# Configuration - paths are auto-detected; override via environment variables if needed
$WorkingOpcDir = $PSScriptRoot
$Open62541Dir = "$PSScriptRoot\..\third_party\open62541"

# ── Auto-detect CMake ────────────────────────────────────────────────
$CmakePath = $null
# 1. Env-var override
if ($env:CMAKE_PATH -and (Test-Path $env:CMAKE_PATH)) {
    $CmakePath = $env:CMAKE_PATH
}
# 2. Already in PATH?
if (-not $CmakePath) {
    $cmCmd = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($cmCmd) { $CmakePath = $cmCmd.Path }
}
# 3. Common install locations
if (-not $CmakePath) {
    $cmakeCandidates = @(
        "$env:ProgramFiles\CMake\bin\cmake.exe",
        "${env:ProgramFiles(x86)}\CMake\bin\cmake.exe",
        "$env:LOCALAPPDATA\CMake\bin\cmake.exe"
    )
    foreach ($cp in $cmakeCandidates) {
        if (Test-Path $cp) { $CmakePath = $cp; break }
    }
}
if ($CmakePath) {
    Write-Host "Found CMake at: $CmakePath" -ForegroundColor Green
} else {
    Write-Host "ERROR: CMake not found! Install from https://cmake.org/download/ or set CMAKE_PATH env var." -ForegroundColor Red
    exit 1
}

# ── Auto-detect OpenSSL ──────────────────────────────────────────────
$OpenSslDir = $null
# 1. Env-var override
if ($env:OPENSSL_DIR -and (Test-Path $env:OPENSSL_DIR)) {
    $OpenSslDir = $env:OPENSSL_DIR
}
# 2. Already in PATH?
if (-not $OpenSslDir) {
    $sslCmd = Get-Command openssl.exe -ErrorAction SilentlyContinue
    if ($sslCmd) { $OpenSslDir = Split-Path $sslCmd.Path -Parent }
}
# 3. Common install locations
if (-not $OpenSslDir) {
    $sslCandidates = @(
        "$env:ProgramFiles\OpenSSL-Win64\bin",
        "$env:ProgramFiles\OpenSSL\bin",
        "${env:ProgramFiles(x86)}\OpenSSL-Win64\bin",
        "$env:ProgramW6432\OpenSSL-Win64\bin",
        "C:\OpenSSL-Win64\bin",
        "C:\OpenSSL\bin"
    )
    foreach ($sp in $sslCandidates) {
        if (Test-Path $sp) { $OpenSslDir = $sp; break }
    }
}
if ($OpenSslDir) {
    Write-Host "Found OpenSSL at: $OpenSslDir" -ForegroundColor Green
} else {
    Write-Host "WARNING: OpenSSL not found. Encryption support may fail. Install from https://slproweb.com/products/Win32OpenSSL.html or set OPENSSL_DIR env var." -ForegroundColor Yellow
}

# ── Auto-detect MSBuild ──────────────────────────────────────────────
$msbuildPath = $null
try {
    $msCmd = Get-Command msbuild.exe -ErrorAction SilentlyContinue
    if ($msCmd) { $msbuildPath = Split-Path $msCmd.Path -Parent }
} catch { }

if (-not $msbuildPath) {
    # Use vswhere first (most reliable)
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) { $vswhere = "$env:ProgramFiles\Microsoft Visual Studio\Installer\vswhere.exe" }
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationPath 2>$null
        if ($installPath) {
            foreach ($sub in @('MSBuild\Current\Bin\amd64', 'MSBuild\Current\Bin')) {
                $candidate = Join-Path $installPath $sub
                if (Test-Path (Join-Path $candidate 'msbuild.exe')) { $msbuildPath = $candidate; break }
            }
        }
    }
}

if (-not $msbuildPath) {
    $candidates = @(
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin',
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\amd64',
        'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64',
        'C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\amd64',
        'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\amd64',
        'C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\amd64'
    )
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c 'msbuild.exe')) { $msbuildPath = $c; break }
    }
}

if ($msbuildPath) {
    Write-Host "Found MSBuild at: $msbuildPath" -ForegroundColor Green
    $env:PATH = "$msbuildPath;$env:PATH"
} else {
    Write-Host "ERROR: MSBuild not found! Install Visual Studio Build Tools from https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OPC UA Server Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop any running server
Write-Host "[1/5] Stopping any running server..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq "server_json_config"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Step 2: Copy source to open62541 examples
Write-Host "[2/5] Copying source file to open62541 examples..." -ForegroundColor Yellow
$SourceFile = Join-Path $WorkingOpcDir "server_json_config.c"
$DestFile = Join-Path $Open62541Dir "examples\server_json_config.c"

if (-not (Test-Path $SourceFile)) {
    Write-Host "ERROR: Source file not found: $SourceFile" -ForegroundColor Red
    exit 1
}

Copy-Item -Force $SourceFile $DestFile
Write-Host "  Copied: $SourceFile" -ForegroundColor Gray
Write-Host "  To:     $DestFile" -ForegroundColor Gray

# Step 3: Configure (if needed) and build using CMake
Write-Host "[3/5] Building server_json_config..." -ForegroundColor Yellow
Set-Location $Open62541Dir

$BuildDir = Join-Path $Open62541Dir "build"
$CacheFile = Join-Path $BuildDir "CMakeCache.txt"
$ResolvedOpen62541Dir = (Resolve-Path $Open62541Dir).Path
$ExampleProject = Join-Path $BuildDir "examples\server_json_config.vcxproj"

if (Test-Path $CacheFile) {
    $cacheHomeMatch = Select-String -Path $CacheFile -Pattern "^CMAKE_HOME_DIRECTORY:INTERNAL=(.*)$" -ErrorAction SilentlyContinue
    if ($cacheHomeMatch -and $cacheHomeMatch.Matches.Count -gt 0) {
        $cacheHome = $cacheHomeMatch.Matches[0].Groups[1].Value
        if ($cacheHome) {
            # The cached source folder may no longer exist if the project was moved
            $resolvedCacheHome = (Resolve-Path $cacheHome -ErrorAction SilentlyContinue).Path
            if ($resolvedCacheHome -ne $ResolvedOpen62541Dir) {
                Write-Host "  CMake cache points to a different source directory. Reconfiguring..." -ForegroundColor Yellow
                Remove-Item -Recurse -Force $BuildDir
            }
        } else {
            Write-Host "  CMake cache missing source directory. Reconfiguring..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force $BuildDir
        }
    } else {
        Write-Host "  CMake cache missing source directory. Reconfiguring..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $BuildDir
    }
}

if ((Test-Path $BuildDir) -and (-not (Test-Path $ExampleProject))) {
    Write-Host "  Example target missing. Reconfiguring build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $BuildDir
}

if (-not (Test-Path $BuildDir)) {
    Write-Host "  Configuring CMake build directory..." -ForegroundColor Yellow
    $cmakeArgs = @('-S', $Open62541Dir, '-B', $BuildDir, '-A', 'x64', '-DUA_BUILD_EXAMPLES=ON')
    if ($OpenSslDir) { $cmakeArgs += '-DUA_ENABLE_ENCRYPTION_OPENSSL=ON' }
    & $CmakePath @cmakeArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: CMake configure failed!" -ForegroundColor Red
        exit 1
    }
}

& $CmakePath --build build --config Release --target server_json_config

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Build successful!" -ForegroundColor Green

# Step 4: Copy executable back to the server folder
Write-Host "[4/5] Copying executable to server folder..." -ForegroundColor Yellow
$BuiltExe = Join-Path $Open62541Dir "build\bin\examples\server_json_config.exe"
$DestExe = Join-Path $WorkingOpcDir "server_json_config.exe"

if (-not (Test-Path $BuiltExe)) {
    Write-Host "ERROR: Built executable not found: $BuiltExe" -ForegroundColor Red
    exit 1
}

Copy-Item -Force $BuiltExe $DestExe
Write-Host "  Copied: $BuiltExe" -ForegroundColor Gray
Write-Host "  To:     $DestExe" -ForegroundColor Gray

# Step 5: Ensure OpenSSL DLLs are present
Write-Host "[5/5] Checking OpenSSL DLLs..." -ForegroundColor Yellow
$cryptoDll = Get-ChildItem -Path $WorkingOpcDir -Filter "libcrypto-*.dll" -ErrorAction SilentlyContinue
$sslDll = Get-ChildItem -Path $WorkingOpcDir -Filter "libssl-*.dll" -ErrorAction SilentlyContinue

if (-not $cryptoDll -or -not $sslDll) {
    if ($OpenSslDir -and (Test-Path $OpenSslDir)) {
        Write-Host "  Copying OpenSSL DLLs..." -ForegroundColor Gray
        Get-ChildItem -Path $OpenSslDir -Filter "libcrypto-*.dll" | ForEach-Object { 
            Copy-Item -Force $_.FullName $WorkingOpcDir 
            Write-Host "  Copied: $($_.Name)" -ForegroundColor Gray
        }
        Get-ChildItem -Path $OpenSslDir -Filter "libssl-*.dll" | ForEach-Object { 
            Copy-Item -Force $_.FullName $WorkingOpcDir 
            Write-Host "  Copied: $($_.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  WARNING: OpenSSL not found, skipping DLL copy" -ForegroundColor Yellow
    }
} else {
    Write-Host "  OpenSSL DLLs already present" -ForegroundColor Gray
}

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " BUILD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the server, run:" -ForegroundColor Cyan
Write-Host '  .\server_json_config.exe "ps_server.json5"' -ForegroundColor White
Write-Host ""

Set-Location $WorkingOpcDir
