# -*- coding: utf-8 -*-
"""
文件批量重命名工具
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import re


class FileRenamerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.file_list = []
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="📝 文件批量重命名", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 15))

        # 选择文件夹区域
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(folder_frame, text="选择文件夹：", font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)

        self.folder_entry = ctk.CTkEntry(folder_frame, width=400, placeholder_text="点击右侧按钮选择文件夹")
        self.folder_entry.pack(side="left", padx=5, pady=10)

        ctk.CTkButton(folder_frame, text="浏览", width=80, command=self.select_folder).pack(side="left", padx=5, pady=10)

        # 重命名规则区域
        rule_frame = ctk.CTkFrame(self)
        rule_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(rule_frame, text="重命名规则：", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 前缀
        prefix_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
        prefix_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(prefix_frame, text="文件名前缀：", width=100, anchor="w").pack(side="left")
        self.prefix_entry = ctk.CTkEntry(prefix_frame, placeholder_text="例如：照片_")
        self.prefix_entry.pack(side="left", fill="x", expand=True, padx=5)

        # 起始编号
        num_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
        num_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(num_frame, text="起始编号：", width=100, anchor="w").pack(side="left")
        self.start_num_entry = ctk.CTkEntry(num_frame, placeholder_text="例如：1", width=150)
        self.start_num_entry.insert(0, "1")
        self.start_num_entry.pack(side="left", padx=5)

        ctk.CTkLabel(num_frame, text="编号位数：", width=100, anchor="w").pack(side="left", padx=(20, 0))
        self.digits_entry = ctk.CTkEntry(num_frame, placeholder_text="例如：3", width=150)
        self.digits_entry.insert(0, "3")
        self.digits_entry.pack(side="left", padx=5)

        # 后缀名处理
        ext_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
        ext_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(ext_frame, text="文件类型：", width=100, anchor="w").pack(side="left")
        self.ext_entry = ctk.CTkEntry(ext_frame, placeholder_text="留空表示所有文件，例如：.jpg .png")
        self.ext_entry.pack(side="left", fill="x", expand=True, padx=5)

        # 预览区域
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(preview_frame, text="重命名预览：", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.preview_textbox = ctk.CTkTextbox(preview_frame, height=150)
        self.preview_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 按钮区域
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_frame, text="🔍 预览效果", command=self.preview_rename).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✅ 开始重命名", fg_color="#28a745", hover_color="#218838", command=self.do_rename).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔄 重置", fg_color="gray", command=self.reset).pack(side="left", padx=5)

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要重命名文件的文件夹")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.load_files(folder)

    def load_files(self, folder):
        """加载文件列表"""
        self.file_list = []
        ext_filter = self.ext_entry.get().strip().lower()

        try:
            for filename in sorted(os.listdir(folder)):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    if ext_filter:
                        exts = ext_filter.split()
                        if any(filename.lower().endswith(ext) for ext in exts):
                            self.file_list.append(filename)
                    else:
                        self.file_list.append(filename)

            self.preview_textbox.delete("1.0", "end")
            self.preview_textbox.insert("end", f"找到 {len(self.file_list)} 个文件\n")
            for f in self.file_list[:10]:
                self.preview_textbox.insert("end", f"  {f}\n")
            if len(self.file_list) > 10:
                self.preview_textbox.insert("end", f"  ... 还有 {len(self.file_list) - 10} 个文件\n")
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹失败：{str(e)}")

    def preview_rename(self):
        """预览重命名效果"""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("提示", "请先选择有效的文件夹")
            return

        self.load_files(folder)

        if not self.file_list:
            messagebox.showwarning("提示", "没有找到符合条件的文件")
            return

        prefix = self.prefix_entry.get()
        try:
            start_num = int(self.start_num_entry.get())
            digits = int(self.digits_entry.get())
        except ValueError:
            messagebox.showerror("错误", "起始编号和编号位数必须是数字")
            return

        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("end", "重命名预览：\n\n")

        for i, old_name in enumerate(self.file_list):
            name, ext = os.path.splitext(old_name)
            new_num = str(start_num + i).zfill(digits)
            new_name = f"{prefix}{new_num}{ext}"
            self.preview_textbox.insert("end", f"  {old_name}  →  {new_name}\n")

    def do_rename(self):
        """执行重命名"""
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showwarning("提示", "请先选择有效的文件夹")
            return

        if not self.file_list:
            self.load_files(folder)

        if not self.file_list:
            messagebox.showwarning("提示", "没有找到符合条件的文件")
            return

        if not messagebox.askyesno("确认", f"确定要重命名这 {len(self.file_list)} 个文件吗？\n此操作不可撤销！"):
            return

        prefix = self.prefix_entry.get()
        try:
            start_num = int(self.start_num_entry.get())
            digits = int(self.digits_entry.get())
        except ValueError:
            messagebox.showerror("错误", "起始编号和编号位数必须是数字")
            return

        success_count = 0
        error_list = []

        for i, old_name in enumerate(self.file_list):
            old_path = os.path.join(folder, old_name)
            name, ext = os.path.splitext(old_name)
            new_num = str(start_num + i).zfill(digits)
            new_name = f"{prefix}{new_num}{ext}"
            new_path = os.path.join(folder, new_name)

            try:
                # 避免重名，先重命名为临时名
                temp_path = os.path.join(folder, f"__temp_rename_{i}_{ext}")
                os.rename(old_path, temp_path)
                os.rename(temp_path, new_path)
                success_count += 1
            except Exception as e:
                error_list.append(f"{old_name}: {str(e)}")

        # 重新加载文件列表
        self.load_files(folder)

        if error_list:
            messagebox.showwarning("完成", f"成功重命名 {success_count} 个文件\n失败 {len(error_list)} 个：\n" + "\n".join(error_list[:5]))
        else:
            messagebox.showinfo("成功", f"成功重命名 {success_count} 个文件！")

    def reset(self):
        """重置"""
        self.folder_entry.delete(0, "end")
        self.prefix_entry.delete(0, "end")
        self.start_num_entry.delete(0, "end")
        self.start_num_entry.insert(0, "1")
        self.digits_entry.delete(0, "end")
        self.digits_entry.insert(0, "3")
        self.ext_entry.delete(0, "end")
        self.preview_textbox.delete("1.0", "end")
        self.file_list = []
