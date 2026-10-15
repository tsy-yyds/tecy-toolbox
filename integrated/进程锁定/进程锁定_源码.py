import os
import sys
import time
import psutil
import threading
import json
import random
import platform
import math  # 确保导入math模块
from tkinter import (Tk, Frame, Listbox, Scrollbar, Button, Label, Entry,
                     Checkbutton, IntVar, Toplevel, messagebox, Menu, StringVar,
                     Canvas)
from tkinter.ttk import Treeview, Style, Progressbar
import tkinter as tk

class ProcessLocker:
    def __init__(self, root):
        self.root = root
        self.root.title("进程锁定器")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # 设置中文字体
        self.style = Style()
        self.style.configure("Treeview.Heading", font=("SimHei", 10, "bold"))
        self.style.configure("Treeview", font=("SimHei", 9))
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TLabel", font=("SimHei", 10))
        
        # 锁定的进程列表
        self.locked_processes = {}  # {pid: (name, path, args)}
        self.locked_pids = set()
        
        # 配置文件路径
        self.config_file = "process_locker_config.json"
        self.config = self.load_config()
        
        # 动画相关变量
        self.animation_running = False
        
        # 创建UI
        self.create_widgets()
        
        # 刷新进程列表
        self.refresh_processes()
        
        # 启动监控线程
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_locked_processes, daemon=True)
        self.monitor_thread.start()
        
        # 启动自动刷新计时器
        self.start_auto_refresh()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧进程列表区域
        left_frame = Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 搜索框和控制按钮
        top_control_frame = Frame(left_frame)
        top_control_frame.pack(fill="x", pady=(0, 5))
        
        # 搜索框
        search_frame = Frame(top_control_frame)
        search_frame.pack(side="left", fill="x", expand=True)
        
        Label(search_frame, text="搜索进程:", font=("SimHei", 10)).pack(side="left", padx=(0, 5))
        self.search_var = StringVar()
        self.search_var.trace_add("write", self.on_search_changed)
        Entry(search_frame, textvariable=self.search_var, font=("SimHei", 10)).pack(side="left", fill="x", expand=True)
        
        # 进程列表
        self.process_tree = Treeview(left_frame, columns=("pid", "name", "status", "cpu", "memory"), show="headings")
        self.process_tree.heading("pid", text="进程ID")
        self.process_tree.heading("name", text="进程名称")
        self.process_tree.heading("status", text="状态")
        self.process_tree.heading("cpu", text="CPU使用率(%)")
        self.process_tree.heading("memory", text="内存使用(MB)")
        
        self.process_tree.column("pid", width=80, anchor="center")
        self.process_tree.column("name", width=200)
        self.process_tree.column("status", width=80, anchor="center")
        self.process_tree.column("cpu", width=100, anchor="center")
        self.process_tree.column("memory", width=100, anchor="center")
        
        # 添加滚动条
        scrollbar = Scrollbar(left_frame, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        self.process_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 右侧操作区域
        right_frame = Frame(main_frame, width=200)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 炫酷标题
        title_canvas = Canvas(right_frame, height=60, bg="#f0f0f0", highlightthickness=0)
        title_canvas.pack(fill="x", pady=(0, 20))
        title_canvas.create_text(100, 30, text="进程控制中心", font=("SimHei", 12, "bold"), fill="#333333")
        
        # 操作按钮，添加悬停效果
        self.create_hover_button(right_frame, "锁定进程", self.lock_selected_process, "#4CAF50", "#45a049")
        self.create_hover_button(right_frame, "解锁进程", self.unlock_selected_process, "#2196F3", "#0b7dda")
        self.create_hover_button(right_frame, "刷新列表", self.refresh_processes, "#ff9800", "#e68a00")
        self.create_hover_button(right_frame, "强制结束", self.terminate_selected_process, "#f44336", "#d32f2f")
        self.create_hover_button(right_frame, "设置", self.open_settings, "#9c27b0", "#7b1fa2")
        
        # 锁定的进程列表
        Label(right_frame, text="已锁定的进程", font=("SimHei", 10, "bold")).pack(anchor="w", padx=5, pady=(20, 5))
        
        self.locked_frame = Frame(right_frame)
        self.locked_frame.pack(fill="both", expand=True, padx=5)
        
        self.locked_listbox = Listbox(self.locked_frame, font=("SimHei", 9), selectbackground="#a6a6a6")
        locked_scrollbar = Scrollbar(self.locked_frame, orient="vertical", command=self.locked_listbox.yview)
        self.locked_listbox.configure(yscrollcommand=locked_scrollbar.set)
        
        self.locked_listbox.pack(side="left", fill="both", expand=True)
        locked_scrollbar.pack(side="right", fill="y")
        
        # 状态栏
        self.status_var = StringVar(value="就绪")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w", font=("SimHei", 9))
        status_bar.pack(side="bottom", fill="x")
        
        # 添加双击事件
        self.process_tree.bind("<Double-1>", lambda e: self.lock_selected_process())
        self.locked_listbox.bind("<Double-1>", lambda e: self.unlock_selected_process())
    
    def create_hover_button(self, parent, text, command, normal_bg, hover_bg):
        """创建带有悬停效果的按钮"""
        btn = Button(parent, text=text, command=command, height=2, font=("SimHei", 10),
                    bg=normal_bg, fg="white", relief="flat", bd=0)
        btn.pack(fill="x", pady=(0, 10), padx=5)
        
        # 绑定悬停事件
        def on_enter(e):
            btn['background'] = hover_bg

        def on_leave(e):
            btn['background'] = normal_bg

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = Menu(self.root, font=("SimHei", 10))
        
        # 文件菜单
        file_menu = Menu(menubar, tearoff=0, font=("SimHei", 10))
        file_menu.add_command(label="导出进程列表", command=self.export_process_list)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 工具菜单
        tool_menu = Menu(menubar, tearoff=0, font=("SimHei", 10))
        tool_menu.add_command(label="系统信息", command=self.show_system_info)
        tool_menu.add_command(label="进程统计", command=self.show_process_stats)
        menubar.add_cascade(label="工具", menu=tool_menu)
        
        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0, font=("SimHei", 10))
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="使用帮助", command=self.show_help)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def refresh_processes(self):
        """刷新进程列表"""
        # 添加刷新动画效果
        self.status_var.set("正在刷新进程列表...")
        
        # 清空现有列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # 获取所有进程并添加到列表
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    status = proc.info['status']
                    cpu = proc.info['cpu_percent'] or 0
                    memory = proc.info['memory_info'].rss / (1024 * 1024)  # 转换为MB
                    
                    # 搜索过滤
                    search_text = self.search_var.get().lower()
                    if search_text and search_text not in name.lower() and str(pid) != search_text:
                        continue
                    
                    # 状态显示为中文
                    status_cn = self.status_to_chinese(status)
                    
                    # 检查是否为锁定进程
                    tags = ("locked",) if pid in self.locked_pids else ()
                    
                    self.process_tree.insert("", "end", values=(
                        pid, 
                        name, 
                        status_cn, 
                        f"{cpu:.1f}", 
                        f"{memory:.1f}"
                    ), tags=tags)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # 设置锁定进程的样式
            self.process_tree.tag_configure("locked", background="#c1e1c1")
            
            self.status_var.set(f"已刷新进程列表，共 {len(self.process_tree.get_children())} 个进程")
        except Exception as e:
            self.status_var.set(f"刷新进程列表失败: {str(e)}")
    
    def status_to_chinese(self, status):
        """将进程状态转换为中文"""
        status_map = {
            'running': '运行中',
            'sleeping': '休眠',
            'disk-sleep': '磁盘休眠',
            'stopped': '已停止',
            'tracing-stop': '跟踪停止',
            'zombie': '僵尸',
            'dead': '已死亡',
            'idle': '空闲',
            'locked': '已锁定',
            'waiting': '等待中'
        }
        return status_map.get(status, status)
    
    def lock_selected_process(self):
        """锁定选中的进程"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个进程")
            return
        
        # 添加锁定动画
        self.start_animation("lock")
        
        for item in selected_items:
            values = self.process_tree.item(item, "values")
            pid = int(values[0])
            name = values[1]
            
            if pid in self.locked_pids:
                messagebox.showinfo("提示", f"进程 {name} (PID: {pid}) 已被锁定")
                continue
            
            try:
                # 获取进程路径和命令行参数
                proc = psutil.Process(pid)
                path = proc.exe()
                args = proc.cmdline()
                
                # 添加到锁定列表
                self.locked_processes[pid] = {
                    'name': name,
                    'path': path,
                    'args': args
                }
                self.locked_pids.add(pid)
                
                # 更新锁定列表显示
                self.update_locked_listbox()
                
                self.status_var.set(f"已锁定进程: {name} (PID: {pid})")
                messagebox.showinfo("成功", f"进程 {name} (PID: {pid}) 已被锁定")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                messagebox.showerror("错误", f"无法锁定进程 {name} (PID: {pid})，权限不足或进程已结束")
            except Exception as e:
                messagebox.showerror("错误", f"锁定进程失败: {str(e)}")
        
        # 停止动画并刷新进程列表
        self.stop_animation()
        self.refresh_processes()
        # 保存配置
        self.save_config()
    
    def unlock_selected_process(self):
        """解锁选中的进程"""
        selected_indices = self.locked_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请先从已锁定列表中选择一个进程")
            return
        
        # 添加解锁动画
        self.start_animation("unlock")
        
        # 获取选中的进程信息
        selected_text = self.locked_listbox.get(selected_indices[0])
        # 从文本中提取PID (格式如 "进程名 (PID: 1234)")
        try:
            pid = int(selected_text.split("PID: ")[1].rstrip(")"))
            
            if pid in self.locked_pids:
                # 从锁定列表中移除
                del self.locked_processes[pid]
                self.locked_pids.remove(pid)
                
                # 更新锁定列表显示
                self.update_locked_listbox()
                
                self.status_var.set(f"已解锁进程: {selected_text}")
                messagebox.showinfo("成功", f"进程 {selected_text} 已被解锁")
            else:
                messagebox.showinfo("提示", "选中的进程未被锁定")
        except (IndexError, ValueError):
            messagebox.showerror("错误", "无法解析进程信息")
        
        # 停止动画并刷新进程列表
        self.stop_animation()
        self.refresh_processes()
        # 保存配置
        self.save_config()
    
    def terminate_selected_process(self):
        """强制结束选中的进程"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个进程")
            return
        
        values = self.process_tree.item(selected_items[0], "values")
        pid = int(values[0])
        name = values[1]
        
        # 检查是否为锁定的进程
        if pid in self.locked_pids:
            if not messagebox.askyesno("警告", f"进程 {name} (PID: {pid}) 已被锁定，确定要结束它吗？它会被自动重启。"):
                return
        
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            self.status_var.set(f"已尝试结束进程: {name} (PID: {pid})")
            messagebox.showinfo("成功", f"已向进程 {name} (PID: {pid}) 发送结束信号")
            
            # 刷新进程列表
            self.refresh_processes()
        except psutil.NoSuchProcess:
            messagebox.showerror("错误", f"进程 {name} (PID: {pid}) 不存在")
        except psutil.AccessDenied:
            messagebox.showerror("错误", f"没有权限结束进程 {name} (PID: {pid})")
        except Exception as e:
            messagebox.showerror("错误", f"结束进程失败: {str(e)}")
    
    def update_locked_listbox(self):
        """更新锁定进程列表显示"""
        self.locked_listbox.delete(0, "end")
        for pid, info in self.locked_processes.items():
            self.locked_listbox.insert("end", f"{info['name']} (PID: {pid})")
    
    def monitor_locked_processes(self):
        """监控锁定的进程，确保它们持续运行"""
        while self.monitoring:
            # 复制一份锁定的进程列表，避免在迭代时修改
            processes_to_check = list(self.locked_processes.items())
            
            for pid, info in processes_to_check:
                # 检查进程是否仍然存在
                try:
                    # 尝试获取进程信息，如果进程不存在会抛出异常
                    psutil.Process(pid)
                    # 进程存在，继续监控
                    continue
                except psutil.NoSuchProcess:
                    # 进程已结束，需要重启
                    self.status_var.set(f"进程 {info['name']} (PID: {pid}) 已结束，正在重启...")
                    
                    try:
                        # 重启进程
                        if platform.system() == "Windows":
                            # Windows系统
                            new_proc = psutil.Popen(info['args'] if info['args'] else [info['path']])
                        else:
                            # 其他系统 (Linux, macOS等)
                            new_proc = psutil.Popen(info['args'] if info['args'] else [info['path']])
                        
                        new_pid = new_proc.pid
                        
                        # 更新锁定进程的PID
                        del self.locked_processes[pid]
                        self.locked_pids.remove(pid)
                        
                        self.locked_processes[new_pid] = {
                            'name': info['name'],
                            'path': info['path'],
                            'args': info['args']
                        }
                        self.locked_pids.add(new_pid)
                        
                        # 在主线程中更新UI
                        self.root.after(0, self.update_locked_listbox)
                        self.root.after(0, self.refresh_processes)
                        
                        self.status_var.set(f"进程 {info['name']} 已重启 (新PID: {new_pid})")
                        # 保存配置
                        self.save_config()
                    except Exception as e:
                        error_msg = f"重启进程 {info['name']} 失败: {str(e)}"
                        self.status_var.set(error_msg)
                        # 在主线程中显示错误消息
                        self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
            
            # 每N秒检查一次，从配置中获取
            time.sleep(self.config.get('monitor_interval', 2))
    
    def on_search_changed(self, *args):
        """搜索文本变化时刷新进程列表"""
        self.refresh_processes()
    
    def start_auto_refresh(self):
        """启动自动刷新计时器"""
        if self.config.get('auto_refresh', 1):
            interval = self.config.get('auto_refresh_interval', 10) * 1000  # 转换为毫秒
            self.root.after(interval, self.auto_refresh_callback)
    
    def auto_refresh_callback(self):
        """自动刷新回调函数"""
        if self.monitoring and self.config.get('auto_refresh', 1):
            self.refresh_processes()
            self.start_auto_refresh()
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x350")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 标题
        Label(settings_window, text="应用设置", font=("SimHei", 12, "bold")).pack(pady=10)
        
        # 监控间隔设置
        Frame(settings_window).pack(fill="x", pady=5)
        Label(settings_window, text="进程监控间隔 (秒):", font=("SimHei", 10)).pack(anchor="w", padx=20)
        
        monitor_frame = Frame(settings_window)
        monitor_frame.pack(fill="x", padx=20, pady=5)
        
        self.monitor_interval_var = IntVar(value=self.config.get('monitor_interval', 2))
        Entry(monitor_frame, textvariable=self.monitor_interval_var, width=10, font=("SimHei", 10)).pack(side="left")
        Label(monitor_frame, text="秒 (建议2-10秒)").pack(side="left", padx=5)
        
        # 启动时自动锁定上次锁定的进程
        Frame(settings_window).pack(fill="x", pady=5)
        self.auto_lock_on_start_var = IntVar(value=self.config.get('auto_lock_on_start', 1))
        Checkbutton(settings_window, text="启动时自动锁定上次锁定的进程", 
                   variable=self.auto_lock_on_start_var, font=("SimHei", 10)).pack(anchor="w", padx=20)
        
        # 自动刷新进程列表
        Frame(settings_window).pack(fill="x", pady=5)
        self.auto_refresh_var = IntVar(value=self.config.get('auto_refresh', 1))
        Checkbutton(settings_window, text="自动刷新进程列表", 
                   variable=self.auto_refresh_var, font=("SimHei", 10)).pack(anchor="w", padx=20)
        
        # 自动刷新间隔
        auto_refresh_frame = Frame(settings_window)
        auto_refresh_frame.pack(fill="x", padx=40, pady=5)
        
        self.auto_refresh_interval_var = IntVar(value=self.config.get('auto_refresh_interval', 10))
        Entry(auto_refresh_frame, textvariable=self.auto_refresh_interval_var, width=10, font=("SimHei", 10)).pack(side="left")
        Label(auto_refresh_frame, text="秒 (建议5-30秒)").pack(side="left", padx=5)
        
        # 启用动画效果
        Frame(settings_window).pack(fill="x", pady=5)
        self.enable_animations_var = IntVar(value=self.config.get('enable_animations', 1))
        Checkbutton(settings_window, text="启用动画效果", 
                   variable=self.enable_animations_var, font=("SimHei", 10)).pack(anchor="w", padx=20)
        
        # 保存按钮
        Button(settings_window, text="保存设置", command=lambda: self.save_settings(settings_window),
              font=("SimHei", 10), bg="#4CAF50", fg="white", relief="flat").pack(pady=20)
    
    def save_settings(self, settings_window):
        """保存设置"""
        monitor_interval = self.monitor_interval_var.get()
        auto_lock_on_start = self.auto_lock_on_start_var.get()
        auto_refresh = self.auto_refresh_var.get()
        auto_refresh_interval = self.auto_refresh_interval_var.get()
        enable_animations = self.enable_animations_var.get()
        
        # 验证输入
        if monitor_interval < 1 or monitor_interval > 60:
            messagebox.showerror("错误", "监控间隔应在1-60秒之间")
            return
        
        if auto_refresh_interval < 1 or auto_refresh_interval > 300:
            messagebox.showerror("错误", "自动刷新间隔应在1-300秒之间")
            return
        
        # 更新配置
        self.config['monitor_interval'] = monitor_interval
        self.config['auto_lock_on_start'] = auto_lock_on_start
        self.config['auto_refresh'] = auto_refresh
        self.config['auto_refresh_interval'] = auto_refresh_interval
        self.config['enable_animations'] = enable_animations
        
        # 保存配置
        self.save_config()
        
        messagebox.showinfo("成功", "设置已保存")
        settings_window.destroy()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            'monitor_interval': 2,
            'auto_lock_on_start': 1,
            'auto_refresh': 1,
            'auto_refresh_interval': 10,
            'enable_animations': 1,
            'locked_processes': {}
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 确保所有配置项都存在
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                # 如果设置了启动时自动锁定，则加载上次锁定的进程
                if config.get('auto_lock_on_start', 1):
                    saved_locked = config.get('locked_processes', {})
                    for pid_str, info in saved_locked.items():
                        try:
                            pid = int(pid_str)
                            self.locked_processes[pid] = info
                            self.locked_pids.add(pid)
                        except ValueError:
                            continue
                return config
            else:
                return default_config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 保存当前锁定的进程
            self.config['locked_processes'] = {str(pid): info for pid, info in self.locked_processes.items()}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            self.status_var.set(f"保存配置失败: {str(e)}")
    
    def export_process_list(self):
        """导出进程列表到文件"""
        try:
            filename = f"process_list_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"进程列表 - 导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{'PID':<10} {'名称':<30} {'状态':<10} {'CPU(%)':<10} {'内存(MB)':<10} {'锁定状态'}\n")
                f.write("-" * 80 + "\n")
                
                for item in self.process_tree.get_children():
                    values = self.process_tree.item(item, "values")
                    pid, name, status, cpu, memory = values
                    locked = "已锁定" if int(pid) in self.locked_pids else "未锁定"
                    
                    # 处理长名称
                    if len(name) > 30:
                        name = name[:27] + "..."
                    
                    f.write(f"{pid:<10} {name:<30} {status:<10} {cpu:<10} {memory:<10} {locked}\n")
            
            self.status_var.set(f"进程列表已导出到 {filename}")
            messagebox.showinfo("成功", f"进程列表已导出到 {filename}")
        except Exception as e:
            self.status_var.set(f"导出进程列表失败: {str(e)}")
            messagebox.showerror("错误", f"导出进程列表失败: {str(e)}")
    
    def show_system_info(self):
        """显示系统信息"""
        sys_info_window = Toplevel(self.root)
        sys_info_window.title("系统信息")
        sys_info_window.geometry("400x300")
        sys_info_window.transient(self.root)
        
        # 创建带滚动条的文本框
        frame = Frame(sys_info_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap="word", font=("SimHei", 10))
        scrollbar = Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 收集系统信息
        info = []
        info.append(f"系统: {platform.system()} {platform.release()} {platform.version()}")
        info.append(f"处理器: {platform.processor()}")
        info.append(f"架构: {platform.machine()}")
        info.append(f"Python版本: {platform.python_version()}")
        
        # 内存信息
        mem = psutil.virtual_memory()
        total_mem = mem.total / (1024 **3)
        available_mem = mem.available / (1024** 3)
        used_mem = mem.used / (1024 **3)
        info.append("\n内存信息:")
        info.append(f"  总内存: {total_mem:.2f} GB")
        info.append(f"  可用内存: {available_mem:.2f} GB")
        info.append(f"  已使用: {used_mem:.2f} GB ({mem.percent}%)")
        
        # CPU信息
        info.append("\nCPU信息:")
        info.append(f"  逻辑核心数: {psutil.cpu_count(logical=True)}")
        info.append(f"  物理核心数: {psutil.cpu_count(logical=False) or '未知'}")
        info.append(f"  当前使用率: {psutil.cpu_percent(interval=1)}%")
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        total_disk = disk.total / (1024 **3)
        used_disk = disk.used / (1024** 3)
        free_disk = disk.free / (1024 **3)
        info.append("\n磁盘信息:")
        info.append(f"  总容量: {total_disk:.2f} GB")
        info.append(f"  已使用: {used_disk:.2f} GB ({disk.percent}%)")
        info.append(f"  可用空间: {free_disk:.2f} GB")
        
        # 添加到文本框
        text_widget.insert("1.0", "\n".join(info))
        text_widget.config(state="disabled")  # 设置为只读
        
        Button(sys_info_window, text="确定", command=sys_info_window.destroy,
              font=("SimHei", 10)).pack(pady=10)
    
    def show_process_stats(self):
        """显示进程统计信息"""
        stats_window = Toplevel(self.root)
        stats_window.title("进程统计")
        stats_window.geometry("400x300")
        stats_window.transient(self.root)
        
        # 创建统计信息
        total_processes = len(self.process_tree.get_children())
        locked_count = len(self.locked_processes)
        
        # 获取资源占用最高的进程
        top_cpu = None
        top_memory = None
        for item in self.process_tree.get_children():
            values = self.process_tree.item(item, "values")
            pid, name, status, cpu, memory = values
            cpu_val = float(cpu)
            mem_val = float(memory)
            
            if not top_cpu or cpu_val > float(top_cpu[3]):
                top_cpu = (pid, name, status, cpu, memory)
            
            if not top_memory or mem_val > float(top_memory[4]):
                top_memory = (pid, name, status, cpu, memory)
        
        # 创建统计显示
        frame = Frame(stats_window)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        Label(frame, text="进程统计信息", font=("SimHei", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        Label(frame, text="总进程数:", font=("SimHei", 10)).grid(row=1, column=0, sticky="w", pady=5)
        Label(frame, text=str(total_processes), font=("SimHei", 10)).grid(row=1, column=1, sticky="w", pady=5)
        
        Label(frame, text="已锁定进程数:", font=("SimHei", 10)).grid(row=2, column=0, sticky="w", pady=5)
        Label(frame, text=str(locked_count), font=("SimHei", 10)).grid(row=2, column=1, sticky="w", pady=5)
        
        Label(frame, text="CPU使用率最高:", font=("SimHei", 10)).grid(row=3, column=0, sticky="w", pady=5)
        if top_cpu:
            Label(frame, text=f"{top_cpu[1]} ({top_cpu[3]}%)", font=("SimHei", 10)).grid(row=3, column=1, sticky="w", pady=5)
        
        Label(frame, text="内存使用率最高:", font=("SimHei", 10)).grid(row=4, column=0, sticky="w", pady=5)
        if top_memory:
            Label(frame, text=f"{top_memory[1]} ({top_memory[4]}MB)", font=("SimHei", 10)).grid(row=4, column=1, sticky="w", pady=5)
        
        # 添加炫酷进度条展示CPU和内存使用情况
        Label(frame, text="系统CPU使用率:", font=("SimHei", 10)).grid(row=5, column=0, sticky="w", pady=5)
        cpu_frame = Frame(frame)
        cpu_frame.grid(row=5, column=1, sticky="w", pady=5)
        cpu_percent = psutil.cpu_percent(interval=1)
        Progressbar(cpu_frame, orient="horizontal", length=150, mode="determinate", value=cpu_percent).pack(side="left")
        Label(cpu_frame, text=f"{cpu_percent}%", font=("SimHei", 9), width=5).pack(side="left", padx=5)
        
        Label(frame, text="系统内存使用率:", font=("SimHei", 10)).grid(row=6, column=0, sticky="w", pady=5)
        mem_frame = Frame(frame)
        mem_frame.grid(row=6, column=1, sticky="w", pady=5)
        mem_percent = psutil.virtual_memory().percent
        Progressbar(mem_frame, orient="horizontal", length=150, mode="determinate", value=mem_percent).pack(side="left")
        Label(mem_frame, text=f"{mem_percent}%", font=("SimHei", 9), width=5).pack(side="left", padx=5)
        
        Button(stats_window, text="刷新", command=self.show_process_stats,
              font=("SimHei", 10)).pack(side="left", padx=20, pady=20)
        Button(stats_window, text="关闭", command=stats_window.destroy,
              font=("SimHei", 10)).pack(side="right", padx=20, pady=20)
    
    def show_about(self):
        """显示关于对话框"""
        about_window = Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("300x200")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        Label(about_window, text="进程锁定器", font=("SimHei", 16, "bold")).pack(pady=10)
        Label(about_window, text="版本: 1.0.0", font=("SimHei", 10)).pack()
        Label(about_window, text="一个用于锁定重要进程的工具", font=("SimHei", 10)).pack(pady=5)
        Label(about_window, text="确保被锁定的进程不会意外关闭", font=("SimHei", 10)).pack()
        Label(about_window, text="进程关闭后会自动重新启动", font=("SimHei", 10)).pack(pady=5)
        
        Button(about_window, text="确定", command=about_window.destroy,
              font=("SimHei", 10)).pack(pady=10)
    
    def show_help(self):
        """显示帮助对话框"""
        help_window = Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("500x400")
        help_window.transient(self.root)
        
        # 创建带滚动条的文本框
        frame = Frame(help_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap="word", font=("SimHei", 10))
        scrollbar = Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加帮助内容
        help_text = """
进程锁定器使用帮助:

1. 进程列表:
   - 左侧显示系统中所有正在运行的进程
   - 可以通过搜索框筛选进程
   - 已锁定的进程会以绿色背景显示

2. 锁定进程:
   - 在进程列表中选择一个进程
   - 点击"锁定进程"按钮或双击进程
   - 被锁定的进程会显示在右侧"已锁定的进程"列表中

3. 解锁进程:
   - 在右侧"已锁定的进程"列表中选择一个进程
   - 点击"解锁进程"按钮或双击进程

4. 其他功能:
   - 点击"刷新列表"按钮可以手动刷新进程列表
   - "强制结束"按钮可以结束选中的进程
   - "设置"按钮可以配置监控间隔等参数
   - "导出进程列表"可以将当前进程信息保存到文件

注意事项:
- 某些系统进程可能无法锁定，因为需要管理员权限
- 锁定过多进程可能会影响系统性能
- 进程锁定后，即使被关闭也会自动重新启动
        """
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")  # 设置为只读
        
        Button(help_window, text="确定", command=help_window.destroy,
              font=("SimHei", 10)).pack(pady=10)
    
    def start_animation(self, animation_type):
        """启动动画效果 - 修改了背景色设置"""
        if not self.config.get('enable_animations', 1) or self.animation_running:
            return
            
        self.animation_running = True
        self.animation_type = animation_type
        
        # 根据操作系统选择合适的透明背景方式
        if platform.system() == "Windows":
            # Windows使用系统按钮颜色作为背景，接近透明效果
            self.animation_canvas = Canvas(self.root, width=50, height=50, highlightthickness=0, bg=self.root.cget("bg"))
        else:
            # 其他系统尝试使用透明色
            try:
                self.animation_canvas = Canvas(self.root, width=50, height=50, highlightthickness=0, bg="systemTransparent")
            except:
                self.animation_canvas = Canvas(self.root, width=50, height=50, highlightthickness=0, bg=self.root.cget("bg"))
                
        self.animation_canvas.place(relx=0.5, rely=0.5, anchor="center")
        
        if animation_type == "lock":
            self.animate_lock()
        elif animation_type == "unlock":
            self.animate_unlock()
    
    def animate_lock(self):
        """锁定动画"""
        if not self.animation_running:
            return
            
        size = 30
        self.animation_canvas.delete("all")
        
        # 绘制锁的形状
        for i in range(10):
            angle = i * 36
            x = 25 + size * 0.4 * math.cos(math.radians(angle))
            y = 25 + size * 0.4 * math.sin(math.radians(angle))
            self.animation_canvas.create_oval(x-2, y-2, x+2, y+2, fill="#4CAF50")
        
        self.root.after(100, self.animate_lock)
    
    def animate_unlock(self):
        """解锁动画"""
        if not self.animation_running:
            return
            
        size = 30
        self.animation_canvas.delete("all")
        
        # 绘制解锁的形状
        for i in range(10):
            angle = 180 + i * 36
            x = 25 + size * 0.4 * math.cos(math.radians(angle))
            y = 25 + size * 0.4 * math.sin(math.radians(angle))
            self.animation_canvas.create_oval(x-2, y-2, x+2, y+2, fill="#f44336")
        
        self.root.after(100, self.animate_unlock)
    
    def stop_animation(self):
        """停止动画效果"""
        if self.animation_running and hasattr(self, 'animation_canvas'):
            self.animation_running = False
            self.animation_canvas.destroy()
    
    def on_close(self):
        """窗口关闭事件处理"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    # 确保中文正常显示（matplotlib 无实际用途，已精简移除）
    
    # 检查是否以管理员权限运行（Windows）
    if platform.system() == "Windows":
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                messagebox.showwarning("警告", "建议以管理员权限运行，否则可能无法锁定某些系统进程")
        except Exception:
            pass
    
    root = Tk()
    app = ProcessLocker(root)
    root.mainloop()