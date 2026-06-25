param(
    [double]$ValRatio = 0.2,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = "python"

$argsList = @(
    (Join-Path $root "training\04_merge_roboflow_exports.py"),
    "--source", (Join-Path $root "data\roboflow_export\LaTuan.v1i.yolov8"),
    "--source", (Join-Path $root "data\roboflow_export\LaTuan.v1i.yolov8 (1)"),
    "--dataset-dir", (Join-Path $root "dataset"),
    "--val-ratio", $ValRatio,
    "--zip-output", (Join-Path $root "dataset.zip")
)

if ($Clean) {
    $argsList += "--clean"
}

& $python @argsList
& $python (Join-Path $root "training\03_validate_dataset.py") --dataset-dir (Join-Path $root "dataset")

Write-Host ""
Write-Host "Ready for Colab upload:"
Write-Host "  dataset.zip"
