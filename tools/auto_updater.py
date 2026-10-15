# -*- coding: utf-8 -*-
"""
自动更新模块
使用说明：将下方 ENABLE_AUTO_UPDATE 设为 True，并填入你的123云盘直链地址即可启用
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# ==================== 配置区 ====================
# 总开关：False=禁用更新（避免占位URL报错），True=启用更新
ENABLE_AUTO_UPDATE = False

# 远程版本文件地址（123云盘直链）
REMOTE_VERSION_URL = "https://xxx.123pan.com/xxx/version.txt"
# 更新包zip地址（123云盘直链）
UPDATE_ZIP_URL = "https://xxx.123pan.com/xxx/update.zip"
# ================================================

PROJECT_ROOT = Path(__file__).parent.parent


def get_local_version():
    """读取本地版本号"""
    ver_file = PROJECT_ROOT / "version.txt"
    if not ver_file.exists():
        return "v1.0.0"
    with open(ver_file, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_remote_version():
    """获取远程版本号"""
    if not ENABLE_AUTO_UPDATE or requests is None:
        return None
    try:
        resp = requests.get(REMOTE_VERSION_URL, timeout=8)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception:
        return None


def download_zip(save_path):
    """下载更新包"""
    if requests is None:
        return False
    try:
        resp = requests.get(UPDATE_ZIP_URL, stream=True, timeout=120)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def install_update(zip_path):
    """安装更新（解压覆盖）"""
    temp_dir = PROJECT_ROOT / "update_temp"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        # 找到解压后的根目录
        extracted_items = sorted(temp_dir.iterdir())
        if not extracted_items:
            return False
        extracted = extracted_items[0]

        # 如果解压出的是单个文件夹，进入其中
        if extracted.is_dir():
            source_dir = extracted
        else:
            source_dir = temp_dir

        # 覆盖文件，跳过虚拟环境、缓存目录
        skip_dirs = ("venv", "__pycache__", ".git", "update_temp")
        for item in source_dir.iterdir():
            dest = PROJECT_ROOT / item.name
            if item.name in skip_dirs:
                continue
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # 更新本地版本号
        new_ver = get_remote_version()
        if new_ver:
            with open(PROJECT_ROOT / "version.txt", "w", encoding="utf-8") as f:
                f.write(new_ver)
        return True
    except Exception:
        return False
    finally:
        # 清理临时文件
        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


def check_for_update():
    """检查并执行更新（静默失败，不影响主程序启动）"""
    if not ENABLE_AUTO_UPDATE:
        return False

    try:
        local = get_local_version()
        remote = get_remote_version()

        if not remote or local == remote:
            return False

        # 弹窗确认更新
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        tip = messagebox.askyesno(
            "发现新版本",
            f"本地版本：{local}\n线上版本：{remote}\n\n是否立即更新？"
        )
        root.destroy()

        if not tip:
            return False

        # 下载更新包
        zip_file = PROJECT_ROOT / "update.zip"
        if not download_zip(zip_file):
            messagebox.showerror("更新失败", "更新包下载失败，请检查网络！")
            return False

        # 安装更新
        if not install_update(zip_file):
            messagebox.showerror("更新失败", "文件覆盖出错，更新终止！")
            return False

        messagebox.showinfo("更新完成", "更新成功，程序即将重启！")

        # 重启程序
        try:
            os.execv(sys.executable, [sys.executable, str(PROJECT_ROOT / "main.py")])
        except Exception:
            pass
        return True

    except Exception:
        # 任何更新相关错误都静默跳过，不影响主程序
        return False
