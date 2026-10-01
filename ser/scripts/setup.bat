@echo off
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo.
echo ============================================
echo   음성 감정인식 - 환경 설치
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [FAIL] python 을 찾을 수 없습니다. Python 3.10~3.11 을 설치하고
  echo        설치 중 "Add python.exe to PATH" 를 체크하세요.
  pause & exit /b 1
)
python -c "import sys;v=sys.version_info;print('python %%d.%%d.%%d'%%v[:3]);sys.exit(0 if (3,9)<=v[:2]<=(3,12) else 1)"
if errorlevel 1 (
  echo [WARN] 3.10 ~ 3.12 를 권장합니다. 계속하려면 아무 키나 누르세요.
  pause >nul
)

if not exist .venv (
  echo [1/4] 가상환경 생성...
  python -m venv .venv
) else (
  echo [1/4] 가상환경 이미 있음 - 건너뜀
)
call .venv\Scripts\activate.bat

echo [2/4] pip 업그레이드...
python -m pip install --upgrade pip -q

echo [3/4] PyTorch (CUDA 12.1) 설치... 약 2.5GB, 5~15분 걸립니다
pip install torch==2.4.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
  echo [FAIL] torch 설치 실패. 네트워크를 확인하고 다시 실행하세요.
  pause & exit /b 1
)

echo [4/4] 나머지 패키지 설치...
pip install -q transformers==4.44.2 peft==0.12.0 librosa==0.10.2.post1 soundfile==0.12.1 ^
            numpy==1.26.4 pandas==2.2.2 scikit-learn==1.5.1 PyYAML==6.0.2 tqdm matplotlib ^
            fastapi "uvicorn[standard]" python-multipart
if errorlevel 1 ( echo [FAIL] 패키지 설치 실패 & pause & exit /b 1 )

echo.
echo ============================================
echo   설치 완료 - 사전 점검을 실행합니다
echo ============================================
echo.
python src\quickcheck.py --config configs\base.yaml
echo.
echo 다음: run_all.bat pilot   (빠른 검증)  또는  run_all.bat full  (본 학습)
pause
