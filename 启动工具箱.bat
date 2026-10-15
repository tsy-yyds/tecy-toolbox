@echo off
title 多功能工具箱 v2.7
cd /d "%~dp0"

echo.
echo ==============================================================
echo              多功能实用工具箱 v2.7
echo ==============================================================
echo.
echo   正在启动，请稍候...
echo.

:: 检测并扩展 PATH，确保 ffmpeg 可用
set "FFMPEG_BIN=%~dp0ffmpeg\bin"

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%FFMPEG_BIN%\ffmpeg.exe" (
        set "PATH=%FFMPEG_BIN%;%PATH%"
    )
)

:: 三级 Python 优先级：venv > 嵌入式 > 系统
if exist "venv\Scripts\pythonw.exe" (
    call "venv\Scripts\pythonw.exe" "main.py"
) else if exist "python-embed\pythonw.exe" (
    call "python-embed\pythonw.exe" "main.py"
) else (
    call pythonw "main.py"
)

if %errorlevel% neq 0 (
    echo.
    echo 程序启动失败！
    echo.
    echo 如果是缺少依赖库，请先运行 "安装.bat"
    echo.
    pause
)
