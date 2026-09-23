@echo off
cd /d "%~dp0"
start "HAL Campus Evidence Desk" http://127.0.0.1:8789
python app.py
