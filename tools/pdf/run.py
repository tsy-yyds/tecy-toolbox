import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
import fitz  # PyMuPDF (PDF转图片核心)

# 主题配置
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class PDFToolkit(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📄 PDF全能工具箱 | 最终版")
        self.geometry("800x600")
        self.minsize(700, 500)

        # 主标签页
        self.tab_view = ctk.CTkTabview(self, corner_radius=10)
        self.tab_view.pack(pady=15, padx=20, fill="both", expand=True)

        # 功能标签
        self.tab_merge = self.tab_view.add("🔗 合并PDF")
        self.tab_split = self.tab_view.add("✂️ 拆分PDF")
        self.tab_text = self.tab_view.add("📝 提取文本")
        self.tab_img = self.tab_view.add("🖼️ PDF转图片")  # 你要的功能
        self.tab_word = self.tab_view.add("📄 PDF转Word")

        # 初始化界面
        self.init_merge_tab()
        self.init_split_tab()
        self.init_text_tab()
        self.init_pdf_to_image()
        self.init_word_tab()

    # 日志输出
    def log(self, widget, text):
        widget.insert(ctk.END, text + "\n")
        widget.see(ctk.END)

    # -------------------------- 1. 合并PDF --------------------------
    def init_merge_tab(self):
        self.merge_files = []
        frame = ctk.CTkFrame(self.tab_merge, corner_radius=10)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(frame, text="选择多个PDF文件", font=("微软雅黑",13)).pack(pady=5)
        self.merge_listbox = ctk.CTkTextbox(frame, height=150)
        self.merge_listbox.pack(pady=5, padx=10, fill="x")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="添加PDF", command=self.add_merge_pdf).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="清空列表", command=lambda: self.merge_listbox.delete(1.0,ctk.END)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="开始合并", command=self.merge_pdf, fg_color="#2563eb").pack(side="left", padx=5)

        self.merge_log = ctk.CTkTextbox(frame, height=120)
        self.merge_log.pack(pady=10, padx=10, fill="both", expand=True)
        self.log(self.merge_log, "✅ 添加PDF文件，点击合并即可生成新文件！")

    def add_merge_pdf(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF文件", "*.pdf")])
        if files:
            self.merge_files.extend(files)
            for f in files:
                self.merge_listbox.insert(ctk.END, os.path.basename(f) + "\n")

    def merge_pdf(self):
        if not self.merge_files:
            messagebox.showerror("错误", "请先添加PDF文件！")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF文件", "*.pdf")])
        if not save_path:
            return

        self.log(self.merge_log, "🔄 开始合并...")
        try:
            writer = PdfWriter()
            for file in self.merge_files:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(self.merge_log, f"🎉 合并完成！保存至：{os.path.basename(save_path)}")
            messagebox.showinfo("成功", "PDF合并完成！")
        except Exception as e:
            self.log(self.merge_log, f"❌ 失败：{str(e)}")

    # -------------------------- 2. 拆分PDF --------------------------
    def init_split_tab(self):
        frame = ctk.CTkFrame(self.tab_split, corner_radius=10)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(top_frame, text="PDF文件：", font=("微软雅黑",12)).grid(row=0,column=0,padx=5)
        self.split_path = ctk.StringVar()
        ctk.CTkEntry(top_frame, textvariable=self.split_path, width=400).grid(row=0,column=1,padx=5)
        ctk.CTkButton(top_frame, text="选择", command=self.select_split_pdf).grid(row=0,column=2,padx=5)

        ctk.CTkLabel(top_frame, text="拆分页码（如：1-5,7）：", font=("微软雅黑",12)).grid(row=1,column=0,padx=5,pady=8)
        self.split_page = ctk.CTkEntry(top_frame, width=400)
        self.split_page.grid(row=1,column=1,padx=5,pady=8)

        ctk.CTkButton(frame, text="开始拆分", command=self.split_pdf, fg_color="#2563eb").pack(pady=5)
        self.split_log = ctk.CTkTextbox(frame, height=200)
        self.split_log.pack(pady=10, padx=10, fill="both", expand=True)
        self.log(self.split_log, "✅ 选择PDF → 输入页码 → 拆分！")

    def select_split_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if path:
            self.split_path.set(path)

    def split_pdf(self):
        path = self.split_path.get()
        pages = self.split_page.get()
        if not path or not pages:
            messagebox.showerror("错误", "请填写完整信息！")
            return
        save_dir = filedialog.askdirectory(title="选择保存文件夹")
        if not save_dir:
            return

        self.log(self.split_log, "🔄 开始拆分...")
        try:
            reader = PdfReader(path)
            total_pages = len(reader.pages)
            writer = PdfWriter()
            for part in pages.split(","):
                if "-" in part:
                    s, e = map(int, part.split("-"))
                    for i in range(s-1, e):
                        if i < total_pages: writer.add_page(reader.pages[i])
                else:
                    i = int(part)-1
                    if i < total_pages: writer.add_page(reader.pages[i])
            
            save_path = os.path.join(save_dir, "拆分结果.pdf")
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(self.split_log, f"🎉 拆分完成！保存至：{save_path}")
            messagebox.showinfo("成功", "PDF拆分完成！")
        except Exception as e:
            self.log(self.split_log, f"❌ 失败：{str(e)}")

    # -------------------------- 3. 提取文本 --------------------------
    def init_text_tab(self):
        frame = ctk.CTkFrame(self.tab_text, corner_radius=10)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        self.text_path = ctk.StringVar()
        ctk.CTkEntry(top_frame, textvariable=self.text_path, width=500).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="选择PDF", command=self.select_text_pdf).pack(side="left", padx=5)

        ctk.CTkButton(frame, text="提取文本", command=self.extract_text, fg_color="#2563eb").pack(pady=5)
        self.text_content = ctk.CTkTextbox(frame)
        self.text_content.pack(pady=10, padx=10, fill="both", expand=True)
        self.log(self.text_content, "✅ 选择PDF后一键提取所有文本！")

    def select_text_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if path:
            self.text_path.set(path)

    def extract_text(self):
        path = self.text_path.get()
        if not path:
            messagebox.showerror("错误", "请选择PDF文件！")
            return
        self.text_content.delete(1.0, ctk.END)
        try:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            self.text_content.insert(ctk.END, text)
            self.log(self.text_content, "🎉 文本提取完成！")
        except Exception as e:
            self.log(self.text_content, f"❌ 失败：{str(e)}")

    # -------------------------- 4. ✅ 你要的：PDF整页转高清图片 --------------------------
    def init_pdf_to_image(self):
        frame = ctk.CTkFrame(self.tab_img, corner_radius=10)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        self.pdf_img_path = ctk.StringVar()

        ctk.CTkEntry(top_frame, textvariable=self.pdf_img_path, width=500).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="选择PDF", command=self.select_pdf_img).pack(side="left", padx=5)

        ctk.CTkButton(frame, text="🚀 转换为图片", command=self.pdf_to_image, fg_color="#2563eb", height=40).pack(pady=10)
        
        self.img_log = ctk.CTkTextbox(frame)
        self.img_log.pack(pady=10, padx=10, fill="both", expand=True)
        self.log(self.img_log, "✅ PDF每一页 → 高清PNG图片")
        self.log(self.img_log, "ℹ️ 无损清晰度，直接保存")

    def select_pdf_img(self):
        path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if path:
            self.pdf_img_path.set(path)

    def pdf_to_image(self):
        pdf_path = self.pdf_img_path.get()
        if not pdf_path:
            messagebox.showerror("错误", "请选择PDF文件！")
            return

        save_dir = filedialog.askdirectory(title="选择图片保存文件夹")
        if not save_dir:
            return

        self.log(self.img_log, "🔄 正在转换PDF为图片...")
        try:
            doc = fitz.open(pdf_path)
            # 遍历每一页转图片
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 高清渲染
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                # 保存图片
                img_path = os.path.join(save_dir, f"第{page_num+1}页.png")
                pix.save(img_path)

            self.log(self.img_log, f"🎉 转换完成！共 {len(doc)} 页")
            messagebox.showinfo("成功", f"PDF转图片完成！\n共{len(doc)}页高清图片")
        except Exception as e:
            self.log(self.img_log, f"❌ 转换失败：{str(e)}")

    # -------------------------- 5. PDF转Word --------------------------
    def init_word_tab(self):
        frame = ctk.CTkFrame(self.tab_word, corner_radius=10)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=5)
        self.word_path = ctk.StringVar()
        ctk.CTkEntry(top_frame, textvariable=self.word_path, width=500).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="选择PDF", command=self.select_word_pdf).pack(side="left", padx=5)

        ctk.CTkButton(frame, text="🚀 一键转Word", command=self.convert_to_word, fg_color="#2563eb", height=40).pack(pady=10)
        
        self.word_log = ctk.CTkTextbox(frame)
        self.word_log.pack(pady=10, padx=10, fill="both", expand=True)
        self.log(self.word_log, "✅ 转换为可编辑Word文档")

    def select_word_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if path:
            self.word_path.set(path)

    def convert_to_word(self):
        pdf_path = self.word_path.get()
        if not pdf_path:
            messagebox.showerror("错误", "请先选择PDF文件！")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word文档", "*.docx")])
        if not save_path:
            return

        self.log(self.word_log, "🔄 正在转换...")
        try:
            reader = PdfReader(pdf_path)
            doc = Document()
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    doc.add_paragraph(text)
            doc.save(save_path)
            self.log(self.word_log, "🎉 转换成功！")
            messagebox.showinfo("成功", "PDF转Word完成！")
        except Exception as e:
            self.log(self.word_log, f"❌ 失败：{str(e)}")

if __name__ == "__main__":
    app = PDFToolkit()
    app.mainloop()