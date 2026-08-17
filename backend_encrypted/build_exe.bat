@echo off
REM ============================================================
REM  TaNix Alpha 2.0  -  Build single Windows .exe
REM  Run this ONCE on your Windows PC (Python 3.11 64-bit)
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo [1/3] Installing dependencies + PyInstaller ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [2/3] Building the .exe (this can take several minutes)...

pyinstaller --noconfirm --clean --console --name TaNixAlpha2.0 ^
  --add-data "bot.py;." ^
  --add-data "start.py;." ^
  --add-data "sessions.py;." ^
  --add-data "strategies.py;." ^
  --add-data "qx.py;." ^
  --add-data "analysis.py;." ^
  --add-data "charting.py;." ^
  --add-data "notifier.py;." ^
  --add-data "messages.py;." ^
  --add-data "storage.py;." ^
  --add-data "ticks.py;." ^
  --add-data "indicators_py.py;." ^
  --add-data "config.py;." ^
  --add-data "get_chat_id.py;." ^
  --add-data "pyquotex;pyquotex" ^
  --add-data "pyarmor_runtime_000000;pyarmor_runtime_000000" ^
  --collect-all telegram ^
  --collect-all httpx ^
  --collect-all aiogram ^
  --collect-all aiohttp ^
  --collect-all matplotlib ^
  --collect-all numpy ^
  --collect-all certifi ^
  --collect-all fake_useragent ^
  --collect-all bs4 ^
  --collect-all pydantic ^
  --hidden-import orjson ^
  --hidden-import websocket ^
  --hidden-import requests ^
  --hidden-import urllib3 ^
  --hidden-import pyfiglet ^
  --hidden-import Brotli ^
  --hidden-import brotli ^
  --hidden-import dotenv ^
  --hidden-import magic_filter ^
  --hidden-import apscheduler ^
  main.py

echo.
echo [3/3] Copying .env and data next to the exe ...
if exist ".env" copy /Y ".env" "dist\TaNixAlpha2.0\.env" >nul
if exist ".env.example" copy /Y ".env.example" "dist\TaNixAlpha2.0\.env.example" >nul
if exist "data" xcopy /E /I /Y "data" "dist\TaNixAlpha2.0\data" >nul

REM ---- create a safe launcher that keeps the window open + logs everything ----
(
echo @echo off
echo cd /d "%%~dp0"
echo TaNixAlpha2.0.exe ^> run_log.txt 2^>^&1
echo echo.
echo echo ---------- run_log.txt ----------
echo type run_log.txt
echo pause
) > "dist\TaNixAlpha2.0\run.bat"


echo.
echo ============================================================
echo  DONE!
echo  Your app folder:  dist\TaNixAlpha2.0\
echo  Run it:           dist\TaNixAlpha2.0\TaNixAlpha2.0.exe
echo  (Put your real .env inside that folder before running.)
echo ============================================================
pause
