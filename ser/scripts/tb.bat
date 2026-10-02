@echo off
chcp 65001 > nul
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat ( echo [FAIL] run setup.bat first. & pause & exit /b 1 )
call .venv\Scripts\activate.bat
python -c "import tensorboard" 2>nul || pip install -q tensorboard tabulate
echo.
echo   TensorBoard -^> http://localhost:6006
echo   press Ctrl+C to stop
echo.
start "" http://localhost:6006
tensorboard --logdir work\tb --port 6006
