@echo off
chcp 65001 > nul
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist .venv\Scripts\activate.bat (
  echo [FAIL] run setup.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat

set MODE=%1
if "%MODE%"=="" set MODE=pilot
set CFG=
if /I "%MODE%"=="pilot" set CFG=configs\pilot.yaml
if /I "%MODE%"=="full"  set CFG=configs\base.yaml
if not defined CFG (
  echo usage: run_all.bat [pilot^|full]
  echo   pilot : high-confidence subset, 5 epochs, 2-3 h
  echo   full  : all data, 20 epochs, 8-14 h
  pause
  exit /b 1
)

if not exist work mkdir work
if not exist logs mkdir logs
set TS=%RANDOM%
for /f "tokens=1-4 delims=/: " %%a in ("%TIME%") do set TS=%%a%%b

echo.
echo ============================================
echo   mode: %MODE%    config: %CFG%
echo ============================================
echo.

echo [0/5] pre-flight check ------------------------
python src\quickcheck.py --config %CFG%
if errorlevel 1 (
  echo.
  echo [STOP] pre-flight failed. Fix the [FAIL] items above.
  pause
  exit /b 1
)

echo.
echo [1/5] EDA report ------------------------------ (~1 min)
python src\eda_report.py --config %CFG% --out work\eda
if errorlevel 1 ( echo [FAIL] eda & pause & exit /b 1 )

echo.
echo [2/5] label manifest -------------------------- (2-5 min)
python src\build_manifest.py --config %CFG%
if errorlevel 1 ( echo [FAIL] manifest & pause & exit /b 1 )

echo.
echo [3/5] audio 48k -^> 16k cache ------------------ (30-70 min, one time only)
python src\preprocess_audio.py --config %CFG% --workers 8
if errorlevel 1 ( echo [FAIL] preprocess & pause & exit /b 1 )

echo.
if exist work\manifest_split.csv copy /Y work\manifest_split.csv work\manifest_split_prev.csv >nul
echo [4/5] speaker-independent split --------------- (instant)
python src\split.py --config %CFG%
if errorlevel 1 ( echo [FAIL] split & pause & exit /b 1 )

echo.
echo [5/5] training -------------------------------- (pilot 2-3 h / full 8-14 h)
echo       Ctrl+C is safe - best.pt is kept.
python src\train.py --config %CFG% --run %MODE%_%TS%
if errorlevel 1 ( echo [FAIL] train & pause & exit /b 1 )

echo.
echo ============================================
echo   DONE.  checkpoint: work\ckpt\%MODE%_%TS%\best.pt
echo.
echo   evaluate:
echo     python src\evaluate.py --ckpt work\ckpt\%MODE%_%TS%\best.pt --split test
echo ============================================
pause
