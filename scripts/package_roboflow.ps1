param(
    [string]$Source = "data\roboflow_export",
    [double]$ValRatio = 0.2,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Get-ProjectPython {
    $candidates = @(
        (Join-Path $root ".venv\Scripts\python.exe"),
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        try {
            $output = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "No working Python found. Install Python 3.11+, then recreate .venv and install requirements.txt."
}

$python = Get-ProjectPython
if ([System.IO.Path]::IsPathRooted($Source)) {
    $sourceCandidate = $Source
} else {
    $sourceCandidate = Join-Path $root $Source
}
$sourcePath = Resolve-Path -Path $sourceCandidate -ErrorAction Stop

$packageArgs = @(
    (Join-Path $root "training\02_package_dataset.py"),
    "--source", $sourcePath.Path,
    "--val-ratio", $ValRatio
)
if ($Clean) {
    $packageArgs += "--clean"
}

& $python @packageArgs
& $python (Join-Path $root "training\03_validate_dataset.py") --dataset-dir (Join-Path $root "dataset")

$zipPath = Join-Path $root "dataset.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -Path (Join-Path $root "dataset") -DestinationPath $zipPath -Force
Write-Host "Created $zipPath"
Write-Host "Upload dataset.zip to Google Drive: MyDrive/SmartHospital/dataset.zip"
