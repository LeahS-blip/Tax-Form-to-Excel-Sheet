@echo off
setlocal
REM ============================================================
REM  Commit this folder and push it to GitHub.
REM  Repo: https://github.com/LeahS-blip/PDF-to-Excel-Sheet
REM  Client data (Drop / Extracted folders) is excluded via .gitignore.
REM  The first push opens a browser to sign in to GitHub if needed.
REM ============================================================

cd /d "C:\Users\leahs\OneDrive\Documents\PDF to Excel"

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git is not installed. Get it from https://git-scm.com/download/win
  pause
  exit /b 1
)

REM Clear any half-initialized repo left behind, for a clean start.
if exist ".git" (
  echo Removing existing .git folder for a clean init...
  rmdir /s /q ".git"
)

git init
git branch -M main
git add .
git commit -m "Initial commit: Tax Form to Excel Sheet extractor + Claude MCP setup"

git remote remove origin >nul 2>&1
git remote add origin https://github.com/LeahS-blip/PDF-to-Excel-Sheet.git

echo.
echo Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push failed. Most common cause: the GitHub repo already has a commit
  echo (e.g. a README made on github.com). To reconcile, run:
  echo     git pull origin main --allow-unrelated-histories
  echo     git push -u origin main
)
echo.
echo Done. Review the excluded files below are NOT uploaded:
echo   - Drop tax forms here\   - Extracted workbooks\   - *_extracted.xlsx
pause
