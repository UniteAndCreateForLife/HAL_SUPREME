[CmdletBinding()]
param(
    [string]$RuntimeRoot = "$env:USERPROFILE\HAL_RUNTIME\LightX2V",
    [string]$ModelRoot = "$env:USERPROFILE\HAL_MODELS\Wan2.2-TI2V-5B",
    [string]$EnvName = "hal-lightx2v",
    [switch]$Install,
    [switch]$DownloadModel
)

$ErrorActionPreference = "Stop"

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

Require-Command "nvidia-smi"
Require-Command "git"
Require-Command "conda"

Write-Host "=== GPU ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
Write-Host "=== Runtime root === $RuntimeRoot"
Write-Host "=== Model root === $ModelRoot"

if (-not $Install) {
    Write-Host ""
    Write-Host "Dry-run only. Re-run with -Install to create the isolated runtime."
    Write-Host "Add -DownloadModel to fetch Wan2.2-TI2V-5B."
    exit 0
}

if (-not (Test-Path $RuntimeRoot)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $RuntimeRoot) | Out-Null
    git clone https://github.com/ModelTC/LightX2V.git $RuntimeRoot
}

$envList = conda env list
if ($envList -notmatch [regex]::Escape($EnvName)) {
    conda create -n $EnvName python=3.12 -y
}

conda run -n $EnvName python -m pip install --upgrade pip
conda run -n $EnvName python -m pip install torch==2.6.0+cu124 torchvision==0.21.0+cu124 torchaudio==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
conda run -n $EnvName python -m pip install -r "$RuntimeRoot\requirements_win.txt"
conda run -n $EnvName python -m pip install -v -e $RuntimeRoot
conda run -n $EnvName python -m pip install huggingface_hub

if ($DownloadModel) {
    New-Item -ItemType Directory -Force -Path $ModelRoot | Out-Null
    conda run -n $EnvName python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Wan-AI/Wan2.2-TI2V-5B', local_dir=r'$ModelRoot')"
}

$pythonPath = (conda run -n $EnvName python -c "import sys; print(sys.executable)" | Select-Object -Last 1).Trim()

Set-Item Env:HAL_LIGHTX2V_PYTHON $pythonPath
Set-Item Env:HAL_LIGHTX2V_ROOT $RuntimeRoot
Set-Item Env:HAL_WAN22_TI2V5B_MODEL $ModelRoot
Set-Item Env:HAL_LIGHTX2V_CONFIG "configs/lightx2v/wan22_ti2v_5b_turing_8gb.json"

Write-Host ""
Write-Host "Runtime installed and environment variables configured for this shell."
Write-Host "Doctor: python scripts/nightmare_runtime_doctor.py"
Write-Host "Canary: python scripts/run_lightx2v_canary.py"
Write-Host "No public endpoint is created and no upload is performed."
