@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "REPO_DIR=%SCRIPT_DIR%.."
set "VENV_PY=%REPO_DIR%\.venv\Scripts\python.exe"

pushd "%REPO_DIR%" >nul || (
  echo ERROR: failed to open repository directory: "%REPO_DIR%"
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo STEP: creating virtual environment .venv
  py -3 -m venv .venv || python -m venv .venv || (
    echo ERROR: Python not found ^(neither py nor python^)
    popd >nul
    exit /b 1
  )
)

if not exist "%VENV_PY%" (
  echo ERROR: python.exe not found in .venv after environment creation
  popd >nul
  exit /b 1
)

echo STEP: upgrading pip
"%VENV_PY%" -m pip install --upgrade pip || (
  echo ERROR: pip upgrade failed
  popd >nul
  exit /b 1
)

echo STEP: installing project
"%VENV_PY%" -m pip install -e . || (
  echo ERROR: project install failed
  popd >nul
  exit /b 1
)

echo STEP: running setup wizard
"%VENV_PY%" -m telethon_fancifier.cli setup || (
  echo ERROR: setup wizard failed
  popd >nul
  exit /b 1
)

popd >nul
echo Done: setup completed.
exit /b 0
