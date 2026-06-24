@echo off
chcp 65001 >nul 2>nul
echo ============================================================
echo   PRStudy Build Script
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller -q
)

if exist "build" rmdir /s /q "build"

echo [INFO] Preparing runtime resources...
if exist "dist\jre" (
    echo [INFO] Copying dist\jre to project root...
    xcopy /E /I /Y "dist\jre" "jre" >nul
)
if exist "dist\allure" (
    echo [INFO] Copying dist\allure to project root...
    xcopy /E /I /Y "dist\allure" "allure" >nul
)

echo [INFO] Building...
python -m PyInstaller PRStudy.spec --noconfirm

if exist "dist\PRStudy\PRStudy.exe" (
    echo [INFO] Cleaning up redundant dist\PRStudy.exe...
    if exist "dist\PRStudy.exe" del /q "dist\PRStudy.exe"

    echo [INFO] Bundling virtual environment...
    if exist ".venv" (
        xcopy /E /I /Y ".venv" "dist\PRStudy\venv" >nul
        echo [INFO] Virtual environment copied to dist\PRStudy\venv
    ) else (
        echo [WARN] .venv not found. Recipient will need system Python.
    )

    echo [INFO] Bundling testcases...
    if exist "testcases" (
        robocopy "testcases" "dist\PRStudy\testcases" /E >nul
        echo [INFO] Testcases copied to dist\PRStudy\testcases
    ) else (
        echo [WARN] testcases directory not found.
    )

    echo.
    echo ============================================================
    echo   Build complete!
    echo   Output: dist\PRStudy\PRStudy.exe
    echo ============================================================
) else (
    echo.
    echo [ERROR] Build failed.
)

pause
