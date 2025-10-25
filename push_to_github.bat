@echo off
echo ============================================
echo Pushing to GitHub: Yololagidetesksiapi
echo ============================================
echo.

REM Configure git (change this if needed)
git config user.name "Nexuszzz"
git config user.email "your.email@example.com"

REM Check git status
echo [1/4] Checking git status...
git status

echo.
echo [2/4] Staging all files...
git add .

echo.
echo [3/4] Committing...
git commit -m "Initial commit: ESP32-CAM Fire Detection with YOLOv10"

echo.
echo [4/4] Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ============================================
echo Done! Check: https://github.com/Nexuszzz/Yololagidetesksiapi
echo ============================================
pause
