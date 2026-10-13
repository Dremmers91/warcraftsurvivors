$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$gamePython = '.\.venv\Scripts\python.exe'
& $gamePython -m ruff check src tests scripts run_game.py
if ($LASTEXITCODE -ne 0) { throw 'Lint failed.' }
& $gamePython -m ruff format --check src tests scripts run_game.py
if ($LASTEXITCODE -ne 0) { throw 'Formatting failed.' }
& $gamePython -m mypy
if ($LASTEXITCODE -ne 0) { throw 'Type checking failed.' }
& $gamePython -m pytest
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $gamePython scripts\validate_assets.py
if ($LASTEXITCODE -ne 0) { throw 'Asset validation failed.' }
foreach ($zoneId in @('elwynn','duskwood','stranglethorn','plaguelands','icecrown')) {
  foreach ($classId in @('paladin','warrior','mage','hunter','warlock','priest')) {
    & $gamePython run_game.py --smoke-test --zone $zoneId --class $classId --save-dir 'artifacts/milestone5/source/save' --screenshot "artifacts/milestone5/source/$zoneId-$classId.png"
    if ($LASTEXITCODE -ne 0) { throw "Launch smoke failed: $zoneId / $classId" }
  }
  & $gamePython run_game.py --smoke-test --zone $zoneId --encounter-smoke --save-dir 'artifacts/milestone5/source/save' --screenshot "artifacts/milestone5/source/$zoneId-boss.png"
  if ($LASTEXITCODE -ne 0) { throw "Boss launch smoke failed: $zoneId" }
}
foreach ($screenName in @('main','classes','zones','settings','progression','talents','shop','achievements','unlocks')) {
  & $gamePython run_game.py --smoke-test --screen-smoke $screenName --save-dir 'artifacts/milestone5/source/save' --screenshot "artifacts/milestone5/source/$screenName.png"
  if ($LASTEXITCODE -ne 0) { throw "Progression screen smoke failed: $screenName" }
}
