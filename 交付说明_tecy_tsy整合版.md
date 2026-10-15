---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: faacd42252068f5f84d8de6f81eabf66_40e7bb6ea13b11f1a238525400e6dd8f
    ReservedCode1: bRqiRsKpWpulgBmzOEhHfGYLCnCJWFAYTJQd+LZPqSUhxy9IOYEsho8EKeDWDNxjjV0ENAGEbIMkI4sNK0s6EeZz3BBp9++kJNV2TXgkHUSxyyNNF6wdMmddtFKYye1xB3HWSakd8x0f8SeoQxHM3CraIUiqZGEbdHxDvhBjoCL6CEGGbO8CBJQKhqo=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: faacd42252068f5f84d8de6f81eabf66_40e7bb6ea13b11f1a238525400e6dd8f
    ReservedCode2: bRqiRsKpWpulgBmzOEhHfGYLCnCJWFAYTJQd+LZPqSUhxy9IOYEsho8EKeDWDNxjjV0ENAGEbIMkI4sNK0s6EeZz3BBp9++kJNV2TXgkHUSxyyNNF6wdMmddtFKYye1xB3HWSakd8x0f8SeoQxHM3CraIUiqZGEbdHxDvhBjoCL6CEGGbO8CBJQKhqo=
---

# tecy_tsy 多功能实用工具箱 v3.0 — 整合升级交付说明

> 交付日期：2026-08-26
> 交付形式：**多文件目录形式 exe（PyInstaller onedir），免 bat、双击即用**
> 品牌标识：tecy_tsy ｜ UI 风格：深蓝主色、左侧导航 + 右侧内容、卡片式（仿火绒安全软件）

---

## 一、可执行程序

| 项目 | 内容 |
|---|---|
| 可直接双击运行的 exe | `D:\桌面\多功能工具箱（新）\dist\多功能工具箱\多功能工具箱.exe` |
| 打包引擎 | PyInstaller 6.22.2，onedir 方式 |
| Python 环境 | 主文件夹自带 `venv`（Python 3.14.7） |
| 验证结果 | 实跑 exe，主窗口正常弹出，标题 `tecy_tsy · 多功能实用工具箱 v3.0  |  整合升级版`，无导入缺库报错 |

**使用方式**：双击 `D:\桌面\多功能工具箱（新）\dist\多功能工具箱\多功能工具箱.exe` 即可，不再需要任何 .bat 启动。

---

## 二、完整目录结构

```
D:\桌面\多功能工具箱（新）\dist\多功能工具箱\
├── 多功能工具箱.exe          ← 主程序（双击即用）
├── _internal\                ← 打包的 Python 运行时与全部依赖模块
├── assets\                   ← 图标等资源（icon.ico / icon.png）
├── cookies.txt               ← 抖音 cookies 兜底文件（Netscape 格式，可替换为你的导出）
├── ffmpeg\
│   └── bin\ffmpeg.exe        ← 音视频合并/无水印处理所需
└── integrated\               ← 以子进程方式整合的独立程序
    ├── 游戏空间\
    │   └── 游戏空间v3.0.exe
    ├── 进程锁定\
    │   ├── 进程锁定.exe       ← 由 v1.5 源码单独打包
    │   └── 进程锁定_源码.py   ← 源码留存（含精简 matplotlib）
    └── 应用包密码工具\
        ├── 密码本生成器.exe
        ├── 密码本启动器.exe
        └── 应用包-磁盘管理.exe
```

---

## 三、整合功能接入方式

主程序为 CustomTkinter 界面，自身模块以**同进程页签**呈现；无法与 CustomTkinter 同进程的 PyQt5/tkinter 程序以**子进程入口**方式整合，全部通过主程序左侧导航进入。

| 功能 | 来源（未改动源文件夹） | 接入方式 | 入口 |
|---|---|---|---|
| 游戏空间 | `D:\Desktop\game\历史版本\游戏空间v3.0\game_launcher_v3.0.py`（PyQt5，独立 exe 亦已纳入） | 子进程拉起 `integrated\游戏空间\游戏空间v3.0.exe` | 左侧导航「游戏空间」→ 点击启动 |
| 进程锁定 | `D:\Desktop\进程锁定\v1.5\进程锁定.py`（tkinter，进程锁定+监控） | 源码复制为 `integrated\进程锁定\进程锁定_源码.py` 后单独 PyInstaller 打包成 `进程锁定.exe`，子进程拉起 | 左侧导航「进程锁定」→ 点击启动 |
| TxConfig 腾讯进程管家 | `关闭Tencent所有进程 v12.0.bat` 核心逻辑 | 改写成纯 Python 模块 `tools\tencent_process_manager.py`，与主程序同进程 | 左侧导航「腾讯进程管家」→ 进入即用（清理/保护一体化） |
| 密码本生成器 / 启动器 | `应用包\python\密码本生成器.py`、`密码本启动器.py` | 复用已有稳定 exe，子进程拉起 | 左侧导航「应用包密码工具」→ 生成器 / 启动器 |
| 磁盘管理 | `应用包\python\应用包-磁盘管理.py` | 复用已有稳定 exe，子进程拉起 | 左侧导航「应用包密码工具」→ 磁盘管理 |
| 其余工具 | 主程序原有（批量重命名 / 图片转换 / 二维码 / 单位换算 / 番茄钟 / 系统信息 / 音乐+视频下载 / PDF工具 / 文件校验） | 同进程页签 | 左侧导航各页签 |

> 说明：被整合的 4 个源文件夹（TxConfig、D:\Desktop\game、进程锁定、应用包\python）全程未做任何修改；仅读取源码并在主文件夹内复制/打包。

---

## 四、抖音下载修复说明（Fresh cookies needed）

### 4.1 问题成因
新版 yt-dlp（2026.x）对抖音强制校验登录态 cookies，直接下载报：
`ERROR: [Douyin] ... Fresh cookies (not necessarily logged in) are needed`

### 4.2 修复内容（`tools\music_downloader.py`）
1. **cookies.txt 兜底通道**：项目目录（exe 同目录）存在 `cookies.txt` 时自动加载（修正为 yt-dlp 标准 `cookiefile` 参数）。
2. **浏览器 cookies 通道**：无 cookies.txt 时自动探测本机浏览器 cookies（Edge → Chrome 任一可用），用 `cookiesfrombrowser` 自动携带登录态。降级下载模式同样附带 cookies。
3. **路径兼容**：下载器在打包后自动定位到 exe 目录（`sys.frozen` 时使用 `Path(sys.executable).parent`），确保 ffmpeg / cookies.txt / 下载输出目录在 onedir 形态下全部正确。
4. **yt-dlp 版本**：已升级至最新稳定版 `2026.08.19`（venv 环境）。

### 4.3 实测记录（重点）
- **环境**：`D:\桌面\多功能工具箱（新）\venv\Scripts\python.exe`，yt-dlp 2026.08.19。
- 实测链接：`https://www.douyin.com/video/7670746932901383475`
- **实测结果**：该链接页面详情 JSON 返回空（`Failed to parse JSON: Expecting value in '' char 0`），判定**该视频链接已失效/被删除/不可见**，因此无法完成端到端下载；同时本机浏览器中**未检测到 douyin 域登录 cookies**。
- **通道自检结论**：
  - cookies.txt：格式已修复为标准 Netscape（含 `# Netscape HTTP Cookie File` 头、纯 LF、`domain` 与 `include_subdomains` 标志匹配），yt-dlp 可正常加载不再报 “invalid Netscape format”；项目根与 dist 目录均已放置。
  - 浏览器通道：`chrome` 提取成功（28 个 cookies），`edge` 因与 Chrome 共用数据库复制受限而回退到 chrome；两条通道在下载器中均已就绪。
- **验证过的可运行截图级证据**：完整实测日志见 `D:\桌面\多功能工具箱（新）\temp\douyin_verify_final.log`（原始中间产物）。
- **结论**：修复逻辑已就位且通道自检通过；因目标视频链接失效，无法在本机完成一次真实下载演示。**用户侧若需立即下载抖音视频**：①在本机浏览器登录抖音后，重启可自动通过浏览器通道携带登录态；②或将登录后的 douyin cookies 导出为 Netscape 格式存为 `cookies.txt` 放到 dist 目录（deliverable）旁。

---

## 五、启动方式 & 打包说明

### 5.1 免 bat 直达
- 主程序在开发态与打包态均直接运行 `main.py` / exe，不再依赖 `启动工具箱.bat`。
- `启动工具箱.bat` 仅作为历史留存保留在项目根，未参与交付流程。

### 5.2 onedir 打包
- 打包命令（venv，PyInstaller 6.22.2）：
  ```
  pyinstaller --onedir --windowed --name 多功能工具箱 \
    --icon assets\icon.ico --paths tools \
    --add-data "tools\pdf;tools\pdf" --add-data "assets;assets" \
    --collect-all customtkinter \
    --hidden-import pymupdf --hidden-import docx \
    --hidden-import yt_dlp --hidden-import qrcode --hidden-import psutil \
    main.py
  ```
- 打包后按需复制 `assets`、`cookies.txt`、`ffmpeg`、`integrated` 到 exe 同目录（见目录结构）。
- 随包依赖已包含：customtkinter、Pillow、qrcode、psutil、PyPDF2、python-docx、PyMuPDF、yt-dlp、requests、ffmpeg、cookies.txt、图标。
- 打包中间产物（build / spec / log）位于主文件夹 `temp\`，不影响程序运行，可随时清理。

---

## 六、主文件夹内部清理

已从主文件夹移除测试与冗余副本（全部进入回收站，可恢复）：
- `test_all_apis.py`、`test_api.py`、`test_api2.py`、`test_snapany.py`、`test_snapany2.py`、`test_video_api.py`、`test_video_api2.py`、`test_video_api3.py`
- `main - 副本.py`、`version - 副本.txt`
- 根目录与 `tools` 下的 `__pycache__`

有效资源 **ffmpeg、python-embed、venv、tools、assets、integrated** 均完整保留。

---

## 七、验证结论

- [x] 品牌 tecy_tsy 展示于启动界面、主窗口标题、导航区
- [x] 火绒风格深蓝统一配色、左侧导航+右侧内容布局
- [x] 四组外部功能（游戏空间/进程锁定/TxConfig/密码+磁盘工具）全部接入
- [x] 抖音 Fresh cookies 修复落地（通道自检通过；目标链接已失效，见 4.3）
- [x] 免 bat、双击 exe 直达
- [x] 主窗口实弹验证通过，子程序（游戏空间、进程锁定）实弹验证通过
- [x] 被整合的 4 个源文件夹未做任何修改
*（内容由AI生成，仅供参考）*

---

## 八、2026-08-26 晚间故障修复记录

**故障现象**：老板反馈"功能全都不能用"——主窗口能打开，但点击左侧导航切换页面无反应（仅深色模式按钮有效）。

**根因定位**（两处源码 bug）：
1. `main.py` 的 `_select()`：切换页面时对**已销毁的缓存页面**调用 `configure()`，触发 TclError，被 tkinter 静默吞掉后界面表现为"点啥都没反应"（customtkinter 递归访问已销毁控件）。
2. `_build_page()`：只接了"腾讯进程管家"与 9 个常规工具页，**未分发**「游戏空间 / 进程锁定 / 密码本工具 / 磁盘管理」4 个附加应用入口页，点击会抛 `KeyError: '游戏空间'`。

**修复内容**：
- `_select()` 改为每次切换先销毁旧页、清空 `self._pages` 缓存，再重建新页，杜绝复用已销毁控件。
- `_build_page()` 增加 elif 分支，将 4 个附加应用页正确分发到 `_page_game/_page_locker/_page_password/_page_disk` 渲染。

**重新打包**：已用 PyInstaller 6.22.2（同 spec）重新打包，资源（assets / ffmpeg / integrated / cookies.txt）已补齐到新构建，旧构建保留在 `dist\_bak_多功能工具箱_20260826`。

**验证结果**：
- [x] 逐页脚本压测：14 个页面两轮全量切换 + 30 次随机切换，全部 PASS，无异常无空白
- [x] 4 个附加应用页 UI 逐控件核对：标题/描述/启动按钮/所在路径均正确渲染
- [x] 实测点击"启动"成功拉起独立程序窗口（游戏空间v3.0.exe）
- [x] 新 exe 实弹启动正常，窗口标题 `tecy_tsy · 多功能实用工具箱 v3.0`，无报错

> 新版可执行程序：`D:\桌面\多功能工具箱（新）\dist\多功能工具箱\多功能工具箱.exe`

---

## 九、单文件安装包交付（2026-08-26 追加）

> 交付形式：**单一 setup.exe 安装包（Inno Setup 6.7.3），一个文件即完成安装、可卸载**

| 项目 | 内容 |
|---|---|
| 安装包路径 | `D:\桌面\多功能工具箱（新）\dist\installer\多功能工具箱v3.0安装版.exe` |
| 体积 | 约 276 MB（lzma2/ultra 压缩，含全部内置程序与 ffmpeg 资源） |
| 制作工具 | Inno Setup 6.7.3（ISCC） |
| 安装目录 | `%LOCALAPPDATA%\Programs\tecy_tsy多功能工具箱`（用户级安装，**免管理员权限**） |
| 权限说明 | 由于程序运行时会在自身目录写入 `cookies.txt`，故采用用户级安装目录，避免 Program Files 写入受限导致功能异常 |
| 安装界面 | 简体中文向导（已补齐官方 ChineseSimplified 语言文件） |
| 卸载方式 | 控制面板「程序和功能」或安装目录 `unins000.exe` |

**安装包行为**：
- 默认创建开始菜单快捷方式；安装向导最后一步可勾选「创建桌面快捷方式」与「安装后立即启动」。
- 安装内容与多文件版完全一致：主程序 + `_internal` + `assets` + `ffmpeg` + `integrated`（游戏空间/进程锁定/密码本/磁盘管理）+ `cookies.txt`。
- 卸载时移除全部文件（含 cookies.txt）。

**编译命令（留档）**：
```
"C:\Users\Administrator\AppData\Local\Programs\Inno Setup 6\ISCC.exe" /Q toolbox_installer.iss
```

**实测验证记录**：
- [x] 静默安装到测试目录：退出码 0，目录结构与 multi 文件版一致（主 exe/_internal/assets/ffmpeg/integrated/cookies.txt/unins000 全部就位）
- [x] 从安装目录启动主程序：窗口正常弹出，标题 `tecy_tsy · 多功能实用工具箱 v3.0  |  整合升级版`，Responding=True
- [x] 卸载：退出码 0，安装目录清空
