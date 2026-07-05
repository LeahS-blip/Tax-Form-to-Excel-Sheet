@echo off
setlocal
REM ============================================================
REM  Drag one or more tax PDFs onto this icon to extract them
REM  to Excel. Each PDF becomes a workbook in "Extracted workbooks".
REM  A combined packet (1040 + schedules + K-1s in one PDF) is
REM  split into one tab per form automatically.
REM ============================================================

set "PY=C:\Python314\python.exe"
set "CLI=C:\Users\leahs\OneDrive\Documents\PDF to Excel\tax_extractor\tax_extractor\cli.py"
set "OUTDIR=C:\Users\leahs\OneDrive\Documents\PDF to Excel\Extracted workbooks"

if "%~1"=="" (
  echo.
  echo   Drag one or more tax PDFs onto this icon to extract them to Excel.
  echo   Nothing was dropped, so there is nothing to do.
  echo.
  pause
  exit /b 0
)

if not exist "%PY%" (
  echo [ERROR] Python not found at "%PY%".
  echo Edit this file and set PY to your python.exe path.
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
