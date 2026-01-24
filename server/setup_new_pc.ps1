# setup_new_pc.ps1
# Run this script on a new PC to configure the OPC UA server for that machine.
# It auto-detects hostname and IP, updates ps_server.json5, and regenerates certificates.

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OPC UA Server - New PC Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory (server folder)
$WorkingOpcDir = $PSScriptRoot
Set-Location $WorkingOpcDir

# ============================================
# Step 1: Detect hostname and IP
# ============================================
Write-Host "[1/4] Detecting hostname and IP address..." -ForegroundColor Yellow

$Hostname = $env:COMPUTERNAME
Write-Host "  Hostname: $Hostname" -ForegroundColor Green

# Get the primary IP address (prefer IPv4, non-loopback)
$IpAddress = $null
$adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.PrefixOrigin -ne "WellKnown"
} | Sort-Object -Property InterfaceIndex

if ($adapters) {
    $IpAddress = $adapters[0].IPAddress
}

if (-not $IpAddress) {
    # Fallback: use hostname resolution
    $IpAddress = [System.Net.Dns]::GetHostAddresses($Hostname) | 
        Where-Object { $_.AddressFamily -eq 'InterNetwork' } | 
        Select-Object -First 1 -ExpandProperty IPAddressToString
}

if (-not $IpAddress) {
    Write-Host "ERROR: Could not detect IP address. Please specify manually." -ForegroundColor Red
    $IpAddress = Read-Host "Enter IP address"
}

Write-Host "  IP Address: $IpAddress" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 2: Update ps_server.json5
# ============================================
Write-Host "[2/4] Updating ps_server.json5..." -ForegroundColor Yellow

$ConfigFile = Join-Path $WorkingOpcDir "ps_server.json5"

if (-not (Test-Path $ConfigFile)) {
    Write-Host "ERROR: ps_server.json5 not found at: $ConfigFile" -ForegroundColor Red
    exit 1
}

$configContent = Get-Content $ConfigFile -Raw

# Build the new applicationUri
$NewAppUri = "urn:${Hostname}:open62541:ps"
$NewEndpoint = "opc.tcp://${IpAddress}:4841"

# Replace applicationUri (matches pattern like: applicationUri: "urn:...:open62541:ps")
$configContent = $configContent -replace 'applicationUri:\s*"urn:[^"]*:open62541:ps"', "applicationUri: `"$NewAppUri`""

# Replace discoveryUrls (matches pattern like: "opc.tcp://...:4841")
$configContent = $configContent -replace '"opc\.tcp://[^"]*:4841"', "`"$NewEndpoint`""

# Write updated config
Set-Content -Path $ConfigFile -Value $configContent -NoNewline

Write-Host "  Updated applicationUri: $NewAppUri" -ForegroundColor Green
Write-Host "  Updated endpoint: $NewEndpoint" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 3: Generate new certificates
# ============================================
Write-Host "[3/4] Generating new certificates..." -ForegroundColor Yellow

$GenerateCertScript = Join-Path $WorkingOpcDir "generate_cert.py"

if (-not (Test-Path $GenerateCertScript)) {
    Write-Host "ERROR: generate_cert.py not found at: $GenerateCertScript" -ForegroundColor Red
    exit 1
}

# Check if Python is available
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found. Please install Python 3.7+ and add to PATH." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Using Python: $pythonCmd" -ForegroundColor Gray

# Check if cryptography package is installed
$cryptoCheck = & $pythonCmd -c "import cryptography" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing cryptography package..." -ForegroundColor Gray
    & $pythonCmd -m pip install cryptography --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install cryptography package." -ForegroundColor Red
        exit 1
    }
}

# Generate certificates
& $pythonCmd $GenerateCertScript $Hostname $IpAddress

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Certificate generation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Certificates generated successfully" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 4: Verify setup
# ============================================
Write-Host "[4/4] Verifying setup..." -ForegroundColor Yellow

$certFile = Join-Path $WorkingOpcDir "open62541_server_cert.der"
$keyFile = Join-Path $WorkingOpcDir "open62541_server_key.pem"
$exeFile = Join-Path $WorkingOpcDir "server_json_config.exe"

$allGood = $true

if (Test-Path $certFile) {
    Write-Host "  [OK] Certificate: $certFile" -ForegroundColor Green
} else {
    Write-Host "  [MISSING] Certificate: $certFile" -ForegroundColor Red
    $allGood = $false
}

if (Test-Path $keyFile) {
    Write-Host "  [OK] Private key: $keyFile" -ForegroundColor Green
} else {
    Write-Host "  [MISSING] Private key: $keyFile" -ForegroundColor Red
    $allGood = $false
}

if (Test-Path $exeFile) {
    Write-Host "  [OK] Server executable: $exeFile" -ForegroundColor Green
} else {
    Write-Host "  [MISSING] Server executable: $exeFile" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

# ============================================
# Done
# ============================================
if ($allGood) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " SETUP COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration summary:" -ForegroundColor Cyan
    Write-Host "  Hostname:       $Hostname"
    Write-Host "  IP Address:     $IpAddress"
    Write-Host "  Application URI: $NewAppUri"
    Write-Host "  Endpoint URL:   $NewEndpoint"
    Write-Host ""
    Write-Host "To start the server, run:" -ForegroundColor Cyan
    Write-Host '  .\server_json_config.exe "ps_server.json5"' -ForegroundColor White
    Write-Host ""
    Write-Host "In Process Simulate, connect to:" -ForegroundColor Cyan
    Write-Host "  $NewEndpoint" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " SETUP INCOMPLETE - See errors above" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
