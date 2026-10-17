@echo off
setlocal
REM ============================================================
REM  Drag one or more tax PDFs onto this icon to extract them
REM  to Excel. Each PDF becomes a workbook in "Extracted workbooks"
REM  (next to this project folder). A combined packet (1040 +
REM  schedules + K-1s in one PDF) is split into one tab per form.
REM ============================================================

REM Paths are relative to this file, so the folder can live anywhere.
set "ROOT=%~dp0.."
set "CLI=%ROOT%\scripts\cli.py"
set "OUTDIR=%ROOT%\Extracted workbooks"

REM Use python on PATH; set PY to a full path if you have several Pythons.
set "PY=python"

if "%~1"=="" (
  echo.
  echo   Drag one or more tax PDFs onto this icon to extract them to Excel.
  echo   Nothing was dropped, so there is nothing to do.
  echo.
  pause
  exit /b 0
)

"%PY%" --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found. Run "Install dependencies.bat" first,
  echo or edit this file and set PY to the full path of python.exe.
  pause
  exit /b 1
)
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

:loop
if "%~1"=="" goto done
echo.
echo Extracting "%~nx1" ...
"%PY%" "%CLI%" "%~1" -o "%OUTDIR%\%~n1_extracted.xlsx"
shift
goto loop

:done
echo.
echo Done. Workbooks saved in:
echo   %OUTDIR%
echo Verify any amber (low-confidence) or red (missing) cells against the PDF.
start "" "%OUTDIR%"
pause
