param([switch]$Preview)
$ErrorActionPreference = 'Stop'
$assetRoot = Split-Path -Parent $PSScriptRoot
$blenderPath = 'C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
& $blenderPath --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'build_set.py') *> (Join-Path $assetRoot 'reports/build.log')
if ($LASTEXITCODE -ne 0) { Get-Content -LiteralPath (Join-Path $assetRoot 'reports/build.log') -Tail 25; throw 'Generation failed.' }
$renderArgs = @('--background', '--python-exit-code', '1', '--python', (Join-Path $PSScriptRoot 'render_verify.py'))
if ($Preview) { $renderArgs += @('--', '--preview') }
& $blenderPath @renderArgs *> (Join-Path $assetRoot 'reports/render.log')
if ($LASTEXITCODE -ne 0) { Get-Content -LiteralPath (Join-Path $assetRoot 'reports/render.log') -Tail 25; throw 'Validation/rendering failed.' }
Get-Content -LiteralPath (Join-Path $assetRoot 'reports/render.log') -Tail 5
