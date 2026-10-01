@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
REM Docker helper (Makefile substitute for Windows)
REM   run bake work\ckpt\pilot_1234\best.pt
REM   run demo | train | save | load | down

if "%1"=="bake" (
  if not exist model mkdir model
  copy /Y "%2" model\best.pt
  dir model\best.pt
  goto :eof
)
if "%1"=="demo" (
  docker compose build demo
  if errorlevel 1 goto :eof
  docker compose up -d demo
  echo.
  echo   -^> http://localhost:8000   ^(takes 30-60 s to boot^)
  echo      docker compose logs -f demo
  goto :eof
)
if "%1"=="train" ( docker compose --profile train run --rm train all & goto :eof )
if "%1"=="save"  ( docker save ser-demo:1.0 -o ser-demo.tar & dir ser-demo.tar & goto :eof )
if "%1"=="load"  ( docker load -i ser-demo.tar & goto :eof )
if "%1"=="down"  ( docker compose down -v & goto :eof )
echo usage: run [bake ^<ckpt^> ^| demo ^| train ^| save ^| load ^| down]
