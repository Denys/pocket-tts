@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pocket_tts gradio --host 127.0.0.1 --port 7860 %*
  goto :eof
)

where pocket-tts >nul 2>nul
if %ERRORLEVEL%==0 (
  pocket-tts gradio --host 127.0.0.1 --port 7860 %*
  goto :eof
)

echo Pocket TTS Gradio could not start.
echo Expected .venv\Scripts\python.exe or pocket-tts on PATH.
pause
