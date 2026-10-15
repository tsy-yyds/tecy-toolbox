# -*- coding: utf-8 -*-
"""
系统信息查看工具
"""

import customtkinter as ctk
import platform
import psutil
import os
import socket
import uuid
import time


class SystemInfoFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.create_widgets()
        # 延迟一下再刷新，确保界面已创建
        self.after(500, self.refresh_all)

    def create_widgets(self):
        # 标题
        title = ctk.CTkLabel(self, text="💻 系统信息查看", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 10))

        # 刷新按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(btn_frame, text="🔄 刷新信息", width=120, command=self.refresh_all).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📊 实时监控", width=120, command=self.toggle_monitor).pack(side="left", padx=5)

        self.monitor_label = ctk.CTkLabel(btn_frame, text="", text_color="gray")
        self.monitor_label.pack(side="left", padx=10)

        # 创建滚动区域
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 系统信息
        self.create_info_section("🖥️ 系统信息", [
            ("操作系统", "os_name"),
            ("系统版本", "os_version"),
            ("系统架构", "os_arch"),
            ("计算机名", "computer_name"),
            ("用户名", "user_name"),
        ])

        # CPU信息
        self.create_info_section("⚡ CPU 信息", [
            ("CPU 型号", "cpu_name"),
            ("物理核心数", "cpu_cores"),
            ("逻辑核心数", "cpu_threads"),
            ("当前频率", "cpu_freq"),
            ("CPU 使用率", "cpu_usage"),
        ])

        # 内存信息
        self.create_info_section("💾 内存信息", [
            ("总内存", "mem_total"),
            ("已使用", "mem_used"),
            ("可用内存", "mem_available"),
            ("内存使用率", "mem_percent"),
        ])

        # 磁盘信息
        self.create_info_section("💿 磁盘信息", [
            ("磁盘信息", "disk_info"),
        ])

        # 网络信息
        self.create_info_section("🌐 网络信息", [
            ("主机名", "hostname"),
            ("IP 地址", "ip_address"),
            ("MAC 地址", "mac_address"),
        ])

        # 运行时间
        self.create_info_section("⏱️ 运行时间", [
            ("系统运行时间", "uptime"),
        ])

        self.is_monitoring = False

    def create_info_section(self, title, fields):
        """创建一个信息区块"""
        section_frame = ctk.CTkFrame(self.scroll_frame)
        section_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # 存储标签引用
        self.labels = getattr(self, 'labels', {})

        for label_text, key in fields:
            row = ctk.CTkFrame(section_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=2)

            ctk.CTkLabel(row, text=label_text + "：", width=120, anchor="w", text_color="gray").pack(side="left")

            value_label = ctk.CTkLabel(row, text="获取中...", anchor="w")
            value_label.pack(side="left", fill="x", expand=True)

            self.labels[key] = value_label

    def refresh_all(self):
        """刷新所有信息"""
        try:
            # 系统信息
            self.labels['os_name'].configure(text=f"{platform.system()} {platform.release()}")
            self.labels['os_version'].configure(text=platform.version())
            self.labels['os_arch'].configure(text=platform.machine())
            self.labels['computer_name'].configure(text=platform.node())
            self.labels['user_name'].configure(text=os.environ.get('USERNAME', os.environ.get('USER', '未知')))

            # CPU信息
            try:
                cpu_name = platform.processor() or "未知"
            except:
                cpu_name = "未知"
            self.labels['cpu_name'].configure(text=cpu_name)
            self.labels['cpu_cores'].configure(text=f"{psutil.cpu_count(logical=False)} 核")
            self.labels['cpu_threads'].configure(text=f"{psutil.cpu_count(logical=True)} 线程")

            try:
                freq = psutil.cpu_freq()
                if freq:
                    self.labels['cpu_freq'].configure(text=f"{freq.current:.1f} MHz")
                else:
                    self.labels['cpu_freq'].configure(text="未知")
            except:
                self.labels['cpu_freq'].configure(text="未知")

            cpu_percent = psutil.cpu_percent(interval=0.5)
            self.labels['cpu_usage'].configure(text=f"{cpu_percent}%")

            # 内存信息
            mem = psutil.virtual_memory()
            self.labels['mem_total'].configure(text=self.format_bytes(mem.total))
            self.labels['mem_used'].configure(text=self.format_bytes(mem.used))
            self.labels['mem_available'].configure(text=self.format_bytes(mem.available))
            self.labels['mem_percent'].configure(text=f"{mem.percent}%")

            # 磁盘信息
            disk_text = ""
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_text += f"{partition.device} ({partition.mountpoint}) - 总: {self.format_bytes(usage.total)}, 已用: {self.format_bytes(usage.used)} ({usage.percent}%)\n"
                except:
                    disk_text += f"{partition.device} ({partition.mountpoint}) - 无法读取\n"

            self.labels['disk_info'].configure(text=disk_text.strip(), justify="left")

            # 网络信息
            try:
                hostname = socket.gethostname()
                self.labels['hostname'].configure(text=hostname)
            except:
                self.labels['hostname'].configure(text="未知")

            try:
                ip = socket.gethostbyname(socket.gethostname())
                self.labels['ip_address'].configure(text=ip)
            except:
                self.labels['ip_address'].configure(text="未知")

            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 8 * 6, 8)][::-1])
                self.labels['mac_address'].configure(text=mac.upper())
            except:
                self.labels['mac_address'].configure(text="未知")

            # 运行时间
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)

                if days > 0:
                    uptime_str = f"{days} 天 {hours} 小时 {minutes} 分钟"
                elif hours > 0:
                    uptime_str = f"{hours} 小时 {minutes} 分钟"
                else:
                    uptime_str = f"{minutes} 分钟"

                self.labels['uptime'].configure(text=uptime_str)
            except:
                self.labels['uptime'].configure(text="未知")

        except Exception as e:
            print(f"刷新系统信息出错: {e}")

    def format_bytes(self, bytes_val):
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"

    def toggle_monitor(self):
        """切换实时监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.monitor_label.configure(text="")
        else:
            self.is_monitoring = True
            self.monitor_label.configure(text="实时监控已开启（每2秒刷新）")
            self.monitor_loop()

    def monitor_loop(self):
        """实时监控循环"""
        if not self.is_monitoring:
            return

        # 只刷新动态数据
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.labels['cpu_usage'].configure(text=f"{cpu_percent}%")

            mem = psutil.virtual_memory()
            self.labels['mem_used'].configure(text=self.format_bytes(mem.used))
            self.labels['mem_available'].configure(text=self.format_bytes(mem.available))
            self.labels['mem_percent'].configure(text=f"{mem.percent}%")
        except:
            pass

        # 2秒后再次刷新
        if self.is_monitoring:
            self.after(2000, self.monitor_loop)
