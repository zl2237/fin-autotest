# -*- coding: utf-8 -*-
"""
GUI 自动化测试工具
================
基于 pytest + requests + allure 的接口自动化测试 GUI 工具。
打包成单文件 exe 后，双击即用，无需安装 Python。

功能特性：
  - 25 条链路（link1 ~ link25）任选执行
  - 执行完毕后在日志中提示用 allure serve 查看 HTML 报告
  - 配置自动保存/回填，防止重复点击
  - 实时进度展示

打包方式（PyInstaller）：
  onefile 模式：pyinstaller --onefile --noconsole --icon=app.ico GUI.spec
  folder 模式：pyinstaller --onedir --noconsole --icon=app.ico GUI.spec

Author: Auto Generated
Version: 1.0.0
"""

import atexit
import configparser
import ctypes
import json
import os
import queue
import re
import shutil
import subprocess
import sys
if sys.platform == 'win32':
    _HIDDEN_STARTUP_INFO = subprocess.STARTUPINFO()
    _HIDDEN_STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    _HIDDEN_STARTUP_INFO = None
import tempfile
import threading
import time
from pathlib import Path

# ============================================================
# PyInstaller 兼容处理
# ============================================================
def get_resource_path(relative_path: str) -> Path:
    """
    兼容开发环境与 PyInstaller 打包后的资源路径。
    - 开发环境：相对于当前文件所在目录
    - onefile 打包：相对于 sys._MEIPASS
    - onedir 打包：相对于 exe 所在目录
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / relative_path
    return Path(__file__).parent / relative_path


# 基础路径
APP_DIR = Path(__file__).parent.resolve()


def _find_project_dir() -> Path:
    """
    定位运行目录。
    - exe 模式：直接返回 exe 所在目录（dist/），所有配置和报告都在该目录下
    - 开发模式：返回脚本所在目录
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.resolve()


PROJECT_DIR = _find_project_dir()
CONFIG_FILE = PROJECT_DIR / "config.ini"

# Allure 结果收集路径
ALLURE_RESULT_DIR = PROJECT_DIR / "report" / "allure-results"

# ============================================================
# Tkinter GUI
# ============================================================
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    print("[ERROR] tkinter 未安装，请使用打包后的 exe 文件运行")
    sys.exit(1)

# 全局美化样式配置
def init_ttk_style():
    style = ttk.Style()
    # 全局基础样式
    style.theme_use("clam")
    style.configure(".", font=("微软雅黑", 10), background="#f8f9fa")
    # 卡片分组LabelFrame
    style.configure("Card.TLabelframe", background="#ffffff", relief="groove", borderwidth=1)
    style.configure("Card.TLabelframe.Label", font=("微软雅黑", 11, "bold"), foreground="#2c3e50", background="#f8f9fa")
    # 输入框、下拉框
    style.configure("TEntry", fieldbackground="#fff", borderwidth=1)
    style.map("TEntry", fieldbackground=[("focus", "#f0f8ff")])
    style.configure("TCombobox", fieldbackground="#fff")
    style.map("TCombobox", fieldbackground=[("focus", "#f0f8ff")])
    # 进度条
    style.configure("TProgressbar", thickness=8, background="#409eff")
    # 滚动条
    style.configure("Vertical.TScrollbar", background="#e9ecef", troughcolor="#f8f9fa", width=8)
    return style

# ============================================================
# 全局变量
# ============================================================
g_running = False
g_thread = None
g_queue = queue.Queue()
g_current_loop = 0
g_total_loops = 1


# ============================================================
# 配置读写
# ============================================================
def load_config() -> dict:
    """读取本地配置文件，返回字典"""
    cfg = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        try:
            cfg.read(CONFIG_FILE, encoding="utf-8")
            if "settings" in cfg:
                s = cfg["settings"]
                result = {
                    "base_url": s.get("base_url", "https://fin-tidb.21eflag.com"),
                    "nickname": s.get("nickname", ""),
                    "username": s.get("username", ""),
                    "password": s.get("password", ""),
                    "user_id": s.get("user_id", ""),
                    "link": s.get("link", "link1"),
                    "loops": s.get("loops", "1"),
                }
                print(f"[DEBUG] 读取配置成功: {CONFIG_FILE}")
                print(f"[DEBUG] 配置内容: base_url={result['base_url']}, username={result['username']}")
                return result
        except Exception as e:
            print(f"[DEBUG] 读取配置失败: {e}")
    else:
        print(f"[DEBUG] 配置文件不存在: {CONFIG_FILE}")
    return {
        "base_url": "https://fin-tidb.21eflag.com",
        "nickname": "",
        "username": "",
        "password": "",
        "user_id": "",
        "link": "link1",
        "loops": "1",
    }


def save_config(values: dict):
    """保存配置到本地文件"""
    cfg = configparser.ConfigParser()
    cfg["settings"] = {
        "base_url": values.get("base_url", ""),
        "nickname": values.get("nickname", ""),
        "username": values.get("username", ""),
        "password": values.get("password", ""),
        "user_id": values.get("user_id", ""),
        "link": values.get("link", "link1"),
        "loops": values.get("loops", "1"),
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)


# ============================================================
# 进度队列线程安全写入
# ============================================================
def _log_debug(msg: str):
    """调试日志写入文件，方便排查 exe 静默失败问题"""
    try:
        debug_file = PROJECT_DIR / "_debug.log"
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} | {msg}\n")
    except Exception:
        pass


def log_progress(text: str):
    g_queue.put(("log", text))


def log_stats(passed: int, failed: int, skipped: int):
    g_queue.put(("stats", passed, failed, skipped))


def log_loop(loop: int, total: int):
    g_queue.put(("loop", loop, total))


def log_error(text: str):
    g_queue.put(("error", text))


# ============================================================
# 写入测试配置到项目
# ============================================================
def write_test_config(base_url: str, username: str, password: str, user_id: str, nickname: str):
    """将 GUI 配置写入运行目录配置文件，供 pytest/conftest.py 读取"""
    bundle_dir = Path(sys._MEIPASS) if getattr(sys, '_MEIPASS', None) else PROJECT_DIR
    env_file = bundle_dir / ".env"
    _log_debug(f"write_test_config | env_file={env_file} | bundle_dir={bundle_dir} | PROJECT_DIR={PROJECT_DIR}")
    env_content = f"""# GUI 自动生成，不要手动修改
BASE_URL={base_url}
USERNAME={username}
PASSWORD={password}
ORDER_CREATE_ID={user_id}
TOKEN_FIELD=data.token
AUTH_HEADER=Authorization
"""
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)

    gui_cfg = {
        "base_url": base_url,
        "username": username,
        "password": password,
        "user_id": user_id,
        "nickname": nickname,
    }
    gui_cfg_file = PROJECT_DIR / ".gui_config.json"
    with open(gui_cfg_file, "w", encoding="utf-8") as f:
        json.dump(gui_cfg, f, ensure_ascii=False, indent=2)

    nickname_file = PROJECT_DIR / ".gui_nickname.txt"
    with open(nickname_file, "w", encoding="utf-8") as f:
        f.write(nickname)
    nickname_file_bundle = bundle_dir / ".gui_nickname.txt"
    with open(nickname_file_bundle, "w", encoding="utf-8") as f:
        f.write(nickname)


# ============================================================
# 清理旧报告
# ============================================================
def clean_reports():
    """清理旧的 allure-results 目录"""
    _log_debug(f"clean_reports | ALLURE_RESULT_DIR={ALLURE_RESULT_DIR}")
    if ALLURE_RESULT_DIR.exists():
        shutil.rmtree(ALLURE_RESULT_DIR)
    ALLURE_RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 执行测试
# ============================================================
def run_tests(link: str, loops: int, base_url: str, username: str, password: str, user_id: str, nickname: str, app: "TestRunnerApp" = None):
    """在新线程中执行 pytest 测试。app 参数用于设置 _test_process 句柄以便 terminate"""
    global g_running, g_current_loop, g_total_loops

    g_running = True
    g_current_loop = 0
    g_total_loops = loops

    try:
        write_test_config(base_url, username, password, user_id, nickname)
        log_progress(f"[配置] 已写入测试参数（.env -> {PROJECT_DIR}）")

        clean_reports()
        log_progress("[清理] 已清理旧报告")

        # 确定 Python 解释器路径
        if hasattr(sys, '_MEIPASS'):
            python_exe = PROJECT_DIR / "venv" / "Scripts" / "python.exe"
            if not python_exe.exists():
                python_exe = Path(sys.executable).with_name("python.exe")
            if not python_exe.exists():
                log_error("[错误] 打包模式下找不到 python.exe，请确保环境中有 Python")
                log_error(f"[调试] sys.executable={sys.executable}, PROJECT_DIR={PROJECT_DIR}")
                log_error("[调试] 将尝试使用系统 PATH 中的 python...")
                import shutil
                system_python = shutil.which("python")
                if system_python:
                    log_progress(f"[调试] 找到系统 python: {system_python}")
                    python_exe = Path(system_python)
                else:
                    log_error("[停止] 系统中也没有找到 python，测试终止")
                    return
        else:
            python_exe = Path(sys.executable)
        log_progress(f"[调试] Python解释器: {python_exe}")

        # 执行测试（支持循环）
        for i in range(1, loops + 1):
            if not g_running:
                log_progress(f"[停止] 检测到停止信号，放弃后续轮次")
                break
            g_current_loop = i
            log_loop(i, loops)
            log_progress(f"[开始] 第 {i}/{loops} 轮执行...")

            bundle_dir = Path(sys._MEIPASS) if getattr(sys, '_MEIPASS', None) else PROJECT_DIR

            cmd = [
                str(python_exe),
                "-m", "pytest",
                str(bundle_dir / "testcases"),
                "-m", link,
                "-v",
                "--tb=short",
                "--alluredir", str(ALLURE_RESULT_DIR),
            ]

            env = os.environ.copy()
            env["BASE_URL"] = base_url
            env["USERNAME"] = username
            env["PASSWORD"] = password
            env["ORDER_CREATE_ID"] = user_id
            env["PYTHONPATH"] = str(bundle_dir) + os.pathsep + env.get("PYTHONPATH", "")
            _log_debug(f"[{i}] pytest 启动 | cwd={bundle_dir} | PYTHONPATH={bundle_dir} | cmd={' '.join(cmd)}")

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(bundle_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    startupinfo=_HIDDEN_STARTUP_INFO,
                )
                if app is not None:
                    app._test_process = proc
                stdout_data, stderr_data = proc.communicate(timeout=600)
                exit_code = proc.returncode
                if app is not None:
                    app._test_process = None
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise

            _log_debug(f"[{i}] pytest 完成 | returncode={exit_code} | stdout={stdout_data[:500] if stdout_data else ''} | stderr={stderr_data[:500] if stderr_data else ''}")

            output = (stdout_data or "") + (stderr_data or "")
            passed = len(re.findall(r" PASSED", output))
            failed = len(re.findall(r" FAILED", output))
            skipped = len(re.findall(r" SKIPPED", output))

            log_stats(passed, failed, skipped)
            log_progress(f"[完成] 第 {i}/{loops} 轮 - 通过:{passed} 失败:{failed} 跳过:{skipped}")

            if exit_code == 1:
                if failed == 0:
                    log_progress(f"[提示] 第 {i} 轮退出码为 1，但未识别到 FAILED 用例，请检查输出")
            elif exit_code not in (0, 5):
                log_error(f"[警告] 第 {i} 轮执行异常，退出码: {exit_code}")

            if stdout_data:
                log_progress(f"[调试] stdout: {stdout_data[:500]}")
            if stderr_data:
                log_progress(f"[调试] stderr: {stderr_data[:500]}")

        # 执行完毕，提示查看报告
        log_progress("[完成] 全部测试执行完毕！")
        log_progress(f"[完成] allure-results 已保存在: {ALLURE_RESULT_DIR}")
        log_progress("[完成] 查看 HTML 报告请执行: allure serve report/allure-results")
        log_progress("[完成] 或先执行: allure generate report/allure-results -o report/allure-report")
        log_progress("[完成] 然后打开: report/allure-report/index.html")
        g_queue.put(("finish",))

    except subprocess.TimeoutExpired:
        log_error("[错误] pytest 执行超时（10分钟），已强制终止")
        log_error("请检查网络连接或测试用例是否有死循环")

    except Exception as e:
        log_error(f"[错误] 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        log_error(f"[调试] {traceback.format_exc()}")

    finally:
        g_running = False


# ============================================================
# GUI 应用类
# ============================================================
class TestRunnerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("物流系统接口自动化测试工具")
        self.root.geometry("600x900")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")

        init_ttk_style()

        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self._center_window()
        self.config = load_config()
        self._create_widgets()
        self._load_config_to_ui()
        self._test_thread = None
        self._test_process = None  # 当前 pytest subprocess 句柄，用于 terminate 终止
        self._poll_queue()
        atexit.register(self._on_exit)

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部警告提示
        warn_frame = tk.Frame(main_frame, bg="#fff7e6", bd=0, relief=tk.FLAT)
        warn_frame.pack(fill=tk.X, pady=(0, 16))
        warn_frame.config(padx=12, pady=10)

        warn_text = (
            "⚠️ 前置权限说明：\n1.账号需提前开通审批流权限：资产推送 | 未放款开票 | 供应商垫付 | 订单锁定 | 应收开票批次；\n2.执行过程请勿登录测试账号。"
        )
        warn_label = tk.Label(
            warn_frame,
            text=warn_text,
            justify=tk.LEFT,
            wraplength=580,
            font=("微软雅黑", 9),
            bg="#fff7e6",
            fg="#d46b08",
        )
        warn_label.pack(fill=tk.X)

        # 基础环境配置
        info_frame = ttk.LabelFrame(main_frame, text=" 基础环境配置 ", padding="14", style="Card.TLabelframe")
        info_frame.pack(fill=tk.X, pady=(0, 14))

        row = ttk.Frame(info_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="运行环境地址：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.base_url_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.base_url_var, width=58).pack(side=tk.LEFT, fill=tk.X, expand=True)

        row = ttk.Frame(info_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="提单号前缀：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(row, textvariable=self.nickname_var, width=22)
        nickname_entry.pack(side=tk.LEFT)
        tk.Label(row, text="  仅支持≤4位字母/数字，不输入默认为lele", foreground="#8c8c8c", bg="#ffffff",
                 font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(12, 0))

        # 账号信息
        account_frame = ttk.LabelFrame(main_frame, text=" 登录账号信息 ", padding="14", style="Card.TLabelframe")
        account_frame.pack(fill=tk.X, pady=(0, 14))

        row = ttk.Frame(account_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="账    号：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.username_var, width=26).pack(side=tk.LEFT)

        ttk.Label(row, text="密    码：", width=10, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(18, 0))
        self.password_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.password_var, show="*", width=22).pack(side=tk.LEFT)

        row = ttk.Frame(account_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="User ID：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.user_id_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.user_id_var, width=58).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 执行链路配置
        test_frame = ttk.LabelFrame(main_frame, text=" 执行链路配置 ", padding="14", style="Card.TLabelframe")
        test_frame.pack(fill=tk.X, pady=(0, 14))

        row = ttk.Frame(test_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="业务执行链路：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.link_var = tk.StringVar()
        link_combo = ttk.Combobox(
            row,
            textvariable=self.link_var,
            values=[f"link{i}" for i in range(1, 26)],
            state="readonly",
            width=22,
            font=("微软雅黑", 10),
        )
        link_combo.pack(side=tk.LEFT)
        link_combo.current(0)
        link_combo.bind("<<ComboboxSelected>>", lambda e: self._on_link_selected())

        self.link_desc_label = tk.Label(row, text="", foreground="#409eff", font=("微软雅黑", 9), bg="#ffffff")
        self.link_desc_label.pack(side=tk.LEFT, padx=(14, 0))
        self._on_link_selected()

        row = ttk.Frame(test_frame)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="循环执行次数：", width=13, font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.loops_var = tk.StringVar(value="1")
        loops_entry = ttk.Entry(row, textvariable=self.loops_var, width=12)
        loops_entry.pack(side=tk.LEFT)
        tk.Label(row, text="  次（仅允许正整数）", foreground="#8c8c8c", bg="#ffffff", font=("微软雅黑", 9)).pack(
            side=tk.LEFT, padx=(12, 0))

        # 执行按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 16))

        self.start_btn = tk.Button(
            btn_frame,
            text="▶  开始执行测试",
            command=self._on_start,
            font=("微软雅黑", 12, "bold"),
            bg="#36c86b",
            fg="#ffffff",
            activebackground="#2db35c",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=26,
            pady=9,
            cursor="hand2",
            bd=0
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 14))

        self.stop_btn = tk.Button(
            btn_frame,
            text="■  终止运行",
            command=self._on_stop,
            font=("微软雅黑", 12),
            bg="#f54242",
            fg="#ffffff",
            activebackground="#d93636",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=26,
            pady=9,
            cursor="hand2",
            state=tk.DISABLED,
            bd=0
        )
        self.stop_btn.pack(side=tk.LEFT)

        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text=" 实时执行日志 & 进度 ", padding="14",
                                        style="Card.TLabelframe")
        progress_frame.pack(fill=tk.BOTH, expand=True)

        stats_row = ttk.Frame(progress_frame)
        stats_row.pack(fill=tk.X, pady=(0, 8))
        self.loop_label = tk.Label(
            stats_row, text="等待执行...", font=("微软雅黑", 10), foreground="#666666", bg="#ffffff"
        )
        self.loop_label.pack(side=tk.LEFT)
        self.stats_label = tk.Label(
            stats_row, text="通过: 0  |  失败: 0  |  跳过: 0", font=("微软雅黑", 10, "bold"), foreground="#2c3e50",
            bg="#ffffff"
        )
        self.stats_label.pack(side=tk.LEFT, padx=(24, 0))

        self.progress = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=580
        )
        self.progress.pack(fill=tk.X, pady=(0, 8))

        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(
            log_frame,
            height=22,
            font=("Consolas", 9),
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg="#171b22",
            fg="#89e894",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=6
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview, style="Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _on_link_selected(self):
        link_map = {
            "link1": "新建订单",
            "link2": "分发订单",
            "link3": "暂存订单",
            "link4": "提交订单",
            "link5": "生成子订单",
            "link6": "录费用",
            "link7": "资产推送审批",
            "link8": "订单锁定审批",
            "link9": "未放款开票申请审批",
            "link10": "供应商垫付申请审批",
            "link11": "生成费用通知单",
            "link12": "生成费用确认单",
            "link13": "发起应收对账批次",
            "link14": "确认应收对账",
            "link15": "发起应收开票批次审批",
            "link16": "审核生成开票申请",
            "link17": "发票上传与登记",
            "link18": "应收核销",
            "link19": "发起应付对账批次",
            "link20": "确认应付对账",
            "link21": "发起应付开票批次申请",
            "link22": "应付发票上传与登记",
            "link23": "发起付款需求",
            "link24": "审核生成付款单",
            "link25": "付款单核销",
        }
        link = self.link_var.get()
        desc = link_map.get(link, "")
        self.link_desc_label.config(text=desc)

    def _load_config_to_ui(self):
        self.base_url_var.set(self.config.get("base_url", "https://fin-tidb.21eflag.com"))
        self.nickname_var.set(self.config.get("nickname", ""))
        self.username_var.set(self.config.get("username", ""))
        self.password_var.set(self.config.get("password", ""))
        self.user_id_var.set(self.config.get("user_id", ""))
        self.loops_var.set(self.config.get("loops", "1"))

        link = self.config.get("link", "link1")
        if link in [f"link{i}" for i in range(1, 26)]:
            self.link_var.set(link)
        else:
            self.link_var.set("link1")
        self._on_link_selected()

    def _get_values(self) -> dict:
        return {
            "base_url": self.base_url_var.get().strip(),
            "nickname": self.nickname_var.get().strip()[:4],
            "username": self.username_var.get().strip(),
            "password": self.password_var.get(),
            "user_id": self.user_id_var.get().strip(),
            "link": self.link_var.get(),
            "loops": self.loops_var.get().strip(),
        }

    def _validate(self, values: dict) -> tuple:
        errors = []

        if not values["base_url"]:
            errors.append("运行环境 不能为空")
        elif not values["base_url"].startswith(("http://", "https://")):
            errors.append("运行环境 必须以 http:// 或 https:// 开头")

        if not values["username"]:
            errors.append("账号 不能为空")

        if not values["password"]:
            errors.append("密码 不能为空")

        if not values["user_id"]:
            errors.append("user_id 不能为空")

        loops = values["loops"]
        if not loops:
            errors.append("循环次数 不能为空")
        elif not loops.isdigit() or int(loops) <= 0:
            errors.append("循环次数 必须为正整数")

        if not values["link"]:
            errors.append("请选择链路")

        return len(errors) == 0, "\n".join(errors)

    def _append_log(self, text: str):
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        if "[错误]" in text or "[警告]" in text:
            self.log_text.tag_config("err", foreground="#ff7c7c")
            self.log_text.insert(tk.END, f"[{timestamp}] {text}\n", "err")
        elif "[完成]" in text or "[成功]" in text:
            self.log_text.tag_config("ok", foreground="#67d8ff")
            self.log_text.insert(tk.END, f"[{timestamp}] {text}\n", "ok")
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {text}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_start(self):
        global g_thread

        values = self._get_values()
        valid, err_msg = self._validate(values)
        if not valid:
            messagebox.showwarning("输入校验失败", err_msg)
            return

        save_config(values)
        self._append_log(f"[保存] 配置已保存到 {CONFIG_FILE}")

        self.start_btn.config(state=tk.DISABLED, bg="#a0d8a0")
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start(10)

        g_thread = threading.Thread(
            target=run_tests,
            args=(
                values["link"],
                int(values["loops"]),
                values["base_url"],
                values["username"],
                values["password"],
                values["user_id"],
                values["nickname"],
                self,
            ),
            daemon=True,
        )
        g_thread.start()
        self._test_thread = g_thread

    def _on_stop(self):
        """停止测试：先 terminate pytest subprocess，再设置标志位"""
        global g_running
        g_running = False
        if self._test_process is not None:
            try:
                self._test_process.terminate()
                self._append_log("[停止] 已向 pytest 进程发送终止信号")
            except Exception as e:
                self._append_log(f"[停止] terminate 失败: {e}")
        self._append_log("[停止] 收到终止信号，等待当前轮次结束...")
        self.stop_btn.config(state=tk.DISABLED)

    def _poll_queue(self):
        try:
            while True:
                msg = g_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "log":
                    self._append_log(msg[1])

                elif msg_type == "stats":
                    passed, failed, skipped = msg[1], msg[2], msg[3]
                    self.stats_label.config(
                        text=f"通过: {passed}  |  失败: {failed}  |  跳过: {skipped}"
                    )

                elif msg_type == "loop":
                    loop, total = msg[1], msg[2]
                    self.loop_label.config(text=f"正在执行第 {loop}/{total} 轮")

                elif msg_type == "finish":
                    self.progress.stop()
                    self.loop_label.config(text="本次运行完毕")
                    self.start_btn.config(state=tk.NORMAL, bg="#36c86b")
                    self.stop_btn.config(state=tk.DISABLED)

                elif msg_type == "error":
                    self._append_log(f"[错误] {msg[1]}")
                    self.progress.stop()
                    self.start_btn.config(state=tk.NORMAL, bg="#36c86b")
                    self.stop_btn.config(state=tk.DISABLED)

        except queue.Empty:
            pass

        self.root.after(200, self._poll_queue)

    def _on_exit(self):
        values = self._get_values()
        save_config(values)

    def run(self):
        self.root.mainloop()


# ============================================================
# 程序入口
# ============================================================
def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    root = tk.Tk()
    app = TestRunnerApp(root)
    app.run()


if __name__ == "__main__":
    main()
