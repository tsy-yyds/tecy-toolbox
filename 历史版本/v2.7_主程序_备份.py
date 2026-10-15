# -*- coding: utf-8 -*-
"""
多功能实用工具箱 - 主程序入口
功能：文件批量重命名、图片格式转换、二维码生成、单位换算、番茄钟、系统信息、
      音乐视频下载器、PDF工具箱、自动更新
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
import os
import logging
from pathlib import Path

# ===================== 自动更新配置 =====================
# 如需启用自动更新，请将 ENABLE_AUTO_UPDATE 设为 True 并填入你的直链
ENABLE_AUTO_UPDATE = False
REMOTE_VERSION_URL = "https://xxx.123pan.com/xxx/version.txt"
UPDATE_ZIP_URL = "https://xxx.123pan.com/xxx/update.zip"
PROJECT_ROOT = Path(__file__).parent
# =========================================================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# 添加tools目录到路径
tools_path = os.path.join(os.path.dirname(__file__), 'tools')
if tools_path not in sys.path:
    sys.path.append(tools_path)

# 导入工具模块
try:
    from file_renamer import FileRenamerFrame
    from image_converter import ImageConverterFrame
    from qrcode_tool import QRCodeFrame
    from unit_converter import UnitConverterFrame
    from pomodoro import PomodoroFrame
    from system_info import SystemInfoFrame
    from music_downloader import MusicDownloaderFrame
    from pdf_tool import PDFToolFrame
    from file_hash import FileHashFrame
except ImportError as e:
    logging.error(f"模块导入失败: {e}")
    messagebox.showerror("导入错误", f"工具模块缺失：{str(e)}\n请检查tools目录文件完整")
    sys.exit(1)

# 全局主题设置
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ToolBoxApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 读取本地版本号
        self.local_version = self.get_local_ver()
        self.title(f"🛠️ 多功能实用工具箱 {self.local_version}")
        self.geometry("1100x750")
        self.minsize(950, 680)
        self.resizable(True, True)
        self.center_window()

        self.current_tab = ""
        self.status_bar = None
        self.create_widgets()

    def get_local_ver(self):
        ver_file = PROJECT_ROOT / "version.txt"
        if ver_file.exists():
            with open(ver_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "v2.0"

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def on_tab_change(self):
        tab_name = self.tabview.get()
        self.current_tab = tab_name
        self.status_bar.configure(text=f"✨ 当前功能：{tab_name}")
        logging.info(f"切换标签页：{tab_name}")

    def toggle_theme(self):
        now = ctk.get_appearance_mode()
        new_mode = "dark" if now == "Light" else "light"
        ctk.set_appearance_mode(new_mode)
        # 更新按钮文字
        if hasattr(self, 'theme_btn'):
            if new_mode == "dark":
                self.theme_btn.configure(text="☀️ 浅色模式")
            else:
                self.theme_btn.configure(text="🌙 深色模式")

    def show_about(self):
        about_text = f"""多功能实用工具箱 {self.local_version}

包含功能：
  文件批量重命名
  图片格式转换 / 压缩
  二维码生成器
  单位换算器
  番茄钟专注计时器
  系统信息查看
  音乐 / 视频下载器
  PDF 全能工具箱
  文件哈希校验

提示：所有工具均已内置，开箱即用
"""
        messagebox.showinfo("关于工具箱", about_text)

    def create_widgets(self):
        # ========== 顶部标题栏 ==========
        top_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        top_frame.pack(fill="x", padx=25, pady=(15, 5))
        top_frame.pack_propagate(False)

        title = ctk.CTkLabel(
            top_frame,
            text="🛠️ 多功能实用工具箱",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(side="left")

        # 右侧按钮组
        btn_group = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_group.pack(side="right")

        about_btn = ctk.CTkButton(
            btn_group, text="ℹ️ 关于", width=80, height=32,
            fg_color="transparent", border_width=2, border_color="#4A90D9",
            text_color="#4A90D9", hover_color="#E8F4FD",
            command=self.show_about
        )
        about_btn.pack(side="right", padx=5)

        theme_btn = ctk.CTkButton(
            btn_group, text="🌙 深色模式", width=110, height=32,
            command=self.toggle_theme
        )
        self.theme_btn = theme_btn
        theme_btn.pack(side="right", padx=5)

        # 副标题
        sub_title = ctk.CTkLabel(
            self,
            text="一站式解决日常小需求 · 9大功能 · 简洁高效",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        sub_title.pack(pady=(0, 12))

        # 分割线
        separator = ctk.CTkFrame(self, height=2, fg_color="#E5E7EB")
        separator.pack(fill="x", padx=25)

        # ========== 标签页 ==========
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.pack(padx=25, pady=15, fill="both", expand=True)
        self.tabview.configure(command=self.on_tab_change)

        # 定义所有标签页
        tabs_config = [
            ("批量重命名", FileRenamerFrame),
            ("图片转换", ImageConverterFrame),
            ("二维码", QRCodeFrame),
            ("单位换算", UnitConverterFrame),
            ("番茄钟", PomodoroFrame),
            ("系统信息", SystemInfoFrame),
            ("下载器", MusicDownloaderFrame),
            ("PDF工具", PDFToolFrame),
            ("哈希校验", FileHashFrame),
        ]

        # 添加标签页并加载对应组件
        for tab_name, frame_class in tabs_config:
            self.tabview.add(tab_name)
            frame = frame_class(self.tabview.tab(tab_name))
            frame.pack(fill="both", expand=True, padx=12, pady=12)

        # ========== 底部状态栏 ==========
        self.current_tab = tabs_config[0][0]
        self.status_bar = ctk.CTkLabel(
            self,
            text=f"✨ 工具箱已就绪 | 当前功能：{self.current_tab}",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
            anchor="w",
            height=28
        )
        self.status_bar.pack(fill="x", padx=25, pady=(0, 12))


def main():
    logging.info("启动多功能实用工具箱")

    # 启动前检查更新（默认关闭，避免占位URL报错）
    if ENABLE_AUTO_UPDATE:
        try:
            from auto_updater import check_for_update
            check_for_update()
        except Exception as e:
            logging.warning(f"更新检测失败，跳过更新：{e}")

    # 启动GUI
    try:
        app = ToolBoxApp()
        app.mainloop()
    except Exception as e:
        logging.error(f"程序运行异常：{e}", exc_info=True)
        messagebox.showerror("程序崩溃", f"运行出错：{str(e)}")


if __name__ == "__main__":
    main()
