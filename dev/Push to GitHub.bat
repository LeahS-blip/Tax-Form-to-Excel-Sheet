@echo off
setlocal
REM ============================================================
REM  Maintainer helper: commit this project and push to GitHub.
REM  Repo: https://github.com/LeahS-blip/PDF-to-Excel-Sheet
REM  Client data (Drop / Extracted folders) is excluded via .gitignore.
REM  The first push opens a browser to sign in to GitHub if needed.
REM ============================================================

cd /d "%~dp0.."

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git is not installed. Get it from https://git-scm.com/download/win
  pause
  exit /b 1
)

if not exist ".git" (
  git init
  git branch -M main
  git remote add origin https://github.com/LeahS-blip/PDF-to-Excel-Sheet.git
)

git add .
git commit -m "Update Tax Form to Excel skill"

echo.
echo Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push failed. If GitHub already has commits you don't have locally, run:
  echo     git pull origin main --allow-unrelated-histories
  echo     git push -u origin main
)
echo.
echo Reminder - these are excluded and must NOT be uploaded:
echo   - Drop tax forms here\   - Extracted workbooks\   - *_extracted.xlsx
pause
