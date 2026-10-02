@echo off
chcp 65001 > nul
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat ( echo [FAIL] run setup.bat first. & pause & exit /b 1 )
call .venv\Scripts\activate.bat

python -c "import jupyterlab" 2>nul || (
  echo installing jupyterlab ... a few minutes
  pip install -q jupyterlab ipywidgets ipykernel
)

echo registering kernel "SER (venv)" ...
python -m ipykernel install --user --name ser --display-name "SER (venv)" >nul 2>&1

echo.
echo   JupyterLab starting from: %CD%
echo   IMPORTANT: pick kernel "SER (venv)" (top right) if asked
echo   press Ctrl+C twice to stop
echo.
jupyter lab
