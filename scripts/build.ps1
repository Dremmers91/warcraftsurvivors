param([switch]$OneFile)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$gamePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $gamePython)) { throw 'Run scripts/setup.ps1 first.' }
$buildMode = if ($OneFile) { '--onefile' } else { '--onedir' }
$buildName = if ($OneFile) { 'WarcraftSurvivorsOneFile' } else { 'WarcraftSurvivors' }
& $gamePython -m PyInstaller --noconfirm --clean --windowed $buildMode --name $buildName --icon 'src/warcraft_survivors/assets/game_icon.ico' --paths src --add-data 'src/warcraft_survivors/data:warcraft_survivors/data' --add-data 'src/warcraft_survivors/assets:warcraft_survivors/assets' run_game.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
Write-Output "Built $buildName ($buildMode). For onedir, distribute the entire folder."
