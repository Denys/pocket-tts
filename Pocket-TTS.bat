@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\pocket-tts.exe" (
  ".venv\Scripts\pocket-tts.exe" app
  goto :eof
)

where uvx >nul 2>nul
if %ERRORLEVEL%==0 (
  uvx --from "pocket-tts[desktop]" pocket-tts app
  goto :eof
)

pocket-tts app
