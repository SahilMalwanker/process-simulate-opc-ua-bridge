@echo off
REM Change to the directory where this script is located
cd /d "%~dp0"

REM Run the server with the config
.\server_json_config.exe "ps_server.json5"

pause