param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$dirs = @(
    "data\raw_videos",
    "data\raw_videos\Binh_Thuong",
    "data\raw_videos\Nam_Tay",
    "data\raw_videos\Chi_Ngon_Tro",
    "data\raw_videos\Xoe_Tay",
    "data\frames",
    "data\roboflow_export",
    "dataset",
    "models"
)

foreach ($dir in $dirs) {
    $path = Join-Path $root $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

Write-Host "Training workspace is ready."
Write-Host ""
Write-Host "Drop raw videos into either:"
Write-Host "  data\raw_videos\binh_thuong.mp4"
Write-Host "  data\raw_videos\nam_tay.mp4"
Write-Host "  data\raw_videos\chi_ngon.mp4"
Write-Host "  data\raw_videos\xoe_tay.mp4"
Write-Host ""
Write-Host "Or use class folders:"
Write-Host "  data\raw_videos\Binh_Thuong\clip_001.mp4"
Write-Host "  data\raw_videos\Nam_Tay\clip_001.mp4"
Write-Host "  data\raw_videos\Chi_Ngon_Tro\clip_001.mp4"
Write-Host "  data\raw_videos\Xoe_Tay\clip_001.mp4"
Write-Host ""
Write-Host "After recording:"
Write-Host "  .\scripts\extract_after_recording.cmd -Clean"
Write-Host ""
Write-Host "After Roboflow YOLOv8 export is unzipped into data\roboflow_export:"
Write-Host "  .\scripts\package_roboflow.cmd -Source data\roboflow_export -Clean"
