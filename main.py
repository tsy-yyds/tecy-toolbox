# -*- coding: utf-8 -*-
"""
多功能实用工具箱 - tecy_tsy 整合版主程序

品牌：tecy_tsy
UI：仿火绒安全软件风格（深蓝主色 · 左侧导航 + 右侧内容区 · 卡片式布局）
版本：v3.0

功能组成：
  [日常工具] 批量重命名 / 图片转换 / 二维码 / 单位换算 / 番茄钟
  [内容工具] 音乐视频下载器 / PDF工具 / 哈希校验
  [系统工具] 系统信息 / 腾讯进程管家（整合自 TxConfig v12.0 核心逻辑）
  [附加应用] 游戏空间 v3.0 / 进程锁定 v1.5 / 密码本生成器 / 密码本启动器 / 磁盘管理
              （以上 PyQt5/tkinter 独立程序以子进程方式一键启动，随包集成）

启动方式：直接双击 exe，无需运行 .bat。
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
import os
import logging
import subprocess
import threading
from pathlib import Path

# ===================== 版本与品牌 =====================
APP_BRAND = "tecy_tsy"
APP_NAME = "多功能实用工具箱"
APP_VERSION = "v3.0"

# ===================== 自动更新配置（默认关闭） =====================
ENABLE_AUTO_UPDATE = False
REMOTE_VERSION_URL = "https://xxx.123pan.com/xxx/version.txt"
UPDATE_ZIP_URL = "https://xxx.123pan.com/xxx/update.zip"

# 自动更新代码仅在启用时导入，避免打包冗余
AUTO_UPDATER = None


def app_base_dir():
    """应用根目录：打包后为 exe 所在目录，开发时为项目目录"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


PROJECT_ROOT = app_base_dir()


def resource_path(rel):
    """资源路径：优先 exe 旁目录，其次 PyInstaller 解包目录"""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    else:
        base = PROJECT_ROOT
    p = PROJECT_ROOT / rel
    if p.exists():
        return p
    return base / rel


# ===================== 日志配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 添加 tools 目录到路径
tools_path = resource_path("tools")
if str(tools_path) not in sys.path:
    sys.path.append(str(tools_path))

# ===================== 导入工具模块 =====================
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
    from tencent_process_manager import TencentProcessManagerFrame
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    try:
        messagebox.showerror("导入错误", f"工具模块缺失：{str(e)}\n请检查 tools 目录文件完整")
    except Exception:
        pass
    sys.exit(1)

# ===================== 主题与配色（火绒风格） =====================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# 火绒风格深蓝配色
DARK_BLUE = "#123457"      # 侧边栏底色
DARK_BLUE2 = "#0E2A47"     # 侧边栏加深
HOVER_BLUE = "#1B4E80"     # 导航悬停
ACCENT_BLUE = "#2E86DE"    # 高亮/选中
ACCENT_LIGHT = "#5DADE2"   # 亮点
TEXT_WHITE = "#ECF2F8"
TEXT_GRAY = "#8FA6BF"


class SplashScreen(ctk.CTkToplevel):
    """启动品牌界面：tecy_tsy 品牌标识"""

    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=DARK_BLUE)
        w, h = 460, 240
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        # center splash body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(expand=True)

        brand = ctk.CTkLabel(
            body, text="tecy_tsy",
            font=ctk.CTkFont(family="Arial", size=40, weight="bold"),
            text_color=TEXT_WHITE
        )
        brand.pack(pady=(10, 4))

        title = ctk.CTkLabel(
            body, text=f"{APP_NAME} {APP_VERSION}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT_LIGHT
        )
        title.pack(pady=(0, 10))

        sub = ctk.CTkLabel(
            body, text="tecy_tsy 出品 · 深蓝整合版",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_GRAY
        )
        sub.pack()

        loading = ctk.CTkLabel(
            self, text="正在加载工具模块...",
            font=ctk.CTkFont(size=12), text_color=TEXT_GRAY
        )
        loading.pack(side="bottom", pady=(0, 18))


class IntegratedToolPage(ctk.CTkFrame):
    """附加应用（独立 exe 子进程）启动页面"""

    def __init__(self, master, title, desc, exe_rel, hint="", **kwargs):
        super().__init__(master, **kwargs)
        self.exe_rel = exe_rel
        self.desc = desc

        # 卡片
        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="both", expand=False, padx=40, pady=40)

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#123457"
        ).pack(pady=(30, 8))

        ctk.CTkLabel(
            card, text=desc,
            font=ctk.CTkFont(size=14), text_color="#555555",
            wraplength=560, justify="center"
        ).pack(pady=(0, 6))

        if hint:
            ctk.CTkLabel(
                card, text=hint,
                font=ctk.CTkFont(size=12), text_color="#888888"
            ).pack(pady=(4, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(16, 24))

        ctk.CTkButton(
            btn_row, text="启动", width=160, height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT_BLUE, hover_color="#1F6FBF",
            command=self._launch
        ).pack(side="left", padx=10)

        self.status = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12), text_color=ACCENT_BLUE
        )
        self.status.pack(pady=(0, 20))

        ctk.CTkLabel(
            card, text=f"所在路径：{resource_path(self.exe_rel)}",
            font=ctk.CTkFont(size=11), text_color="#999999"
        ).pack(pady=(0, 18))

    def _resolved(self):
        # 优先 exe 旁目录（打包后用户可见），其次解包目录
        p = PROJECT_ROOT / self.exe_rel
        if p.exists():
            return p
        return resource_path(self.exe_rel)

    def _launch(self):
        exe = self._resolved()
        if not exe.exists():
            self.status.configure(text="未找到程序文件！")
            messagebox.showwarning("启动失败", f"未找到程序：\n{exe}\n\n请确认打包目录完整。")
            return
        try:
            subprocess.Popen([str(exe)], cwd=str(exe.parent))
            self.status.configure(text="已启动，独立窗口运行中...")
            logger.info(f"启动子程序: {exe}")
        except Exception as e:
            self.status.configure(text="")
            messagebox.showerror("启动失败", f"启动失败：{e}")


class TencentPage(ctk.CTkFrame):
    """腾讯进程管家容器页（同进程 CustomTkinter 整合）"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.manager = TencentProcessManagerFrame(self, **kwargs)
        self.manager.pack(fill="both", expand=True)

    def on_close(self):
        try:
            self.manager.on_close()
        except Exception:
            pass


class ToolBoxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.local_version = APP_VERSION
        self.title(f"{APP_BRAND} · {APP_NAME} {APP_VERSION}  |  整合升级版")
        self.geometry("1180x780")
        self.minsize(1024, 700)

        icon_path = resource_path("assets/icon.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._pages = {}          # 页面缓存
        self._nav_buttons = {}    # 导航按钮缓存
        self.current_key = ""
        self.status_bar = None

        self._build_layout()
        self._center_window()
        self.after(200, lambda: self._select("批量重命名"))

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")

    # ---------------- 布局 ----------------
    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== 左侧导航栏 =====
        nav = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=DARK_BLUE)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_propagate(False)

        # 品牌区
        brand_frame = ctk.CTkFrame(nav, fg_color=DARK_BLUE2, corner_radius=0)
        brand_frame.pack(fill="x")

        ctk.CTkLabel(
            brand_frame, text="tecy_tsy",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_WHITE
        ).pack(pady=(18, 2))

        ctk.CTkLabel(
            brand_frame, text=APP_NAME,
            font=ctk.CTkFont(size=13), text_color=ACCENT_LIGHT
        ).pack(pady=(0, 14))

        # 导航分组
        nav_groups = [
            (" 日常工具", {
                "批量重命名": self._page_tool,
                "图片转换": self._page_tool,
                "二维码": self._page_tool,
                "单位换算": self._page_tool,
                "番茄钟": self._page_tool,
            }),
            (" 内容工具", {
                "下载器": self._page_tool,
                "PDF工具": self._page_tool,
                "哈希校验": self._page_tool,
            }),
            (" 系统工具", {
                "系统信息": self._page_tool,
                "腾讯进程管家": self._page_task,
            }),
            (" 附加应用", {
                "游戏空间": self._page_game,
                "进程锁定": self._page_locker,
                "密码本工具": self._page_password,
                "磁盘管理": self._page_disk,
            }),
        ]

        for group_title, items in nav_groups:
            ctk.CTkLabel(
                nav, text=group_title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_GRAY
            ).pack(anchor="w", padx=18, pady=(14, 4))

            for key in items:
                btn = ctk.CTkButton(
                    nav, text=key, anchor="w", height=34,
                    fg_color="transparent", text_color=TEXT_WHITE,
                    hover_color=HOVER_BLUE,
                    font=ctk.CTkFont(size=14),
                    command=lambda k=key: self._select(k)
                )
                btn.pack(fill="x", padx=10, pady=2)
                self._nav_buttons[key] = btn

        # 底部：主题/关于
        bottom = ctk.CTkFrame(nav, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=14)

        theme_btn = ctk.CTkButton(
            bottom, text="🌙 深色模式", height=30,
            fg_color="transparent", text_color=TEXT_WHITE, hover_color=HOVER_BLUE,
            command=self._toggle_theme
        )
        self.theme_btn = theme_btn
        theme_btn.pack(fill="x", padx=12, pady=2)

        about_btn = ctk.CTkButton(
            bottom, text="ℹ️ 关于", height=30,
            fg_color="transparent", text_color=TEXT_WHITE, hover_color=HOVER_BLUE,
            command=self._show_about
        )
        about_btn.pack(fill="x", padx=12, pady=2)

        # ===== 右侧主区域 =====
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        # 顶部标题栏
        top = ctk.CTkFrame(right, fg_color="transparent", height=64)
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 4))

        top_title = ctk.CTkLabel(
            top, text="tecy_tsy 多功能实用工具箱",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#123457"
        )
        top_title.pack(side="left")

        ver = ctk.CTkLabel(
            top, text=APP_VERSION,
            font=ctk.CTkFont(size=13),
            text_color="#97A8BC",
            fg_color="#E8EEF6",
            corner_radius=10,
            width=60, height=26
        )
        ver.pack(side="left", padx=(12, 0), pady=(6, 0))

        # 内容区容器
        self.content = ctk.CTkFrame(right, corner_radius=14, fg_color=("#F5F7FA", "#1A1A1A"))
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(6, 10))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # 状态栏
        self.status_bar = ctk.CTkLabel(
            right, text="tecy_tsy 工具箱已就绪",
            font=ctk.CTkFont(size=12), text_color="#888888", anchor="w"
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))

    # ---------------- 页面构建 ----------------
    def _select(self, key):
        self.current_key = key
        # 样式：清除选中态
        for k, b in self._nav_buttons.items():
            if k == key:
                b.configure(fg_color=ACCENT_BLUE)
            else:
                b.configure(fg_color="transparent")

        # 销毁旧页面并清空缓存，避免复用已被销毁的 widget 导致 TclError
        for w in self.content.winfo_children():
            w.destroy()
        self._pages.clear()
        page = self._build_page(key)
        self._pages[key] = page
        page.configure(fg_color="transparent")
        page.pack(fill="both", expand=True)

        self.status_bar.configure(text=f"当前功能：{key}")

    def _build_page(self, key):
        container = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=14)
        if key == "腾讯进程管家":
            tp = TencentPage(container)
            tp.pack(fill="both", expand=True)
        elif key in ("游戏空间", "进程锁定", "密码本工具", "磁盘管理"):
            img_builders = {
                "游戏空间": self._page_game,
                "进程锁定": self._page_locker,
                "密码本工具": self._page_password,
                "磁盘管理": self._page_disk,
            }
            img_builders[key](container).pack(fill="both", expand=True)
        else:
            frame = self._new_tool_frame(key, container)
            frame.pack(fill="both", expand=True)
        return container

    def _new_tool_frame(self, key, master):
        cls_map = {
            "批量重命名": FileRenamerFrame,
            "图片转换": ImageConverterFrame,
            "二维码": QRCodeFrame,
            "单位换算": UnitConverterFrame,
            "番茄钟": PomodoroFrame,
            "下载器": MusicDownloaderFrame,
            "PDF工具": PDFToolFrame,
            "哈希校验": FileHashFrame,
            "系统信息": SystemInfoFrame,
        }
        return cls_map[key](master)

    # ---------------- 附加应用页面 ----------------
    def _page_game(self, master):
        return IntegratedToolPage(
            master,
            title="游戏空间 v3.0",
            desc="独立游戏启动器（PyQt5 稳定版，具备密码锁定、游戏管理等功能）。\n运行于独立进程，不影响主程序。",
            exe_rel="integrated/游戏空间/游戏空间v3.0.exe",
            hint="来源：D:\\Desktop\\game\\历史版本\\游戏空间v3.0（v3.0 稳定版）"
        )

    def _page_locker(self, master):
        return IntegratedToolPage(
            master,
            title="进程锁定 v1.5",
            desc="进程锁定与监控工具（tkinter 稳定版）：锁定进程、防止关闭、自动监控。\n运行于独立进程。",
            exe_rel="integrated/进程锁定/进程锁定.exe",
            hint="来源：D:\\Desktop\\进程锁定\\v1.5（v1.5 稳定版）"
        )

    def _page_password(self, master):
        return IntegratedToolPage(
            master,
            title="密码本工具",
            desc="密码本生成器 与 密码本启动器（PyQt5）：\n生成全数字密码本，并自动向目标窗口输入密码。\n运行于独立进程。",
            exe_rel="integrated/应用包密码工具/密码本生成器.exe",
            hint="来源：D:\\Desktop\\应用包\\python（稳定版 exe）"
        )

    def _page_disk(self, master):
        return IntegratedToolPage(
            master,
            title="应用包 - 磁盘管理",
            desc="磁盘空间分析与分类统计工具（PyQt5 + matplotlib，含启动画面）。\n运行于独立进程。",
            exe_rel="integrated/应用包密码工具/应用包-磁盘管理.exe",
            hint="来源：D:\\Desktop\\应用包\\python（稳定版 exe，已排除标注失败品的脚本）"
        )

    # ---------------- 工具类按钮 ----------------
    def _page_tool(self, master):
        pass  # 实际由 _build_page 处理，此标记仅用于映射

    def _page_task(self, master):
        pass

    # ---------------- 其它 ----------------
    def _toggle_theme(self):
        now = ctk.get_appearance_mode()
        new_mode = "dark" if now == "Light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.theme_btn.configure(text="☀️ 浅色模式" if new_mode == "dark" else "🌙 深色模式")
        self.content.configure(fg_color=("#F5F7FA", "#1A1A1A") if new_mode == "light" else ("#F5F7FA", "#1A1A1A"))

    def _show_about(self):
        about = (
            f"{APP_BRAND} · {APP_NAME} {APP_VERSION}\n"
            "仿火绒安全软件风格整合版\n\n"
            "日常工具：批量重命名 / 图片转换 / 二维码 / 单位换算 / 番茄钟\n"
            "内容工具：音乐视频下载器（已修复抖音 cookie 问题）/ PDF工具 / 哈希校验\n"
            "系统工具：系统信息 / 腾讯进程管家（整合 TxConfig v12.0）\n"
            "附加应用：游戏空间 v3.0 / 进程锁定 v1.5 / 密码本工具 / 磁盘管理\n\n"
            f"品牌：tecy_tsy  |  免 bat，双击即用"
        )
        messagebox.showinfo("关于工具箱", about)

    def on_close(self):
        # 停止腾讯进程管家后台保护线程
        for key in list(self._pages):
            page = self._pages[key]
            if isinstance(page, TencentPage):
                page.on_close()
        self.destroy()


def main():
    logger.info(f"启动 {APP_NAME}（{APP_BRAND}） v{APP_VERSION}")

    # 主窗口与品牌启动界面必须同在主线程，避免 Tk 线程模型异常
    app = ToolBoxApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)

    # 启动品牌界面（CTkToplevel，依附主窗口，短暂展示后自动销毁）
    splash = None
    try:
        splash = SplashScreen()
    except Exception as e:
        logger.warning(f"启动界面显示失败：{e}")
        splash = None

    if splash is not None:
        app.after(1800, lambda: splash.destroy())

    app.mainloop()


if __name__ == "__main__":
    main()
