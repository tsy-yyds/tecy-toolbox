# -*- coding: utf-8 -*-
"""
音乐 & 短视频下载器模块
音乐：搜索歌曲名下载（网易云音乐，Meting API）
视频：yt-dlp 通用引擎，支持抖音/B站/快手等 1000+ 平台
"""
import customtkinter as ctk
from tkinter import messagebox
import requests
import os
import sys
import subprocess
import threading
import time
import urllib3
from datetime import datetime
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MusicDownloaderFrame(ctk.CTkFrame):
    """音乐视频下载器 - CustomTkinter Frame版本"""

    # 请求频率限制（秒）
    REQUEST_INTERVAL = 5

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # 保存目录：打包后为 exe 所在目录，开发时为项目根目录
        if getattr(sys, "frozen", False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(__file__).parent.parent
        self.music_folder = self.base_dir / "音乐下载"
        self.video_folder = self.base_dir / "无水印视频下载"

        # 自动创建文件夹
        for folder in [self.music_folder, self.video_folder]:
            folder.mkdir(exist_ok=True)

        # 上次请求时间戳（用于频率控制）
        self._last_request_time = 0

        # 下载状态
        self._downloading = False
        self._last_video_save_dir = None

        self.create_widgets()

    def _rate_limit(self):
        """请求频率限制：距离上次请求不足5秒则等待"""
        now = time.time()
        wait_time = self.REQUEST_INTERVAL - (now - self._last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)
        self._last_request_time = time.time()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(
            self,
            text="音乐 & 短视频 下载器",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(5, 15))

        # 标签页
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_music = self.tabview.add("音乐下载")
        self.tab_video = self.tabview.add("视频下载")

        self._build_music_tab()
        self._build_video_tab()

        # 日志区域
        log_frame = ctk.CTkFrame(self, corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        log_label = ctk.CTkLabel(
            log_frame, text="运行日志",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        log_label.pack(anchor="w", padx=12, pady=(8, 4))

        self.log_box = ctk.CTkTextbox(
            log_frame,
            height=180,
            font=("Consolas", 11)
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.log("下载器已就绪")
        self.log("音乐：输入歌曲名搜索下载 | 视频：粘贴链接解析下载")
        self.log("视频引擎：yt-dlp（支持抖音/B站/快手/YouTube等1000+平台）")

    def _build_music_tab(self):
        frame = ctk.CTkFrame(self.tab_music, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 说明
        tip = ctk.CTkLabel(
            frame,
            text="输入歌曲名（可加歌手），搜索下载网易云音乐",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        )
        tip.pack(anchor="w", pady=(5, 10))

        # 输入框
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(input_frame, text="歌曲名：", width=70).pack(side="left")
        self.music_keyword = ctk.CTkEntry(input_frame, placeholder_text="例如：晴天 周杰伦")
        self.music_keyword.pack(side="left", fill="x", expand=True, padx=(5, 10))

        self.music_btn = ctk.CTkButton(
            input_frame, text="搜索并下载", width=120,
            command=lambda: self._run_thread("music")
        )
        self.music_btn.pack(side="left")

        # 进度条
        self.music_progress = ctk.CTkProgressBar(frame, mode="indeterminate")
        self.music_progress.pack(fill="x", pady=10)
        self.music_progress.set(0)

        # 保存路径提示
        path_tip = ctk.CTkLabel(
            frame,
            text=f"保存位置：{self.music_folder}",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        path_tip.pack(anchor="w", pady=10)

    def _build_video_tab(self):
        frame = ctk.CTkFrame(self.tab_video, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 说明
        tip = ctk.CTkLabel(
            frame,
            text="支持抖音、B站、快手、YouTube等1000+平台，粘贴链接即可下载",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        )
        tip.pack(anchor="w", pady=(5, 10))

        # 输入框
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(input_frame, text="视频链接：", width=70).pack(side="left")
        self.video_link = ctk.CTkEntry(input_frame, placeholder_text="粘贴抖音/B站/快手等视频分享链接...")
        self.video_link.pack(side="left", fill="x", expand=True, padx=(5, 10))

        self.video_btn = ctk.CTkButton(
            input_frame, text="解析并下载", width=120,
            command=lambda: self._run_thread("video")
        )
        self.video_btn.pack(side="left")

        # 进度条（确定模式，显示百分比）
        self.video_progress = ctk.CTkProgressBar(frame)
        self.video_progress.pack(fill="x", pady=10)
        self.video_progress.set(0)

        # 进度文字
        self.video_progress_label = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#888888"
        )
        self.video_progress_label.pack()

        # 打开文件夹按钮（下载完成后显示）
        self.open_folder_btn = ctk.CTkButton(
            frame, text="打开下载文件夹", width=150,
            fg_color="#4A90D9", hover_color="#357ABD",
            command=self._open_video_folder,
            state="disabled"
        )
        self.open_folder_btn.pack(pady=5)

        # 保存路径提示
        path_tip = ctk.CTkLabel(
            frame,
            text=f"保存位置：{self.video_folder}",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        path_tip.pack(anchor="w", pady=10)

    def _open_video_folder(self):
        """在资源管理器中打开视频下载文件夹"""
        if self._last_video_save_dir:
            os.startfile(str(self._last_video_save_dir))
        else:
            os.startfile(str(self.video_folder))

    def log(self, msg):
        """输出日志"""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(ctk.END, f"[{time_str}] {msg}\n")
        self.log_box.see(ctk.END)

    def _sanitize_filename(self, name):
        """清理文件名中的非法字符"""
        if not name:
            name = "未命名"
        for ch in ['/', '\\', '|', '?', '*', ':', '"', '<', '>']:
            name = name.replace(ch, "_")
        return name.strip()[:80]

    def _run_thread(self, mode):
        """多线程执行下载，避免卡UI"""
        if mode == "music":
            keyword = self.music_keyword.get().strip()
            if not keyword:
                messagebox.showwarning("提示", "请输入歌曲名！")
                return
            if self._downloading:
                messagebox.showwarning("提示", "正在下载中，请稍候...")
                return
            self._downloading = True
            self.music_btn.configure(state="disabled")
            self.music_progress.start()
            threading.Thread(target=self._download_music, args=(keyword,), daemon=True).start()
        else:
            url = self.video_link.get().strip()
            if not url:
                messagebox.showwarning("提示", "请输入视频链接！")
                return
            if self._downloading:
                messagebox.showwarning("提示", "正在下载中，请稍候...")
                return
            self._downloading = True
            self.video_btn.configure(state="disabled")
            self.video_progress.set(0)
            self.video_progress_label.configure(text="准备下载...")
            self.open_folder_btn.configure(state="disabled")
            threading.Thread(target=self._download_video, args=(url,), daemon=True).start()

    # ==================== 音乐下载 ====================
    def _download_music(self, keyword):
        """搜索并下载音乐（Meting API - 网易云音乐）"""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            self.log(f"正在搜索：{keyword}")
            self._rate_limit()

            # Meting API 搜索
            api_url = "https://api.i-meto.com/meting/api"
            res = requests.get(
                api_url,
                params={
                    "server": "netease",
                    "type": "search",
                    "id": keyword,
                    "limit": 5
                },
                headers=headers, timeout=15
            )
            data = res.json()

            if not data or len(data) == 0:
                self.log("未找到相关歌曲")
                return

            # 取第一首
            song = data[0]
            title = song.get("title", "未知歌曲")
            author = song.get("author", "未知歌手")
            audio_url = song.get("url", "")

            if not audio_url:
                self.log("无法获取播放地址")
                return

            full_title = f"{title} - {author}"
            full_title = self._sanitize_filename(full_title)
            self.log(f"找到歌曲：{full_title}")
            self.log("开始下载音频...")

            audio_res = requests.get(
                audio_url, headers=headers,
                stream=True, timeout=60
            )

            save_path = self.music_folder / f"{full_title}.mp3"
            total_size = int(audio_res.headers.get('content-length', 0))
            downloaded = 0

            with open(save_path, "wb") as f:
                for chunk in audio_res.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = min(100, int(downloaded / total_size * 100))
                            self.log(f"  下载进度：{pct}%")

            self.log(f"下载完成：{full_title}.mp3")
            self.after(0, lambda: messagebox.showinfo("成功", f"音乐下载完成！\n{full_title}.mp3"))

        except Exception as e:
            self.log(f"音乐下载失败：{str(e)}")
            self.after(0, lambda: messagebox.showerror("失败", f"下载出错：{str(e)}"))
        finally:
            self._downloading = False
            self.after(0, lambda: (
                self.music_progress.stop(),
                self.music_btn.configure(state="normal")
            ))

    # ==================== 视频下载（yt-dlp 通用引擎） ====================
    def _find_ffmpeg(self):
        """定位 ffmpeg：优先项目内 ffmpeg/bin，其次系统 PATH。返回(path 绝对 exe 或空)"""
        local = self.base_dir / "ffmpeg" / "bin" / "ffmpeg.exe"
        if local.exists():
            return str(local)
        try:
            import shutil
            p = shutil.which("ffmpeg")
            if p:
                return p
        except Exception:
            pass
        return ""

    def _detect_cookies(self):
        """自动探测 cookies 来源（修复抖音 Fresh cookies needed）：
        1) 项目目录下存在 cookies.txt -> 直接使用
        2) 否则尝试本机浏览器 cookies（Edge -> Chrome，任一可用即用）
        返回 yt_dlp 可用的 cookies 相关 opts 字典
        """
        # 1) cookies.txt 兜底
        cookie_txt = self.base_dir / "cookies.txt"
        if cookie_txt.exists():
            self.log("检测到项目目录 cookies.txt，正在使用...")
            return {"cookiefile": str(cookie_txt)}

        # 2) 浏览器 cookies（yt-dlp 内置 cookiesfrombrowser，无需额外依赖）
        try:
            import yt_dlp
        except Exception:
            return {}

        for browser in ("edge", "chrome"):
            try:
                # yt-dlp 新版使用 extract_cookies_from_browser（旧版为 load_cookies_from_browser）
                extractor = (getattr(yt_dlp.cookies, "extract_cookies_from_browser", None)
                             or getattr(yt_dlp.cookies, "load_cookies_from_browser", None))
                if extractor is None:
                    continue
                extractor(browser, None)
                self.log(f"已自动加载 {browser} 浏览器 cookies 用于下载鉴权")
                return {"cookiesfrombrowser": (browser, None)}
            except Exception:
                continue
        return {}

    def _progress_hook(self, d):
        """yt-dlp 下载进度回调"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                pct = d['downloaded_bytes'] / d['total_bytes']
                self.after(0, lambda: self.video_progress.set(pct))
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                total_mb = d['total_bytes'] / (1024 * 1024)
                speed = d.get('speed', 0) or 0
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "计算中..."
                self.after(0, lambda: self.video_progress_label.configure(
                    text=f"{downloaded_mb:.1f}MB / {total_mb:.1f}MB  |  {speed_str}"
                ))
            elif 'downloaded_bytes' in d:
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                speed = d.get('speed', 0) or 0
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "计算中..."
                self.after(0, lambda: self.video_progress_label.configure(
                    text=f"已下载 {downloaded_mb:.1f}MB  |  {speed_str}"
                ))
        elif d['status'] == 'finished':
            self.after(0, lambda: (
                self.video_progress.set(1.0),
                self.video_progress_label.configure(text="处理中，正在封装...")
            ))

    def _download_video(self, url):
        """使用 yt-dlp 通用引擎下载视频"""
        self.log("正在解析视频链接...")

        try:
            import yt_dlp

            # 检测 ffmpeg（优先项目内置 ffmpeg，其次系统 PATH）
            ffmpeg_path = self._find_ffmpeg()
            ffmpeg_available = False
            if ffmpeg_path:
                try:
                    subprocess.run(
                        [ffmpeg_path, "-version"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=True
                    )
                    ffmpeg_available = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    ffmpeg_available = False
            if not ffmpeg_available:
                self.log("检测 ffmpeg：未找到内置/系统 ffmpeg")

            # 格式选择策略（不硬编码文件扩展名，让 yt-dlp 自动适配各平台）
            # bestvideo+bestaudio/best：有 ffmpeg 时合并最佳音视频，无 ffmpeg 时回退到单文件
            # 统一使用同一选择器，yt-dlp 自动处理平台差异（如 B站 必须音视频分开）
            format_str = 'bestvideo+bestaudio/best'

            ydl_opts = {
                'outtmpl': str(self.video_folder / '%(title).100s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'format': format_str,
                'progress_hooks': [self._progress_hook],
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
            }

            # 自动附加 cookies（修复抖音 "Fresh cookies needed"）
            cookie_opts = self._detect_cookies()
            if cookie_opts:
                ydl_opts.update(cookie_opts)

            # 使用项目内置 ffmpeg（若存在）
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path

            if ffmpeg_available:
                ydl_opts['merge_output_format'] = 'mp4'

            self.log("正在解析视频信息...")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info:
                    title = info.get('title', '视频')
                    self._last_video_save_dir = self.video_folder

                    self.log(f"标题：{title}")
                    self.log(f"下载完成！保存至：{self.video_folder}")
                    self.after(0, lambda: (
                        self.open_folder_btn.configure(state="normal"),
                        messagebox.showinfo(
                            "下载完成",
                            f"视频下载成功！\n标题：{title}\n保存位置：{self.video_folder}"
                        )
                    ))
                else:
                    self.log("无法获取视频信息")
                    self.after(0, lambda: messagebox.showerror("失败", "无法解析该视频链接，请检查链接是否有效。"))

        except ImportError:
            self.log("yt-dlp 未安装，请运行: pip install yt-dlp")
            self.after(0, lambda: messagebox.showerror("错误", "yt-dlp 未安装，请先安装依赖。"))
        except yt_dlp.utils.DownloadError as e:
            err_msg = str(e)[:200]
            self.log(f"下载失败：{err_msg}")

            # 抖音等平台 cookies 相关问题：给出明确处理指引
            if 'cookie' in err_msg.lower():
                cookie_txt = self.base_dir / "cookies.txt"
                if cookie_txt.exists():
                    hint = (f"已使用项目目录 cookies.txt（{cookie_txt.name}），但仍报 cookies 错误。\n"
                            "请重新导出最新 cookies（需包含 douyin.com 的登录态）：\n"
                            "  浏览器登录抖音 -> F12 -> Application/应用 -> Cookies -> 导出 Netscape 格式 cookies.txt\n"
                            "覆盖到项目根目录后重试。")
                else:
                    hint = ("该平台（如抖音）强制要求浏览器登录 cookies。\n"
                            "本程序已自动尝试读取 Edge/Chrome 浏览器 cookies。\n"
                            "若仍失败，请执行：\n"
                            "  1) 用本机浏览器（Edge 或 Chrome）登录抖音账号后刷新视频页；\n"
                            "  2) 或导出 Netscape 格式 cookies 到 cookies.txt 放入项目根目录。")
                self.log("抖音等平台需要登录态 cookies，已提示处理方式")
                self.after(0, lambda: messagebox.showwarning("需要 cookies", hint))
                return

            # 格式不支持时尝试降级到单一文件
            if 'format' in err_msg.lower() or 'requested format' in err_msg.lower():
                self.log("尝试降级模式：best 单文件...")
                try:
                    ydl_opts2 = {
                        'outtmpl': str(self.video_folder / '%(title).100s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'noplaylist': True,
                        'format': 'best',
                        'progress_hooks': [self._progress_hook],
                        'socket_timeout': 30,
                        'retries': 3,
                    }
                    # 降级模式同样需要 cookies（修复抖音 Fresh cookies needed）
                    cookie_opts = self._detect_cookies()
                    if cookie_opts:
                        ydl_opts2.update(cookie_opts)
                    with yt_dlp.YoutubeDL(ydl_opts2) as ydl:
                        info = ydl.extract_info(url, download=True)
                        if info:
                            title = info.get('title', '视频')
                            self._last_video_save_dir = self.video_folder
                            self.log(f"降级模式下载成功：{title}")
                            self.after(0, lambda: (
                                self.open_folder_btn.configure(state="normal"),
                                messagebox.showinfo("下载完成", f"降级模式下载成功！\n标题：{title}")
                            ))
                            return
                except Exception as e2:
                    self.log(f"降级模式也失败：{str(e2)[:100]}")

            # 检测是否因为缺少 ffmpeg 导致音视频合并失败
            if not ffmpeg_available and ('postprocessing' in err_msg.lower() or
                                          'merge' in err_msg.lower() or
                                          'ffmpeg' in err_msg.lower()):
                self.log("提示：该视频需要 ffmpeg 合并音视频，请运行 安装.bat 安装 ffmpeg")
                self.after(0, lambda: messagebox.showerror(
                    "缺少 ffmpeg",
                    "该视频需要 ffmpeg 来合并音视频流。\n\n请运行项目目录下的「安装.bat」自动安装 ffmpeg，\n然后重试下载。"
                ))
                return

            self.after(0, lambda: messagebox.showerror("下载失败", f"视频下载失败：\n{err_msg[:150]}"))
        except Exception as e:
            self.log(f"下载失败：{str(e)[:200]}")
            self.after(0, lambda: messagebox.showerror("失败", f"下载出错：{str(e)[:200]}"))
        finally:
            self._downloading = False
            self.after(0, lambda: (
                self.video_btn.configure(state="normal"),
                self.video_progress_label.configure(text="就绪")
            ))
