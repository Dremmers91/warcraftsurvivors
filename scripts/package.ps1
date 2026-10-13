param([switch]$IncludeOneFile)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$releaseRoot = Join-Path $projectRoot 'dist\WarcraftSurvivors'
if (-not (Test-Path -LiteralPath (Join-Path $releaseRoot 'WarcraftSurvivors.exe'))) {
  throw 'Run scripts/build.ps1 before packaging.'
}
$verifiedReport = Join-Path $projectRoot 'artifacts\milestone5\executable\validation.json'
if (-not (Test-Path -LiteralPath $verifiedReport)) { throw 'Run scripts/verify_build.py before packaging.' }
$validation = Get-Content -LiteralPath $verifiedReport -Raw | ConvertFrom-Json
$binaryHash = (Get-FileHash -LiteralPath (Join-Path $releaseRoot 'WarcraftSurvivors.exe') -Algorithm SHA256).Hash
if ($binaryHash -ne $validation.executable_sha256) { throw 'Executable changed after validation. Run scripts/verify_build.py again.' }
foreach ($resource in $validation.resource_hashes.PSObject.Properties) {
  $resourcePath = Join-Path $releaseRoot $resource.Name
  if ((Get-FileHash -LiteralPath $resourcePath -Algorithm SHA256).Hash -ne $resource.Value) { throw "Resource changed after validation: $($resource.Name)" }
}
Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') -Destination $releaseRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -Destination $releaseRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'docs\QA.md') -Destination $releaseRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'docs\ASSET_CREDITS.md') -Destination $releaseRoot
$releaseDocs = Join-Path $releaseRoot 'docs'
New-Item -ItemType Directory -Path $releaseDocs -Force | Out-Null
foreach ($docName in @('QA.md','CONTENT_CATALOG.md','ENCOUNTER_CATALOG.md','ZONE_CATALOG.md','PROGRESSION_CATALOG.md','SAVE_FORMAT.md','GAME_DESIGN.md','MILESTONE5_REPORT.md','ARCHITECTURE.md','ASSET_CREDITS.md','ASSET_PIPELINE.md')) {
  Copy-Item -LiteralPath (Join-Path $projectRoot "docs\$docName") -Destination $releaseDocs
}
$releaseScreens = Join-Path $releaseDocs 'screenshots'
New-Item -ItemType Directory -Path $releaseScreens -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'docs\screenshots\milestone5') -Destination $releaseScreens -Recurse -Force
$gamePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$releaseVersion = & $gamePython -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
if ($LASTEXITCODE -ne 0) { throw 'Could not read release version.' }
$archiveName = "WarcraftSurvivors-$releaseVersion-Windows.zip"
Compress-Archive -LiteralPath $releaseRoot -DestinationPath (Join-Path $projectRoot "dist\$archiveName") -Force
Write-Output "Packaged dist\$archiveName"
if ($IncludeOneFile) {
  $oneFileExe = Join-Path $projectRoot 'dist\WarcraftSurvivorsOneFile.exe'
  $oneFileReport = Join-Path $projectRoot 'artifacts\milestone5\executable-onefile\validation.json'
  if (-not (Test-Path -LiteralPath $oneFileReport)) { throw 'Validate the optional onefile executable first.' }
  $oneFileValidation = Get-Content -LiteralPath $oneFileReport -Raw | ConvertFrom-Json
  if ((Get-FileHash -LiteralPath $oneFileExe -Algorithm SHA256).Hash -ne $oneFileValidation.executable_sha256) { throw 'Onefile executable changed after validation.' }
  $oneFileArchive = Join-Path $projectRoot "dist\WarcraftSurvivors-$releaseVersion-Windows-OneFile.zip"
  Compress-Archive -LiteralPath $oneFileExe,(Join-Path $projectRoot 'README.md'),(Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -DestinationPath $oneFileArchive -Force
  Write-Output "Packaged optional onefile: $oneFileArchive"
}
