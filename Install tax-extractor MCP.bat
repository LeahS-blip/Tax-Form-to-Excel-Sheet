@echo off
setlocal
echo ==================================================
echo   tax-extractor MCP server  -  dependency setup
echo ==================================================
echo.

REM Use the same "python" that Claude Desktop will launch from your PATH.
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found on your PATH.
  echo Install Python 3.10+ from https://www.python.org/downloads/
  echo During install, tick "Add python.exe to PATH", then re-run this file.
  echo.
  pause
  exit /b 1
)

echo This Python will be used (it must be the same one Claude Desktop uses):
where python
python --version
echo.

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install "pdfplumber>=0.11" "openpyxl>=3.1" "mcp[cli]>=1.2" "reportlab>=4.0"
if errorlevel 1 (
  echo.
  echo [ERROR] Package install failed. See the messages above.
  pause
  exit /b 1
)

echo.
echo Verifying the server's core dependencies import cleanly...
python -c "import mcp, pdfplumber, openpyxl; print('  core deps OK')"
if errorlevel 1 (
  echo [ERROR] Imports failed. The packages may have installed into a different Python.
  pause
  exit /b 1
)

echo.
echo OPTIONAL - LLM engine for odd / non-standard layouts (sends text to Anthropic API):
echo   python -m pip install "anthropic>=0.40"
echo   then set an ANTHROPIC_API_KEY environment variable.
echo.
echo Done. Next steps are in: SETUP - tax-extractor MCP server.md
pause
