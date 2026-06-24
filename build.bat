@echo off
setlocal enabledelayedexpansion
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
if exist "resources\jre" (
    echo [INFO] resources\jre found
)
if exist "resources\allure" (
    echo [INFO] resources\allure found
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

    echo [INFO] Copying user guide...
    if exist "resources\README.md" (
        copy /Y "resources\README.md" "dist\PRStudy\README.md" >nul
        echo [INFO] User guide copied to dist\PRStudy\README.md
    )

    echo [INFO] Creating report directory...
    if not exist "dist\PRStudy\report" mkdir "dist\PRStudy\report"
    if not exist "dist\PRStudy\report\allure-results" mkdir "dist\PRStudy\report\allure-results"

    echo.
    echo ============================================================
    echo   Build complete!
    echo   Output: dist\PRStudy\PRStudy.exe
    echo ============================================================
    echo.

    :: Ask if user wants to create zip package
    set /p CREATE_ZIP="Do you want to create a ZIP package for distribution? (Y/N): "
    if /i "!CREATE_ZIP!"=="Y" (
        echo [INFO] Creating ZIP package...
        powershell -Command "Compress-Archive -Path 'dist\PRStudy' -DestinationPath 'dist\PRStudy-v1.0.zip' -Force"
        if exist "dist\PRStudy-v1.0.zip" (
            echo [INFO] ZIP package created: dist\PRStudy-v1.0.zip
            for %%A in ("dist\PRStudy-v1.0.zip") do echo [INFO] Package size: %%~zA bytes
        ) else (
            echo [ERROR] Failed to create ZIP package.
        )
    )
) else (
    echo.
    echo [ERROR] Build failed.
)

pause
