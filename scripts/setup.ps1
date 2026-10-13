$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) {
  python -m venv --without-pip .venv
  if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment. Check your Python installation.' }
  python -m pip --python .venv install -r requirements-lock.txt
} else {
  & '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
}
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
