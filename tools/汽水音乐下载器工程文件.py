import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import os
import threading
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 核心修改：脚本在tools内，向上跳转一层到项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

MUSIC_FOLDER = os.path.join(BASE_DIR, "汽水音乐下载")
VIDEO_FOLDER = os.path.join(BASE_DIR, "无水印视频下载")

# 调试打印
print("脚本目录(tools)：", SCRIPT_DIR)
print("项目根目录：", BASE_DIR)
print("音乐保存目录：", MUSIC_FOLDER)
print("视频保存目录：", VIDEO_FOLDER)

# 自动创建文件夹
for folder in [MUSIC_FOLDER, VIDEO_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"已创建文件夹：{folder}")


class SplashScreen:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.root.title("")
        self.root.geometry("600x200")
        self.root.overrideredirect(True)
        self.root.resizable(False, False)
        self.root.attributes("-alpha", 1.0)
        self.root.configure(bg="#1E1E2E")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 200) // 2
        self.root.geometry(f"600x200+{x}+{y}")
        self.label = tk.Label(
            self.root,
            text="仅用于个人学习用途，遵守版权法规，请勿商用",
            font=("微软雅黑", 16, "bold"),
            fg="white",
            bg="#1E1E2E"
        )
        self.label.pack(expand=True)
        self.phase = 0
        self.fade_out()

    def fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0:
            alpha -= 0.04
            self.root.attributes("-alpha", alpha)
            self.root.after(30, self.fade_out)
        else:
            self.next_phase()

    def next_phase(self):
        self.phase += 1
        if self.phase == 1:
            self.label.config(text="tsy制作")
            self.root.attributes("-alpha", 1.0)
            self.root.after(800, self.fade_out)
        else:
            self.root.destroy()
            self.callback()


class PremiumDownloader:
    def __init__(self, window):
        self.window = window
        self.window.title("🎵 汽水音乐 & 🎬 短视频 解析下载器")
        self.window.geometry("900x650")
        self.window.resizable(True, True)
        self.window.configure(bg="#F7F8FA")
        self.setup_style()
        main_container = ttk.Frame(window, padding=25, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(
            main_container,
            text="多功能解析下载工具",
            font=("微软雅黑", 22, "bold"),
            foreground="#2C3E50",
            background="#F7F8FA"
        )
        title_label.pack(pady=(0, 25))
        self.tab_control = ttk.Notebook(main_container, style="Modern.TNotebook")
        self.tab_music = ttk.Frame(self.tab_control)
        self.tab_video = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_music, text="🎵 音乐下载")
        self.tab_control.add(self.tab_video, text="🎬 视频下载")
        self.tab_control.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        self.build_music_tab()
        self.build_video_tab()
        self.build_log_area()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#F7F8FA")
        style.configure("Modern.TNotebook", tabposition="n", background="#FFFFFF", borderwidth=0)
        style.configure(
            "Modern.TNotebook.Tab",
            padding=(25, 12),
            font=("微软雅黑", 11, "bold"),
            borderwidth=0
        )
        style.map("Modern.TNotebook.Tab",
                  background=[("selected", "#4A6CF7"), ("!selected", "#ECEFF4")],
                  foreground=[("selected", "#FFFFFF"), ("!selected", "#4C566A")])
        style.configure("Action.TButton",
                        font=("微软雅黑", 10, "bold"),
                        background="#4A6CF7",
                        foreground="white",
                        padding=(18, 9))
        style.map("Action.TButton",
                  background=[("active", "#3A5CE2"), ("pressed", "#2A4BD0")])
        style.configure("Modern.TEntry", padding=10, font=("微软雅黑", 10))
        style.configure("Log.TLabelframe", font=("微软雅黑", 10, "bold"))

    def build_music_tab(self):
        frame = ttk.Frame(self.tab_music, padding=20, style="Main.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="音乐链接：", font=("微软雅黑", 11), background="#F7F8FA") \
            .grid(row=0, column=0, sticky="w", padx=5, pady=15)
        self.music_link = ttk.Entry(frame, style="Modern.TEntry", width=70)
        self.music_link.grid(row=0, column=1, padx=8, pady=15, sticky="we")
        self.music_link.insert(0, "粘贴汽水音乐分享链接")
        self.music_btn = ttk.Button(frame, text="解析并下载", style="Action.TButton",
                                    command=lambda: self.run_thread("music"))
        self.music_btn.grid(row=0, column=2, padx=8, pady=15)
        self.music_progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
        self.music_progress.grid(row=1, column=0, columnspan=3, sticky="we", padx=5, pady=5)
        self.music_progress.grid_remove()
        frame.columnconfigure(1, weight=1)

    def build_video_tab(self):
        frame = ttk.Frame(self.tab_video, padding=20, style="Main.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="视频链接：", font=("微软雅黑", 11), background="#F7F8FA") \
            .grid(row=0, column=0, sticky="w", padx=5, pady=15)
        self.video_link = ttk.Entry(frame, style="Modern.TEntry", width=70)
        self.video_link.grid(row=0, column=1, padx=8, pady=15, sticky="we")
        self.video_link.insert(0, "粘贴抖音/快手/B站等短视频链接")
        self.video_btn = ttk.Button(frame, text="解析并下载", style="Action.TButton",
                                    command=lambda: self.run_thread("video"))
        self.video_btn.grid(row=0, column=2, padx=8, pady=15)
        self.video_progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
        self.video_progress.grid(row=1, column=0, columnspan=3, sticky="we", padx=5, pady=5)
        self.video_progress.grid_remove()
        frame.columnconfigure(1, weight=1)

    def build_log_area(self):
        log_frame = ttk.LabelFrame(self.window, text="运行日志", padding=15,
                                   style="Log.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            width=100,
            height=16,
            font=("Consolas", 10),
            bg="#FFFFFF",
            relief="flat"
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log("✅ 工具启动成功，可正常解析音乐与视频~")

    def log(self, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{time_str}] {msg}\n")
        self.log_box.see(tk.END)

    def run_thread(self, mode):
        if mode == "music":
            url = self.music_link.get().strip()
            if not url or url == "粘贴汽水音乐分享链接":
                messagebox.showwarning("提示", "请输入有效音乐链接！")
                return
            self.music_progress.grid()
            self.music_progress.start()
            self.music_btn.config(state=tk.DISABLED)
            threading.Thread(target=self.download_music, args=(url,), daemon=True).start()
        else:
            url = self.video_link.get().strip()
            if not url or url == "粘贴抖音/快手/B站等短视频链接":
                messagebox.showwarning("提示", "请输入有效视频链接！")
                return
            self.video_progress.grid()
            self.video_progress.start()
            self.video_btn.config(state=tk.DISABLED)
            threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_music(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            self.log("🎵 正在解析音乐链接...")
            res = requests.get("https://tmini.net/api/dymusic", params={"url": url},
                               headers=headers, verify=False, timeout=30)
            data = res.json()
            if not data.get("url"):
                self.log("❌ 音乐解析失败，接口未返回音频地址")
                return
            title = data.get("name", "未知歌曲").replace("/", "").replace("\\", "").replace("|", "").replace("?", "")
            audio_url = data.get("url")
            self.log(f"✅ 解析成功：{title}")
            self.log("⬇️ 开始下载音频...")
            audio_res = requests.get(audio_url, headers=headers, verify=False, stream=True, timeout=60)
            save_path = os.path.join(MUSIC_FOLDER, f"{title}.mp4")
            with open(save_path, "wb") as f:
                for chunk in audio_res.iter_content(1024 * 1024):
                    f.write(chunk)
            self.log(f"🎉 音乐下载完成：{save_path}")
        except Exception as e:
            self.log(f"❌ 音乐下载失败：{str(e)}")
        finally:
            self.music_progress.stop()
            self.music_progress.grid_remove()
            self.music_btn.config(state=tk.NORMAL)

    def download_video(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            self.log("🎬 正在解析视频链接...")
            res = requests.get("https://tmini.net/api/shortvideo", params={"url": url},
                               headers=headers, verify=False, timeout=30)
            data = res.json()
            if data.get("code") != 200:
                self.log(f"❌ 视频解析失败：{data.get('msg', '未知错误')}")
                return
            video_info = data.get("data", {})
            if not video_info.get("url"):
                self.log("❌ 未获取到视频播放地址")
                return
            title = video_info.get("title", "未知视频").replace("/", "").replace("\\", "").replace("|", "").replace("?", "")
            video_url = video_info.get("url")
            self.log(f"✅ 解析成功：{title}")
            self.log("⬇️ 开始下载视频...")
            video_res = requests.get(video_url, headers=headers, verify=False, stream=True, timeout=120)
            save_path = os.path.join(VIDEO_FOLDER, f"{title}.mp4")
            with open(save_path, "wb") as f:
                for chunk in video_res.iter_content(1024 * 1024):
                    f.write(chunk)
            self.log(f"🎉 视频下载完成：{save_path}")
        except Exception as e:
            self.log(f"❌ 视频下载失败：{str(e)}")
        finally:
            self.video_progress.stop()
            self.video_progress.grid_remove()
            self.video_btn.config(state=tk.NORMAL)


def show_main():
    root = tk.Tk()
    app = PremiumDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root, show_main)
    splash_root.mainloop()