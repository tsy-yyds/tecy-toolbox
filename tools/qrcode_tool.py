# -*- coding: utf-8 -*-
"""
二维码生成工具
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import qrcode
from PIL import Image, ImageTk
import os
from io import BytesIO


class QRCodeFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.qr_image = None
        self.current_qr = None
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="📱 二维码生成器", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 15))

        # 左右分栏
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # 左侧 - 输入区域
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_frame, text="输入内容（文字/网址/联系方式等）：", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.content_text = ctk.CTkTextbox(left_frame, height=150)
        self.content_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.content_text.insert("end", "https://www.example.com")

        # 设置区域
        setting_frame = ctk.CTkFrame(left_frame)
        setting_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(setting_frame, text="二维码设置：", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 大小设置
        size_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(size_frame, text="二维码大小：", width=100, anchor="w").pack(side="left")
        self.size_var = ctk.StringVar(value="300x300")
        size_options = ["200x200", "300x300", "400x400", "500x500", "800x800"]
        ctk.CTkOptionMenu(size_frame, values=size_options, variable=self.size_var, width=150).pack(side="left", padx=5)

        # 容错级别
        error_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        error_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(error_frame, text="容错级别：", width=100, anchor="w").pack(side="left")
        self.error_var = ctk.StringVar(value="中等 (M)")
        error_options = ["低 (L)", "中等 (M)", "较高 (Q)", "高 (H)"]
        ctk.CTkOptionMenu(error_frame, values=error_options, variable=self.error_var, width=150).pack(side="left", padx=5)

        # 颜色设置
        color_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(color_frame, text="前景色：", width=100, anchor="w").pack(side="left")
        self.fg_color_entry = ctk.CTkEntry(color_frame, width=150)
        self.fg_color_entry.insert(0, "#000000")
        self.fg_color_entry.pack(side="left", padx=5)

        ctk.CTkLabel(color_frame, text="背景色：", width=80, anchor="w").pack(side="left", padx=(10, 0))
        self.bg_color_entry = ctk.CTkEntry(color_frame, width=150)
        self.bg_color_entry.insert(0, "#FFFFFF")
        self.bg_color_entry.pack(side="left", padx=5)

        # 按钮
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="🎨 生成二维码", command=self.generate_qr).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="💾 保存图片", fg_color="#28a745", hover_color="#218838", command=self.save_qr).pack(side="left", padx=5)

        # 右侧 - 预览区域
        right_frame = ctk.CTkFrame(main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)

        ctk.CTkLabel(right_frame, text="预览：", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))

        self.preview_label = ctk.CTkLabel(right_frame, text="点击左侧「生成二维码」\n查看预览效果", width=300, height=300, fg_color="#f0f0f0", corner_radius=10)
        self.preview_label.pack(padx=10, pady=10)

        self.info_label = ctk.CTkLabel(right_frame, text="", text_color="gray", wraplength=300)
        self.info_label.pack(pady=5)

    def generate_qr(self):
        """生成二维码"""
        content = self.content_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("提示", "请输入二维码内容")
            return

        # 解析大小
        size_str = self.size_var.get()
        size = int(size_str.split('x')[0])

        # 解析容错级别
        error_map = {
            "低 (L)": qrcode.constants.ERROR_CORRECT_L,
            "中等 (M)": qrcode.constants.ERROR_CORRECT_M,
            "较高 (Q)": qrcode.constants.ERROR_CORRECT_Q,
            "高 (H)": qrcode.constants.ERROR_CORRECT_H
        }
        error_level = error_map.get(self.error_var.get(), qrcode.constants.ERROR_CORRECT_M)

        # 颜色
        fg_color = self.fg_color_entry.get().strip() or "#000000"
        bg_color = self.bg_color_entry.get().strip() or "#FFFFFF"

        try:
            # 生成二维码
            qr = qrcode.QRCode(
                version=None,
                error_correction=error_level,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fg_color, back_color=bg_color)
            img = img.resize((size, size), Image.LANCZOS)

            self.current_qr = img

            # 显示预览
            preview_img = img.copy()
            preview_img.thumbnail((300, 300))
            self.qr_image = ImageTk.PhotoImage(preview_img)
            self.preview_label.configure(image=self.qr_image, text="")

            # 显示信息
            content_len = len(content)
            self.info_label.configure(text=f"内容长度：{content_len} 字符\n图片尺寸：{size}×{size} 像素")

        except Exception as e:
            messagebox.showerror("错误", f"生成二维码失败：{str(e)}")

    def save_qr(self):
        """保存二维码"""
        if not self.current_qr:
            messagebox.showwarning("提示", "请先生成二维码")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存二维码",
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("JPG 图片", "*.jpg"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                self.current_qr.save(file_path)
                messagebox.showinfo("成功", f"二维码已保存到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{str(e)}")
