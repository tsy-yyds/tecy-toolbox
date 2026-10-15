@echo off
setlocal enabledelayedexpansion
cls
title 多功能工具箱 - 一键安装程序

echo ========================================
echo     多功能工具箱 - 一键安装程序
echo ========================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
set "VENV_DIR=%ROOT_DIR%\venv"
set "EMBED_DIR=%ROOT_DIR%\python-embed"
set "MIRROR1=https://pypi.tuna.tsinghua.edu.cn/simple"
set "MIRROR2=https://mirrors.aliyun.com/pypi/simple"
set "PY_MIRROR1=https://mirrors.tuna.tsinghua.edu.cn/python"
set "PY_MIRROR2=https://mirrors.huaweicloud.com/python"
set "PY_VER_NUM=3.12.9"
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"

echo [1/7] 检测 Python 环境...

set "PYTHON_EXE="
set "PY_INSTALLED=0"
set "EMBED_MODE=0"

python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=python"
    set "PY_INSTALLED=1"
    echo [OK] 检测到系统 Python
)

if !PY_INSTALLED! equ 0 (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python3"
        set "PY_INSTALLED=1"
        echo [OK] 检测到系统 Python (python3)
    )
)

if !PY_INSTALLED! equ 0 (
    if exist "!EMBED_DIR!\python.exe" (
        echo [OK] 嵌入式 Python 已存在，跳过下载
        set "PYTHON_EXE=!EMBED_DIR!\python.exe"
        set "PY_INSTALLED=1"
        set "EMBED_MODE=1"
    )
)

if !PY_INSTALLED! equ 0 (
    set "EMBED_MODE=1"
    set "PYTHON_EXE=!EMBED_DIR!\python.exe"
    set "PY_ZIP_URL=!PY_MIRROR1!/!PY_VER_NUM!/python-!PY_VER_NUM!-embed-amd64.zip"
    set "PY_ZIP=!TEMP!\python-embed.zip"

    echo [信息] 未检测到系统 Python，启动嵌入式方案
    echo.
    echo 正在从清华镜像下载 Python !PY_VER_NUM! 嵌入式版本（约13MB）...

    powershell -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!PY_ZIP_URL!' -OutFile '!PY_ZIP!' -UseBasicParsing -TimeoutSec 180 } catch { Write-Error $_.Exception.Message; exit 1 }"

    if !errorlevel! neq 0 (
        echo [重试] 清华镜像失败，尝试华为镜像...
        set "PY_ZIP_URL=!PY_MIRROR2!/!PY_VER_NUM!/python-!PY_VER_NUM!-embed-amd64.zip"
        powershell -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!PY_ZIP_URL!' -OutFile '!PY_ZIP!' -UseBasicParsing -TimeoutSec 180 } catch { Write-Error $_.Exception.Message; exit 1 }"
    )

    if !errorlevel! neq 0 (
        echo [重试] 国内镜像均失败，尝试官方源...
        set "PY_ZIP_URL=https://www.python.org/ftp/python/!PY_VER_NUM!/python-!PY_VER_NUM!-embed-amd64.zip"
        powershell -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!PY_ZIP_URL!' -OutFile '!PY_ZIP!' -UseBasicParsing -TimeoutSec 300 } catch { Write-Error $_.Exception.Message; exit 1 }"
    )

    if exist "!PY_ZIP!" (
        echo 正在解压到 python-embed\ ...
        if not exist "!EMBED_DIR!" mkdir "!EMBED_DIR!"
        powershell -Command "Expand-Archive -Path '!PY_ZIP!' -DestinationPath '!EMBED_DIR!' -Force"
        del "!PY_ZIP!" 2>nul

        if exist "!PYTHON_EXE!" (
            echo [OK] 解压完成

            echo 正在配置 pip 支持...
            powershell -Command "[System.IO.File]::WriteAllLines('!EMBED_DIR!\\python312._pth', @('python312.zip','.','Lib\site-packages','import site'), [System.Text.Encoding]::ASCII)"

            echo 正在下载 pip 安装脚本...
            powershell -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!GET_PIP_URL!' -OutFile '!EMBED_DIR!\\get-pip.py' -UseBasicParsing -TimeoutSec 120 } catch { Write-Error $_.Exception.Message; exit 1 }"

            if exist "!EMBED_DIR!\get-pip.py" (
                echo 正在安装 pip...
                "!PYTHON_EXE!" "!EMBED_DIR!\get-pip.py" --no-warn-script-location 2>nul
                del "!EMBED_DIR!\get-pip.py" 2>nul

                "!PYTHON_EXE!" -m pip --version >nul 2>&1
                if !errorlevel! equ 0 (
                    set "PY_INSTALLED=1"
                    echo [OK] 嵌入式 Python + pip 部署完成
                )
            )
        )
    )

    if !PY_INSTALLED! equ 0 (
        echo [错误] 嵌入式 Python 部署失败
        echo.
        echo 请手动下载安装 Python 3.10+：
        echo   https://www.python.org/downloads/
        echo   https://npmmirror.com/mirrors/python/ （国内镜像）
        echo.
        echo 安装时务必勾选 "Add Python to PATH"
        pause
        exit /b 1
    )
)

for /f "delims=" %%i in ('"!PYTHON_EXE!" -c "import sys; print(sys.version.split()[0])"') do set "PY_VER=%%i"
echo [OK] Python !PY_VER! 已就绪
echo.

echo [2/7] pip 镜像源...
echo 后续 pip install 均使用清华镜像源（失败时回退阿里源/官方源）
echo.

echo [3/7] 创建虚拟环境...
set "SKIP_VENV=0"
if exist "!VENV_DIR!\Scripts\python.exe" (
    echo [跳过] 虚拟环境已存在
) else (
    echo 正在创建虚拟环境...
    if exist "!VENV_DIR!" (
        echo [信息] 清理旧的失败残留...
        rmdir /s /q "!VENV_DIR!" 2>nul
    )
    "!PYTHON_EXE!" -m venv "!VENV_DIR!" 2>nul
    if !errorlevel! neq 0 (
        echo [重试] venv 失败，尝试 virtualenv...
        "!PYTHON_EXE!" -m pip install virtualenv -i !MIRROR1! 2>nul
        if !errorlevel! neq 0 (
            "!PYTHON_EXE!" -m pip install virtualenv -i !MIRROR2! 2>nul
        )
        "!PYTHON_EXE!" -m virtualenv "!VENV_DIR!" 2>nul
        if !errorlevel! neq 0 (
            echo [警告] 虚拟环境创建失败，将直接安装到 Python 环境
            set "SKIP_VENV=1"
        )
    )
    if !SKIP_VENV! equ 0 echo [OK] 虚拟环境创建成功
)

if !SKIP_VENV! equ 1 (
    set "VENV_PYTHON=!PYTHON_EXE!"
) else (
    set "VENV_PYTHON=!VENV_DIR!\Scripts\python.exe"
)
echo.

echo [4/7] 升级 pip...
echo 正在升级 pip...
"!VENV_PYTHON!" -m pip install --upgrade pip -i !MIRROR1! 2>nul
if !errorlevel! neq 0 (
    "!VENV_PYTHON!" -m pip install --upgrade pip -i !MIRROR2! 2>nul
)
echo.

echo [5/7] 安装项目依赖...
echo 正在从 requirements.txt 安装依赖...

"!VENV_PYTHON!" -m pip install -r "!ROOT_DIR!\requirements.txt" -i !MIRROR1!
if !errorlevel! neq 0 (
    echo [重试] 清华源失败，切换到阿里源...
    "!VENV_PYTHON!" -m pip install -r "!ROOT_DIR!\requirements.txt" -i !MIRROR2!
    if !errorlevel! neq 0 (
        echo [重试] 阿里源失败，使用官方源...
        "!VENV_PYTHON!" -m pip install -r "!ROOT_DIR!\requirements.txt"
    )
)

"!VENV_PYTHON!" -m pip install yt-dlp -i !MIRROR1! >nul 2>&1
if !errorlevel! neq 0 (
    "!VENV_PYTHON!" -m pip install yt-dlp -i !MIRROR2! >nul 2>&1
)

echo [OK] 依赖安装完成
echo.

echo [6/7] 安装 ffmpeg（通过 pip 镜像源，约5秒）...
set "FFMPEG_OK=0"
set "FFMPEG_BIN=!ROOT_DIR!\ffmpeg\bin"

ffmpeg -version >nul 2>&1
if !errorlevel! equ 0 (
    set "FFMPEG_OK=1"
    echo [OK] ffmpeg 已可用（系统 PATH）
)

if !FFMPEG_OK! equ 0 (
    if exist "!FFMPEG_BIN!\ffmpeg.exe" (
        set "FFMPEG_OK=1"
        echo [OK] ffmpeg 已可用（项目目录）
    )
)

if !FFMPEG_OK! equ 0 (
    echo [信息] 通过 pip 镜像源下载 ffmpeg（imageio-ffmpeg，约30MB）...

    "!VENV_PYTHON!" -m pip install imageio-ffmpeg -i !MIRROR1!
    set "PIP_ERR=!errorlevel!"
    if !PIP_ERR! neq 0 (
        echo [重试] 清华源失败，切换到阿里源...
        "!VENV_PYTHON!" -m pip install imageio-ffmpeg -i !MIRROR2!
        set "PIP_ERR=!errorlevel!"
        if !PIP_ERR! neq 0 (
            echo [重试] 阿里源失败，使用官方源...
            "!VENV_PYTHON!" -m pip install imageio-ffmpeg
            set "PIP_ERR=!errorlevel!"
        )
    )

    if !PIP_ERR! equ 0 (
        "!VENV_PYTHON!" -c "import imageio_ffmpeg, shutil, os; src=imageio_ffmpeg.get_ffmpeg_exe(); dst=r'!FFMPEG_BIN!'; os.makedirs(dst, exist_ok=True); shutil.copy2(src, os.path.join(dst, 'ffmpeg.exe')); print('OK')"
        if exist "!FFMPEG_BIN!\ffmpeg.exe" (
            set "FFMPEG_OK=1"
            echo [OK] ffmpeg 安装完成（!FFMPEG_BIN!）
        )
        echo [信息] 清理 pip 安装包...
        "!VENV_PYTHON!" -m pip uninstall imageio-ffmpeg -y >nul 2>&1
    )

    if !FFMPEG_OK! equ 0 (
        echo [警告] ffmpeg 自动安装失败
        echo        视频下载功能仍可使用，但画质可能不是最优
    )
)
echo.

echo [7/7] 校验关键模块...
echo 正在校验模块导入...

"!VENV_PYTHON!" -c "import customtkinter; print('  customtkinter OK')" 2>nul
if !errorlevel! neq 0 echo   customtkinter 失败

"!VENV_PYTHON!" -c "import PIL; print('  Pillow OK')" 2>nul
if !errorlevel! neq 0 echo   Pillow 失败

"!VENV_PYTHON!" -c "import qrcode; print('  qrcode OK')" 2>nul
if !errorlevel! neq 0 echo   qrcode 失败

"!VENV_PYTHON!" -c "import psutil; print('  psutil OK')" 2>nul
if !errorlevel! neq 0 echo   psutil 失败

"!VENV_PYTHON!" -c "import fitz; print('  PyMuPDF OK')" 2>nul
if !errorlevel! neq 0 echo   PyMuPDF 失败

"!VENV_PYTHON!" -c "import docx; print('  python-docx OK')" 2>nul
if !errorlevel! neq 0 echo   python-docx 失败

"!VENV_PYTHON!" -c "import yt_dlp; print('  yt-dlp OK')" 2>nul
if !errorlevel! neq 0 echo   yt-dlp 失败

"!VENV_PYTHON!" -c "import PyPDF2; print('  PyPDF2 OK')" 2>nul
if !errorlevel! neq 0 echo   PyPDF2 失败

"!VENV_PYTHON!" -c "import requests; print('  requests OK')" 2>nul
if !errorlevel! neq 0 echo   requests 失败

"!VENV_PYTHON!" -c "import urllib3; print('  urllib3 OK')" 2>nul
if !errorlevel! neq 0 echo   urllib3 失败

echo.

echo ========================================
echo        安装全部完成
echo ========================================
echo.
if !EMBED_MODE! equ 1 (
    echo   Python:    !PY_VER! （嵌入式）
) else (
    echo   Python:    !PY_VER! （系统）
)
if !FFMPEG_OK! equ 1 (
    echo   ffmpeg:    已就绪
) else (
    echo   ffmpeg:    未安装（建议手动安装以提升画质）
)
if !SKIP_VENV! equ 1 (
    echo   Python 环境: 直接使用（无虚拟环境）
) else (
    echo   虚拟环境: !VENV_DIR!
)
echo.
echo   启动方式：直接双击 "启动工具箱.bat"
echo.
echo ========================================

"!VENV_PYTHON!" -m pip cache purge >nul 2>&1

endlocal
pause
