# -*- coding: utf-8 -*-
"""
番茄钟工具
"""

import customtkinter as ctk
from tkinter import messagebox
import time
import threading


class PomodoroFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.is_running = False
        self.is_paused = False
        self.remaining_time = 0
        self.timer_thread = None
        self.mode = "work"  # work / short_break / long_break

        # 默认时间（分钟）
        self.work_time = 25
        self.short_break_time = 5
        self.long_break_time = 15
        self.pomodoros_completed = 0

        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="🍅 番茄钟 - 专注计时器", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 10))

        # 模式选择
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(padx=20, pady=5)

        self.work_btn = ctk.CTkButton(mode_frame, text="专注 25分钟", width=120, fg_color="#e74c3c", hover_color="#c0392b", command=lambda: self.set_mode("work"))
        self.work_btn.pack(side="left", padx=5, pady=10)

        self.short_btn = ctk.CTkButton(mode_frame, text="短休息 5分钟", width=120, fg_color="gray", command=lambda: self.set_mode("short_break"))
        self.short_btn.pack(side="left", padx=5, pady=10)

        self.long_btn = ctk.CTkButton(mode_frame, text="长休息 15分钟", width=120, fg_color="gray", command=lambda: self.set_mode("long_break"))
        self.long_btn.pack(side="left", padx=5, pady=10)

        # 时间显示
        timer_frame = ctk.CTkFrame(self, fg_color="transparent")
        timer_frame.pack(padx=20, pady=20)

        self.timer_label = ctk.CTkLabel(
            timer_frame,
            text="25:00",
            font=ctk.CTkFont(size=80, weight="bold"),
            text_color="#e74c3c"
        )
        self.timer_label.pack()

        self.status_label = ctk.CTkLabel(
            timer_frame,
            text="准备开始专注工作",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.status_label.pack(pady=(5, 0))

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=10)
        self.progress_bar.set(1.0)
        self.progress_bar.pack(padx=20, pady=5)

        # 控制按钮
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(padx=20, pady=15)

        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ 开始",
            width=100,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_timer
        )
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = ctk.CTkButton(
            control_frame,
            text="⏸️ 暂停",
            width=100,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#f39c12",
            hover_color="#d68910",
            command=self.pause_timer,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)

        self.reset_btn = ctk.CTkButton(
            control_frame,
            text="🔄 重置",
            width=100,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="gray",
            command=self.reset_timer
        )
        self.reset_btn.pack(side="left", padx=5)

        # 统计信息
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(stats_frame, text="📊 今日统计", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=10, pady=(0, 10))

        self.pomodoro_count_label = ctk.CTkLabel(stats_inner, text=f"🍅 完成番茄数：0", font=ctk.CTkFont(size=14))
        self.pomodoro_count_label.pack(side="left", padx=10)

        self.focus_time_label = ctk.CTkLabel(stats_inner, text="⏱️ 专注时长：0 分钟", font=ctk.CTkFont(size=14))
        self.focus_time_label.pack(side="left", padx=10)

        # 设置区域
        setting_frame = ctk.CTkFrame(self)
        setting_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(setting_frame, text="⚙️ 时间设置（分钟）", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        setting_inner = ctk.CTkFrame(setting_frame, fg_color="transparent")
        setting_inner.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(setting_inner, text="专注：").pack(side="left")
        self.work_entry = ctk.CTkEntry(setting_inner, width=60)
        self.work_entry.insert(0, "25")
        self.work_entry.pack(side="left", padx=5)

        ctk.CTkLabel(setting_inner, text="短休息：").pack(side="left", padx=(10, 0))
        self.short_entry = ctk.CTkEntry(setting_inner, width=60)
        self.short_entry.insert(0, "5")
        self.short_entry.pack(side="left", padx=5)

        ctk.CTkLabel(setting_inner, text="长休息：").pack(side="left", padx=(10, 0))
        self.long_entry = ctk.CTkEntry(setting_inner, width=60)
        self.long_entry.insert(0, "15")
        self.long_entry.pack(side="left", padx=5)

        ctk.CTkButton(setting_inner, text="应用设置", width=100, command=self.apply_settings).pack(side="left", padx=10)

    def set_mode(self, mode):
        """设置模式"""
        if self.is_running and not self.is_paused:
            if not messagebox.askyesno("确认", "计时器正在运行，确定要切换模式吗？"):
                return

        self.mode = mode
        self.is_running = False
        self.is_paused = False

        # 更新按钮样式
        self.work_btn.configure(fg_color="#e74c3c" if mode == "work" else "gray")
        self.short_btn.configure(fg_color="#27ae60" if mode == "short_break" else "gray")
        self.long_btn.configure(fg_color="#3498db" if mode == "long_break" else "gray")

        # 设置时间
        if mode == "work":
            self.remaining_time = self.work_time * 60
            self.timer_label.configure(text=f"{self.work_time:02d}:00", text_color="#e74c3c")
            self.status_label.configure(text="准备开始专注工作")
        elif mode == "short_break":
            self.remaining_time = self.short_break_time * 60
            self.timer_label.configure(text=f"{self.short_break_time:02d}:00", text_color="#27ae60")
            self.status_label.configure(text="休息一下，放松眼睛")
        else:
            self.remaining_time = self.long_break_time * 60
            self.timer_label.configure(text=f"{self.long_break_time:02d}:00", text_color="#3498db")
            self.status_label.configure(text="好好休息，恢复精力")

        self.progress_bar.set(1.0)
        self.start_btn.configure(state="normal", text="▶️ 开始")
        self.pause_btn.configure(state="disabled")

    def start_timer(self):
        """开始计时"""
        if self.is_paused:
            # 继续
            self.is_paused = False
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal", text="⏸️ 暂停")
            self.status_label.configure(text="专注中..." if self.mode == "work" else "休息中...")
            return

        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")

        if self.mode == "work":
            self.status_label.configure(text="专注中...加油！💪")
        elif self.mode == "short_break":
            self.status_label.configure(text="短休息中...放松一下 ☕")
        else:
            self.status_label.configure(text="长休息中...好好休息 🌿")

        # 启动计时线程
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()

    def pause_timer(self):
        """暂停计时"""
        if not self.is_running:
            return

        if self.is_paused:
            # 继续
            self.is_paused = False
            self.pause_btn.configure(text="⏸️ 暂停")
            self.status_label.configure(text="专注中..." if self.mode == "work" else "休息中...")
        else:
            # 暂停
            self.is_paused = True
            self.pause_btn.configure(text="▶️ 继续")
            self.start_btn.configure(state="normal")
            self.status_label.configure(text="已暂停")

    def reset_timer(self):
        """重置计时器"""
        if self.is_running:
            if not messagebox.askyesno("确认", "确定要重置计时器吗？"):
                return

        self.is_running = False
        self.is_paused = False

        # 重置到当前模式的初始时间
        self.set_mode(self.mode)

    def run_timer(self):
        """计时线程"""
        total_time = self.remaining_time

        while self.remaining_time > 0 and self.is_running:
            if not self.is_paused:
                minutes = self.remaining_time // 60
                seconds = self.remaining_time % 60
                progress = self.remaining_time / total_time if total_time > 0 else 0

                # 更新UI（在lambda中捕获当前值避免延迟绑定）
                self.after(0, lambda m=minutes, s=seconds: self.update_display(m, s))
                self.after(0, lambda p=progress: self.progress_bar.set(p))

                time.sleep(1)
                self.remaining_time -= 1
            else:
                time.sleep(0.1)

        if self.remaining_time <= 0 and self.is_running:
            self.after(0, self.timer_finished)

    def update_display(self, minutes, seconds):
        """更新时间显示"""
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

    def timer_finished(self):
        """计时结束"""
        self.is_running = False
        self.is_paused = False

        self.timer_label.configure(text="00:00")
        self.progress_bar.set(0)
        self.start_btn.configure(state="normal", text="▶️ 开始")
        self.pause_btn.configure(state="disabled")

        # 更新统计
        if self.mode == "work":
            self.pomodoros_completed += 1
            self.pomodoro_count_label.configure(text=f"🍅 完成番茄数：{self.pomodoros_completed}")
            total_minutes = self.pomodoros_completed * self.work_time
            self.focus_time_label.configure(text=f"⏱️ 专注时长：{total_minutes} 分钟")

        # 提示
        if self.mode == "work":
            messagebox.showinfo("番茄完成！🎉", f"太棒了！你完成了一个番茄钟！\n\n已完成 {self.pomodoros_completed} 个番茄\n\n休息一下吧~")
            # 自动切换到休息模式
            if self.pomodoros_completed % 4 == 0:
                self.set_mode("long_break")
            else:
                self.set_mode("short_break")
        else:
            messagebox.showinfo("休息结束！⏰", "休息时间到！\n\n准备好开始下一个番茄了吗？")
            self.set_mode("work")

    def apply_settings(self):
        """应用时间设置"""
        try:
            work = int(self.work_entry.get())
            short = int(self.short_entry.get())
            long_break = int(self.long_entry.get())

            if work <= 0 or short <= 0 or long_break <= 0:
                raise ValueError("时间必须大于0")

            if work > 180 or short > 60 or long_break > 120:
                raise ValueError("时间太长了，请设置合理的时间")

            self.work_time = work
            self.short_break_time = short
            self.long_break_time = long_break

            # 如果当前没在运行，更新显示
            if not self.is_running:
                self.set_mode(self.mode)

            messagebox.showinfo("成功", "时间设置已应用！")

        except ValueError as e:
            messagebox.showerror("错误", f"设置失败：{str(e)}")
