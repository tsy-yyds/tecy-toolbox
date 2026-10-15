# -*- coding: utf-8 -*-
"""
腾讯进程管家 - 整合自 TxConfig「关闭Tencent所有进程 v12.0.bat」核心逻辑
功能：清除腾讯进程（含服务）、扫描全部进程、进程保护（自动重启）、白名单管理、检查间隔设置
本模块为 CustomTkinter 同进程页面，不依赖原 bat 文件。
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import psutil
import subprocess
import threading
import time
import os
import json
import sys
from pathlib import Path

# 核心腾讯进程库（与原 bat 保持一致）
TENCENT_PROCESSES = [
    "QQ.exe", "TIM.exe", "WeChat.exe", "QQMusic.exe", "TencentMeeting.exe",
    "WXWork.exe", "QQBrowser.exe", "TencentDocs.exe", "START.exe", "ACE-Guard.exe",
    "QQLive.exe", "QQGAME.exe", "WeGame.exe", "QQPlayer.exe", "QQPinyin.exe",
    "QQProtect.exe", "TXGuiFoundation.exe",
]
TENCENT_SERVICES = [
    "QQProtectService", "BaradAgent", "SGAgent", "YDService", "WeChatService",
]

RESERVED_PROCESSES = ["explorer.exe", "dwm.exe", "csrss.exe", "wininit.exe",
                      "lsass.exe", "services.exe", "svchost.exe", "winlogon.exe",
                      "smss.exe", "System", "system", "Registry", "Memory Compression"]


def _is_admin():
    """检测当前是否以管理员权限运行"""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class TencentProcessManagerFrame(ctk.CTkFrame):
    """腾讯进程管家 - CustomTkinter 页面"""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / "tencent_manager_config.json"

        # 配置：白名单 / 检查间隔
        self.config = self.load_config()
        self.check_interval = float(self.config.get("check_interval", 0.2))
        self.whitelist = [x.strip() for x in str(self.config.get("whitelist", "WeChat.exe")).split(",") if x.strip()]

        # 保护列表： [{ "name": ..., "path": ... }]
        self.protected = self.config.get("protected", [])
        for item in self.protected:
            item.setdefault("path", "")

        # 后台线程状态
        self.protect_thread = None
        self.protect_running = False

        self.process_cache = []
        self._build_ui()
        self._refresh_process_list()

    # ---------------- 配置存取 ----------------
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        data = {
            "check_interval": str(self.check_interval),
            "whitelist": ",".join(self.whitelist),
            "protected": self.protected,
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"配置保存失败：{e}")

    # ---------------- UI ----------------
    def _build_ui(self):
        # 标题
        title = ctk.CTkLabel(self, text="腾讯进程管家", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(5, 8))

        tip = ctk.CTkLabel(self, text="整合自 TxConfig v12.0（关闭Tencent所有进程）核心逻辑",
                           font=ctk.CTkFont(size=12), text_color="#888888")
        tip.pack(pady=(0, 8))

        # 顶部操作按钮行
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(btn_row, text="清理腾讯进程与相关服务", width=200,
                      fg_color="#C0392B", hover_color="#E74C3C",
                      command=self._confirm_kill_tencent).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="刷新进程列表", width=120,
                      command=self._refresh_process_list).pack(side="left", padx=4)

        self.protect_btn = ctk.CTkButton(
            btn_row, text="开始保护所选进程", width=160,
            command=self._toggle_protect)
        self.protect_btn.pack(side="left", padx=4)

        self.status_label = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="right", padx=8)

        # 中部：进程列表 + 右侧面板
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        # 左侧进程列表（Treeview 内嵌于 CTkFrame）
        left = ctk.CTkFrame(mid, corner_radius=8)
        left.pack(side="left", fill="both", expand=True)

        search_row = ctk.CTkFrame(left, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(search_row, text="筛选：", font=ctk.CTkFont(size=12)).pack(side="left")
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="输入进程名过滤...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_process_list())

        tree_frame = ctk.CTkFrame(left, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(tree_frame, columns=("pid", "name", "path"),
                                 show="headings", selectmode="extended")
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="进程名")
        self.tree.heading("path", text="路径")
        self.tree.column("pid", width=70, anchor="center", stretch=False)
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("path", width=320, anchor="w")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # 右侧：白名单 / 保护列表 / 检查间隔
        right = ctk.CTkFrame(mid, width=250, corner_radius=8)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        # 白名单
        ctk.CTkLabel(right, text="白名单（清理时保护）", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self.whitelist_box = ctk.CTkTextbox(right, height=90, font=("Consolas", 11))
        self.whitelist_box.pack(fill="x", padx=10)
        self._update_whitelist_box()

        wl_row = ctk.CTkFrame(right, fg_color="transparent")
        wl_row.pack(fill="x", padx=10, pady=4)
        self.wl_entry = ctk.CTkEntry(wl_row, placeholder_text="进程名 如 QQ.exe")
        self.wl_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(wl_row, text="添加", width=52, command=self._add_whitelist).pack(side="left")
        ctk.CTkButton(right, text="移除白名单选中项", command=self._remove_whitelist).pack(fill="x", padx=10, pady=2)

        # 保护列表
        ctk.CTkLabel(right, text="保护列表（自动重启）", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self.protect_box = ctk.CTkTextbox(right, height=90, font=("Consolas", 11))
        self.protect_box.pack(fill="x", padx=10)
        self._update_protect_box()

        ctk.CTkButton(right, text="将选中进程加入保护", command=self._add_protected).pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(right, text="移除选中保护项", fg_color="#666666", hover_color="#888888",
                      command=self._remove_protected).pack(fill="x", padx=10, pady=2)

        # 检查间隔
        ctk.CTkLabel(right, text="检查间隔（秒）", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        iv_row = ctk.CTkFrame(right, fg_color="transparent")
        iv_row.pack(fill="x", padx=10, pady=2)
        self.interval_entry = ctk.CTkEntry(iv_row, width=80)
        self.interval_entry.insert(0, str(self.check_interval))
        self.interval_entry.pack(side="left")
        ctk.CTkButton(iv_row, text="保存", width=60, command=self._save_interval).pack(side="left", padx=(6, 0))

        # 底部日志
        log_frame = ctk.CTkFrame(self, corner_radius=8)
        log_frame.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(log_frame, text="运行日志", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self.log_box = ctk.CTkTextbox(log_frame, height=100, font=("Consolas", 10))
        self.log_box.pack(fill="x", padx=10, pady=(0, 8))

        self._log("腾讯进程管家已就绪")
        self._log(f"白名单：{'、'.join(self.whitelist)}")
        self._log(f"检查间隔：{self.check_interval} 秒 | 管理员权限：{'是' if _is_admin() else '否'}")

    def _update_whitelist_box(self):
        self.whitelist_box.delete("1.0", "end")
        self.whitelist_box.insert("1.0", "\n".join(self.whitelist) if self.whitelist else "（空）")

    def _update_protect_box(self):
        self.protect_box.delete("1.0", "end")
        lines = [f"{i['name']}  ->  {i.get('path') or '未知路径'}" for i in self.protected]
        self.protect_box.insert("1.0", "\n".join(lines) if lines else "（空）")

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")

    # ---------------- 进程列表 ----------------
    def _refresh_process_list(self):
        kw = self.search_entry.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.process_cache = []
        try:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    pinfo = proc.info
                    name = str(pinfo.get("name") or "")
                    pid = pinfo.get("pid")
                    exe = str(pinfo.get("exe") or "")
                    if kw and kw not in name.lower() and kw not in exe.lower():
                        continue
                    self.process_cache.append({"pid": pid, "name": name, "path": exe})
                    self.tree.insert("", "end", values=(pid, name, exe[:80]))
                except Exception:
                    continue
        except Exception as e:
            self._log(f"刷新进程列表失败：{e}")

    def _selected_rows(self):
        rows = []
        for item in self.tree.selection():
            vals = self.tree.item(item, "values")
            if vals:
                rows.append({"pid": vals[0], "name": vals[1], "path": vals[2] if len(vals) > 2 else ""})
        return rows

    # ---------------- 清理腾讯进程 ----------------
    def _confirm_kill_tencent(self):
        if not _is_admin():
            messagebox.showwarning("权限不足", "清理腾讯进程/服务需要【管理员权限】。\n请右键以管理员身份运行本程序后重试。")
            return
        ok = messagebox.askokcancel(
            "确认清理",
            f"即将终止以下腾讯进程（白名单除外）：\n\n" + "\n".join(TENCENT_PROCESSES) +
            f"\n\n并停止/删除相关服务：\n" + "\n".join(TENCENT_SERVICES) +
            "\n\n请确保已保存所有工作，是否继续？"
        )
        if not ok:
            return
        threading.Thread(target=self._do_kill_tencent, daemon=True).start()

    def _do_kill_tencent(self):
        killed, skipped = [], []
        for pname in TENCENT_PROCESSES:
            if pname.lower() in [w.lower() for w in self.whitelist]:
                skipped.append(pname)
                continue
            try:
                r = subprocess.run(["taskkill", "/f", "/im", pname, "/t"],
                                   capture_output=True, text=True, timeout=30)
                kind = "成功" if r.returncode == 0 else f"未运行({r.returncode})"
                killed.append(f"{pname} - {kind}")
            except Exception as e:
                killed.append(f"{pname} - 错误:{str(e)[:40]}")
        # 服务
        for svc in TENCENT_SERVICES:
            subprocess.run(["net", "stop", svc], capture_output=True, text=True, timeout=30)
            subprocess.run(["sc", "delete", svc], capture_output=True, text=True, timeout=30)

        def report():
            self._log(f"清理结果：共处理 {len(killed)} 个进程/服务")
            for line in killed[-12:]:
                self._log(f"  {line}")
            if skipped:
                self._log(f"白名单跳过：{','.join(skipped)}")
            messagebox.showinfo("清理完成", "腾讯进程与服务清理执行完毕！")

        self.after(0, report)

    # ---------------- 白名单 ----------------
    def _add_whitelist(self):
        name = self.wl_entry.get().strip()
        if not name:
            return
        if not name.lower().endswith(".exe"):
            name = name + ".exe"
        if name.lower() not in [w.lower() for w in self.whitelist]:
            self.whitelist.append(name)
            self.save_config()
            self._update_whitelist_box()
            self._log(f"已添加白名单：{name}")
        else:
            self._log(f"白名单已存在：{name}")
        self.wl_entry.delete(0, "end")

    def _remove_whitelist(self):
        sel = self.whitelist_box.get("1.0", "end").strip()
        if not sel or sel == "（空）":
            messagebox.showinfo("提示", "请先在白名单框中点选要移除的进程名")
            return
        try:
            name = self.whitelist_box.tag_ranges(ctk.SEL)
            sel_text = self.whitelist_box.get(*name).strip()
        except Exception:
            sel_text = None
        if sel_text:
            self.whitelist = [w for w in self.whitelist if w != sel_text]
            self.save_config()
            self._update_whitelist_box()
            self._log(f"已移除白名单：{sel_text}")
        else:
            messagebox.showinfo("提示", "请先选中白名单中的进程名文本")

    # ---------------- 保护列表 ----------------
    def _add_protected(self):
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo("提示", "请先在进程列表中选择要保护的进程")
            return
        for r in rows:
            dup = [p for p in self.protected if p["name"].lower() == r["name"].lower()]
            if not dup:
                self.protected.append({"name": r["name"], "path": r["path"]})
        self.save_config()
        self._update_protect_box()
        self._log(f"已加入保护：{','.join(r['name'] for r in rows)}")

    def _remove_protected(self):
        try:
            ranges = self.protect_box.tag_ranges(ctk.SEL)
            if ranges:
                sel_text = self.protect_box.get(*ranges).strip()
                name = sel_text.split("->")[0].strip()
            else:
                name = None
        except Exception:
            name = None
        if not name:
            messagebox.showinfo("提示", "请先在保护列表中选择要移除的项")
            return
        self.protected = [p for p in self.protected if p["name"].lower() != name.lower()]
        self.save_config()
        self._update_protect_box()
        self._log(f"已移出保护：{name}")

    # ---------------- 检查间隔 ----------------
    def _save_interval(self):
        raw = self.interval_entry.get().strip()
        try:
            val = float(raw)
            if val < 0.01:
                val = 0.01
            self.check_interval = val
            self.save_config()
            self._log(f"检查间隔已更新为 {val} 秒")
            messagebox.showinfo("已保存", f"进程检查间隔已更新为 {val} 秒")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字（秒）")

    # ---------------- 进程保护 ----------------
    def _toggle_protect(self):
        if self.protect_running:
            self.protect_running = False
            self.protect_btn.configure(text="开始保护所选进程", fg_color="#1F6AA5")
            self._log("已停止进程保护监控")
            return
        if not self.protected:
            messagebox.showinfo("提示", "保护列表为空，请先添加要保护的进程")
            return
        self.protect_running = True
        self.protect_btn.configure(text="停止保护监控", fg_color="#C0392B")
        self._log(f"开始保护 {len(self.protected)} 个进程（间隔 {self.check_interval} 秒）")
        self.protect_thread = threading.Thread(target=self._protect_loop, daemon=True)
        self.protect_thread.start()

    def _protect_loop(self):
        fails = 0
        while self.protect_running:
            for item in self.protected:
                if not self.protect_running:
                    break
                name = item.get("name", "")
                path = item.get("path", "")
                if not name:
                    continue
                running = False
                for proc in psutil.process_iter(["name"]):
                    try:
                        if proc.info["name"] and proc.info["name"].lower() == name.lower():
                            running = True
                            break
                    except Exception:
                        pass
                if not running:
                    try:
                        if path and os.path.exists(path):
                            subprocess.Popen([path], close_fds=True)
                        else:
                            subprocess.Popen([name], close_fds=True)
                        self.after(0, lambda n=name: self._log(f"检测到 {n} 已停止，正在重启..."))
                    except Exception as e:
                        fails += 1
                        if fails > 10:
                            self.after(0, lambda: self._log(f"重启多次失败({str(e)[:40]})，请检查路径"))
                            fails = 0
                    time.sleep(0.5)
            time.sleep(self.check_interval)

    def on_close(self):
        """由主程序在窗口关闭时调用，停止保护线程"""
        self.protect_running = False
        try:
            self.save_config()
        except Exception:
            pass
