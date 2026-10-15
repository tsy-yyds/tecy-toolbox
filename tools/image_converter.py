# -*- coding: utf-8 -*-
"""
图片格式转换工具 - 支持批量处理、质量调节、进度显示
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading


class ImageConverterFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.image_files = []
        self._converting = False
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="图片格式转换 / 压缩",
                             font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 15))

        # 选择图片区域
        select_frame = ctk.CTkFrame(self)
        select_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(select_frame, text="添加图片", command=self.add_images).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(select_frame, text="添加文件夹", command=self.add_folder).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(select_frame, text="清空列表", fg_color="gray", command=self.clear_list).pack(side="left", padx=5, pady=10)

        self.count_label = ctk.CTkLabel(select_frame, text="已选择 0 张图片", text_color="gray")
        self.count_label.pack(side="right", padx=10, pady=10)

        # 图片列表
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.image_listbox = ctk.CTkTextbox(list_frame, height=150)
        self.image_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # 转换设置
        setting_frame = ctk.CTkFrame(self)
        setting_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(setting_frame, text="转换设置：",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 目标格式
        format_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(format_frame, text="目标格式：", width=100, anchor="w").pack(side="left")
        self.format_var = ctk.StringVar(value="JPG")
        format_options = ["JPG", "PNG", "WEBP", "BMP", "GIF", "ICO"]
        self.format_menu = ctk.CTkOptionMenu(format_frame, values=format_options,
                                             variable=self.format_var, width=150)
        self.format_menu.pack(side="left", padx=5)

        # 质量设置
        ctk.CTkLabel(format_frame, text="图片质量：", width=100, anchor="w").pack(side="left", padx=(20, 0))
        self.quality_slider = ctk.CTkSlider(format_frame, from_=10, to=100,
                                             number_of_steps=90, width=200)
        self.quality_slider.set(85)
        self.quality_slider.pack(side="left", padx=5)

        self.quality_label = ctk.CTkLabel(format_frame, text="85%", width=50)
        self.quality_label.pack(side="left")
        self.quality_slider.configure(
            command=lambda v: self.quality_label.configure(text=f"{int(v)}%"))

        # 输出文件夹
        output_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        output_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(output_frame, text="输出文件夹：", width=100, anchor="w").pack(side="left")
        self.output_entry = ctk.CTkEntry(
            output_frame,
            placeholder_text="默认保存到原文件夹的 converted 子文件夹")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(output_frame, text="浏览", width=80,
                       command=self.select_output).pack(side="left", padx=5)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 0))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                           text_color="#888888")
        self.progress_label.pack()

        # 转换按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.convert_btn = ctk.CTkButton(
            btn_frame,
            text="开始转换",
            fg_color="#28a745",
            hover_color="#218838",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_conversion
        )
        self.convert_btn.pack(side="left", padx=5)

    def add_images(self):
        """添加图片文件"""
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tiff"),
                       ("所有文件", "*.*")]
        )
        if files:
            self.image_files.extend(files)
            self.update_list()

    def add_folder(self):
        """添加整个文件夹的图片"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            for filename in os.listdir(folder):
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff']:
                    self.image_files.append(os.path.join(folder, filename))
            self.update_list()

    def clear_list(self):
        """清空列表"""
        self.image_files = []
        self.update_list()

    def update_list(self):
        """更新列表显示"""
        self.image_listbox.delete("1.0", "end")
        for i, f in enumerate(self.image_files):
            self.image_listbox.insert("end", f"[{i+1}] {os.path.basename(f)}\n")
        self.count_label.configure(text=f"已选择 {len(self.image_files)} 张图片")

    def select_output(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)

    def start_conversion(self):
        """在多线程中启动转换，避免UI卡顿"""
        if not self.image_files:
            messagebox.showwarning("提示", "请先添加要转换的图片")
            return
        if self._converting:
            messagebox.showwarning("提示", "正在转换中，请稍候...")
            return

        self._converting = True
        self.convert_btn.configure(state="disabled", text="转换中...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="准备中...")

        output_folder = self.output_entry.get().strip()
        target_format = self.format_var.get().upper()
        quality = int(self.quality_slider.get())

        thread = threading.Thread(
            target=self._convert_images,
            args=(output_folder, target_format, quality),
            daemon=True
        )
        thread.start()

    def _convert_images(self, output_folder, target_format, quality):
        """在后台线程中执行批量转换"""
        total = len(self.image_files)
        success = 0
        errors = []

        format_map = {
            "JPG": ("jpg", "JPEG"),
            "PNG": ("png", "PNG"),
            "WEBP": ("webp", "WEBP"),
            "BMP": ("bmp", "BMP"),
            "GIF": ("gif", "GIF"),
            "ICO": ("ico", "ICO")
        }
        ext, pil_format = format_map.get(target_format, ("jpg", "JPEG"))

        for idx, img_path in enumerate(self.image_files):
            try:
                # 确定输出路径
                if output_folder:
                    out_dir = output_folder
                else:
                    out_dir = os.path.join(os.path.dirname(img_path), "converted")

                os.makedirs(out_dir, exist_ok=True)

                # 打开图片
                img = Image.open(img_path)
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                out_path = os.path.join(out_dir, f"{base_name}.{ext}")

                # 格式转换
                if target_format in ["JPG", "WEBP"]:
                    if img.mode in ('RGBA', 'P', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(
                            img,
                            mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                        )
                        img = background
                    img.save(out_path, format=pil_format, quality=quality, optimize=True)
                elif target_format == "PNG":
                    img.save(out_path, format=pil_format, optimize=True)
                elif target_format == "ICO":
                    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                    img.save(out_path, format=pil_format, sizes=icon_sizes)
                else:
                    img.save(out_path, format=pil_format)

                success += 1

            except Exception as e:
                errors.append(f"{os.path.basename(img_path)}: {str(e)}")

            # 更新进度
            pct = (idx + 1) / total
            self.after(0, lambda p=pct, i=idx+1, t=total, s=success, e=len(errors): (
                self.progress_bar.set(p),
                self.progress_label.configure(text=f"{i}/{t}  成功 {s}  失败 {e}")
            ))

        # 完成
        final_msg = f"成功转换 {success} 张图片"
        if errors:
            final_msg += f"\n失败 {len(errors)} 张：\n" + "\n".join(errors[:10])

        self.after(0, lambda: (
            setattr(self, '_converting', False),
            self.convert_btn.configure(state="normal", text="开始转换"),
            self.progress_label.configure(text="转换完成"),
            messagebox.showinfo("完成", final_msg) if not errors else messagebox.showwarning("完成", final_msg)
        ))
