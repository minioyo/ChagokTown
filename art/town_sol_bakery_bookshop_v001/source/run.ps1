param([switch]$Preview)
$ErrorActionPreference = 'Stop'
$assetRoot = Split-Path -Parent $PSScriptRoot
$blenderPath = 'C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
$reportPath = Join-Path $assetRoot 'reports'
New-Item -ItemType Directory -Path $reportPath -Force | Out-Null
& $blenderPath --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'build_set.py') *> (Join-Path $reportPath 'build.log')
if ($LASTEXITCODE -ne 0) {
    Get-Content -LiteralPath (Join-Path $reportPath 'build.log') -Tail 30
    throw 'Blender generation failed.'
}
$renderArgs = @('--background', '--python-exit-code', '1', '--python', (Join-Path $PSScriptRoot 'render_verify.py'))
if ($Preview) { $renderArgs += @('--', '--preview') }
& $blenderPath @renderArgs *> (Join-Path $reportPath 'render.log')
if ($LASTEXITCODE -ne 0) {
    Get-Content -LiteralPath (Join-Path $reportPath 'render.log') -Tail 30
    throw 'Blender validation/rendering failed.'
}
Get-Content -LiteralPath (Join-Path $reportPath 'build.log') -Tail 4
Get-Content -LiteralPath (Join-Path $reportPath 'render.log') -Tail 5
