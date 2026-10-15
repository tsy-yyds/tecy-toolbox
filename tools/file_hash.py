# -*- coding: utf-8 -*-
"""
文件哈希校验工具 - 计算文件的 MD5、SHA1、SHA256 等哈希值
支持单个文件和批量校验
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import hashlib
import os
import threading


class FileHashFrame(ctk.CTkFrame):
    """文件哈希校验器"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._computing = False
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="文件哈希校验",
                             font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 15))

        tip = ctk.CTkLabel(
            self,
            text="计算文件的 MD5 / SHA1 / SHA256 哈希值，用于校验文件完整性和唯一性",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        tip.pack(pady=(0, 10))

        # 文件选择区域
        select_frame = ctk.CTkFrame(self)
        select_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(select_frame, text="选择文件：", width=80).pack(side="left", padx=10, pady=10)
        self.file_path_entry = ctk.CTkEntry(select_frame, placeholder_text="选择文件或拖拽到此处...")
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=10)

        ctk.CTkButton(select_frame, text="浏览", width=80,
                       command=self.select_file).pack(side="left", padx=5, pady=10)

        # 多文件模式
        multi_frame = ctk.CTkFrame(self)
        multi_frame.pack(fill="x", padx=20, pady=5)

        self.multi_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(multi_frame, text="批量模式（选择文件夹内所有文件）",
                        variable=self.multi_var, command=self._toggle_multi).pack(side="left", padx=10, pady=10)

        # 算法选择
        algo_frame = ctk.CTkFrame(self)
        algo_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(algo_frame, text="哈希算法：", width=80).pack(side="left", padx=10, pady=10)

        self.md5_var = ctk.BooleanVar(value=True)
        self.sha1_var = ctk.BooleanVar(value=False)
        self.sha256_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(algo_frame, text="MD5", variable=self.md5_var).pack(side="left", padx=5, pady=10)
        ctk.CTkCheckBox(algo_frame, text="SHA-1", variable=self.sha1_var).pack(side="left", padx=5, pady=10)
        ctk.CTkCheckBox(algo_frame, text="SHA-256", variable=self.sha256_var).pack(side="left", padx=5, pady=10)

        # 比对哈希值（可选）
        compare_frame = ctk.CTkFrame(self)
        compare_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(compare_frame, text="比对哈希：", width=80).pack(side="left", padx=10, pady=10)
        self.compare_entry = ctk.CTkEntry(
            compare_frame,
            placeholder_text="输入已知哈希值进行比对校验（可选）")
        self.compare_entry.pack(side="left", fill="x", expand=True, padx=5, pady=10)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 0))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                           text_color="#888888")
        self.progress_label.pack()

        # 计算按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.calc_btn = ctk.CTkButton(
            btn_frame,
            text="开始计算",
            fg_color="#4A90D9",
            hover_color="#357ABD",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_compute
        )
        self.calc_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="复制结果", width=100,
            fg_color="gray", command=self.copy_result
        ).pack(side="left", padx=5)

        # 结果显示
        result_frame = ctk.CTkFrame(self)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(result_frame, text="计算结果：",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.result_box = ctk.CTkTextbox(result_frame, height=200, font=("Consolas", 11))
        self.result_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _toggle_multi(self):
        if self.multi_var.get():
            self.file_path_entry.configure(placeholder_text="选择文件夹...")
        else:
            self.file_path_entry.configure(placeholder_text="选择文件或拖拽到此处...")

    def select_file(self):
        if self.multi_var.get():
            folder = filedialog.askdirectory(title="选择文件夹")
            if folder:
                self.file_path_entry.delete(0, "end")
                self.file_path_entry.insert(0, folder)
        else:
            file = filedialog.askopenfilename(title="选择文件")
            if file:
                self.file_path_entry.delete(0, "end")
                self.file_path_entry.insert(0, file)

    def start_compute(self):
        path = self.file_path_entry.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择文件或文件夹！")
            return
        if not os.path.exists(path):
            messagebox.showerror("错误", "所选路径不存在！")
            return
        if self._computing:
            messagebox.showwarning("提示", "正在计算中，请稍候...")
            return

        # 收集要计算的算法
        algorithms = []
        if self.md5_var.get():
            algorithms.append("MD5")
        if self.sha1_var.get():
            algorithms.append("SHA1")
        if self.sha256_var.get():
            algorithms.append("SHA256")

        if not algorithms:
            messagebox.showwarning("提示", "请至少选择一种哈希算法！")
            return

        self._computing = True
        self.calc_btn.configure(state="disabled", text="计算中...")
        self.result_box.delete("1.0", "end")
        self.progress_bar.set(0)
        self.progress_label.configure(text="正在计算...")

        compare_hash = self.compare_entry.get().strip()

        thread = threading.Thread(
            target=self._compute_hashes,
            args=(path, algorithms, compare_hash),
            daemon=True
        )
        thread.start()

    def _compute_hashes(self, path, algorithms, compare_hash):
        """在后台线程中计算哈希"""
        # 收集文件列表
        if os.path.isfile(path):
            files = [path]
        else:
            files = []
            for root, dirs, filenames in os.walk(path):
                for f in filenames:
                    files.append(os.path.join(root, f))

        total = len(files)
        results = []

        for idx, file_path in enumerate(files):
            try:
                file_size = os.path.getsize(file_path)
                size_display = self._format_size(file_size)

                hashes = {}
                for algo in algorithms:
                    hasher = hashlib.new(algo.lower().replace('-', ''))
                    with open(file_path, "rb") as f:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                            hasher.update(chunk)
                    hashes[algo] = hasher.hexdigest()

                matched = False
                if compare_hash:
                    for hv in hashes.values():
                        if hv.lower() == compare_hash.lower():
                            matched = True
                            break

                result_line = f"[{idx + 1}/{total}] {os.path.basename(file_path)} ({size_display})"
                for algo in algorithms:
                    result_line += f"\n  {algo}: {hashes[algo]}"
                if matched:
                    result_line += "\n  >>> 哈希匹配！"
                results.append(result_line + "\n")

            except Exception as e:
                results.append(f"[{idx + 1}/{total}] {os.path.basename(file_path)} - 错误: {str(e)}\n")

            # 更新进度
            pct = (idx + 1) / total if total > 0 else 1.0
            self.after(0, lambda p=pct, i=idx+1, t=total: (
                self.progress_bar.set(p),
                self.progress_label.configure(text=f"{i}/{t}")
            ))

        self.after(0, lambda: (
            setattr(self, '_computing', False),
            self.calc_btn.configure(state="normal", text="开始计算"),
            self.result_box.insert("end", "".join(results)),
            self.progress_label.configure(text="计算完成")
        ))

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def copy_result(self):
        """复制结果到剪贴板"""
        result = self.result_box.get("1.0", "end").strip()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)
            messagebox.showinfo("已复制", "哈希结果已复制到剪贴板")
