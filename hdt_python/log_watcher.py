# log_watcher.py - 日志监控系统（仿照HDT的LogWatcherManager）

import glob
import os
import sys
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from pathlib import Path

if sys.platform == "win32":
    import winreg
else:
    winreg = None  # type: ignore


class LogWatcher(ABC):
    """
    日志监控基类
    仿照 HDT 的 LogWatcher
    """

    def __init__(self, log_file: str, name: str):
        self.log_file = log_file
        self.name = name
        self.file_handle: Optional[object] = None
        self.running = False
        self.last_position = 0
        self.callbacks = []

    def start(self, read_last_lines: int = 0):
        """开始监控日志

        Args:
            read_last_lines: 启动时读取最后N行（0表示智能检测最后一个游戏）
        """
        if not os.path.exists(self.log_file):
            print(f"[{self.name}] 日志文件不存在: {self.log_file}")
            return False

        self.file_handle = open(self.log_file, 'r', encoding='utf-8', errors='ignore')

        if read_last_lines == 0 and self.name == "Power":
            # 智能模式：找到最后一个 CREATE_GAME（含其前 DebugPrintGame 前缀）
            print(f"[{self.name}] 智能模式：查找最后一个游戏...")
            self.file_handle.seek(0)
            all_lines = self.file_handle.readlines()

            from .power_parser import find_last_game_replay_start

            last_game_start = find_last_game_replay_start(all_lines)

            if last_game_start >= 0:
                create_line = next(
                    (
                        i + 1
                        for i in range(last_game_start, len(all_lines))
                        if "CREATE_GAME" in all_lines[i]
                    ),
                    last_game_start + 1,
                )
                print(
                    f"[{self.name}] 找到最后一个游戏，从第 {last_game_start + 1} 行回放"
                    f"（CREATE_GAME 在第 {create_line} 行，共 {len(all_lines) - last_game_start} 行）"
                )
                for line in all_lines[last_game_start:]:
                    line = line.rstrip('\n\r')
                    if line:
                        self.process_line(line)
            else:
                print(f"[{self.name}] 未找到游戏记录，只监控新数据")

            self.last_position = self.file_handle.tell()

        elif read_last_lines > 0:
            # 读取最后N行
            self.file_handle.seek(0, os.SEEK_END)
            file_size = self.file_handle.tell()
            # 估算每行100字节，回退到合适位置
            estimated_pos = max(0, file_size - read_last_lines * 100)
            self.file_handle.seek(estimated_pos)
            # 读取并处理这些行
            lines = self.file_handle.readlines()
            print(f"[{self.name}] 读取历史记录: {len(lines)} 行")
            for line in lines:
                line = line.rstrip('\n\r')
                if line:
                    self.process_line(line)
            self.last_position = self.file_handle.tell()
        else:
            # 跳到文件末尾，只读取新内容
            self.file_handle.seek(0, os.SEEK_END)
            self.last_position = self.file_handle.tell()

        self.running = True
        print(f"[{self.name}] 开始监控: {self.log_file}")
        return True

    def stop(self):
        """停止监控"""
        self.running = False
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        print(f"[{self.name}] 停止监控")

    def read_new_lines(self):
        """读取新行"""
        if not self.file_handle:
            return []

        lines = []
        try:
            # 检查文件是否被重新创建（游戏重启）
            current_size = os.path.getsize(self.log_file)
            if current_size < self.last_position:
                # 文件被重置，重新打开
                self.file_handle.close()
                self.file_handle = open(self.log_file, 'r', encoding='utf-8', errors='ignore')
                self.last_position = 0

            self.file_handle.seek(self.last_position)
            new_lines = self.file_handle.readlines()
            self.last_position = self.file_handle.tell()

            for line in new_lines:
                line = line.rstrip('\n\r')
                if line:
                    lines.append(line)

        except Exception as e:
            print(f"[{self.name}] 读取错误: {e}")

        return lines

    def add_callback(self, callback: Callable[[str], None]):
        """添加回调函数"""
        self.callbacks.append(callback)

    @abstractmethod
    def process_line(self, line: str):
        """处理单行日志（子类实现）"""
        pass


class LogWatcherManager:
    """
    日志监控管理器
    仿照 HDT 的 LogWatcherManager
    管理多个日志监控器
    """

    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.watchers: Dict[str, LogWatcher] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def register_watcher(self, name: str, watcher: LogWatcher):
        """注册日志监控器"""
        self.watchers[name] = watcher
        print(f"[Manager] 注册监控器: {name}")

    def start(self, read_last_lines: int = 0):
        """启动所有监控器

        Args:
            read_last_lines: 启动时读取最后N行历史记录（默认0，智能检测最后一个游戏）
        """
        print("[Manager] 启动日志监控系统...")
        if read_last_lines > 0:
            print(f"[Manager] 读取历史记录: 最后 {read_last_lines} 行")
        else:
            print("[Manager] 智能模式：自动检测最后一个游戏")

        # 启动所有监控器
        for name, watcher in self.watchers.items():
            if watcher.start(read_last_lines=read_last_lines):
                print(f"[Manager] {name} 已启动")

        # 启动监控线程
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        print("[Manager] 监控线程已启动")

    def stop(self):
        """停止所有监控器"""
        print("[Manager] 停止日志监控系统...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=1.0)

        for name, watcher in self.watchers.items():
            watcher.stop()

        print("[Manager] 已停止")

    def _watch_loop(self):
        """监控循环（在独立线程中运行）"""
        last_log_check = 0.0
        while self.running:
            try:
                now = time.time()
                if now - last_log_check >= 5.0:
                    last_log_check = now
                    for watcher in self.watchers.values():
                        switch = getattr(watcher, "try_switch_log_file", None)
                        if callable(switch):
                            switch()

                # 轮询所有监控器
                for name, watcher in self.watchers.items():
                    if not watcher.running:
                        continue

                    # 读取新行
                    new_lines = watcher.read_new_lines()

                    # 处理每一行
                    for line in new_lines:
                        try:
                            watcher.process_line(line)

                            # 调用所有回调
                            for callback in watcher.callbacks:
                                callback(line)

                        except Exception as e:
                            print(f"[{name}] 处理行时出错: {e}")
                            # 继续处理下一行，不中断

                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)

            except Exception as e:
                print(f"[Manager] 监控循环错误: {e}")
                time.sleep(1.0)


def _registry_string(hive, subkey: str, value_name: Optional[str] = None) -> Optional[str]:
    """读取注册表字符串；失败返回 None。"""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(hive, subkey) as key:
            raw, _ = winreg.QueryValueEx(key, value_name or "")
            if raw is None:
                return None
            if isinstance(raw, bytes):
                text = raw.decode("utf-8", errors="ignore").split("\x00", 1)[0]
            else:
                text = str(raw)
            text = text.strip().strip('"')
            return text or None
    except OSError:
        return None


def _normalize_install_dir(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    p = os.path.normpath(path.strip().strip('"'))
    if p.lower().endswith(".exe"):
        p = os.path.dirname(p)
    if os.path.isdir(p):
        return p
    return None


def _registry_install_dirs() -> List[str]:
    """
    从 Windows 注册表读取炉石安装目录（与 HDT / 卸载信息同源）。
    典型项：Uninstall\\Hearthstone → InstallLocation
    """
    if winreg is None:
        return []

    seen: set = set()
    roots: List[str] = []

    def add(path: Optional[str]) -> None:
        norm = _normalize_install_dir(path)
        if norm and norm not in seen:
            seen.add(norm)
            roots.append(norm)

    uninstall_subkeys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Hearthstone"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Hearthstone"),
    )
    for hive, subkey in uninstall_subkeys:
        add(_registry_string(hive, subkey, "InstallLocation"))
        add(_registry_string(hive, subkey, "InstallSource"))
        add(_registry_string(hive, subkey, "DisplayIcon"))

    blizzard_subkeys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Blizzard Entertainment\Hearthstone"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Blizzard Entertainment\Hearthstone"),
    )
    for hive, subkey in blizzard_subkeys:
        for name in ("InstallPath", "Install Location", "Path"):
            add(_registry_string(hive, subkey, name))

    app_path_subkeys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Hearthstone.exe"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\Hearthstone.exe"),
    )
    for hive, subkey in app_path_subkeys:
        add(_registry_string(hive, subkey, None))

    return roots


def _power_log_candidates(install_dirs: List[str]) -> List[str]:
    """在安装目录的 Logs 树下枚举所有 Power.log。"""
    found: List[str] = []
    seen: set = set()
    for root in install_dirs:
        logs_root = os.path.join(root, "Logs")
        if not os.path.isdir(logs_root):
            continue
        direct = os.path.join(logs_root, "Power.log")
        if os.path.isfile(direct) and direct not in seen:
            seen.add(direct)
            found.append(direct)
        for session in glob.glob(os.path.join(logs_root, "Hearthstone_*")):
            for rel in ("Power.log", os.path.join("Logs", "Power.log")):
                pl = os.path.join(session, rel)
                if os.path.isfile(pl) and pl not in seen:
                    seen.add(pl)
                    found.append(pl)
        for pl in glob.glob(os.path.join(logs_root, "**", "Power.log"), recursive=True):
            if pl not in seen:
                seen.add(pl)
                found.append(pl)
    return found


def find_power_log_path() -> Optional[str]:
    """通过注册表安装路径定位当前最新的 Power.log 完整路径。"""
    if winreg is None:
        print("[Finder] 仅支持 Windows 注册表定位 Power.log")
        return None

    install_dirs = _registry_install_dirs()
    if not install_dirs:
        print("[Finder] 注册表中未找到炉石传说安装目录")
        return None

    candidates = _power_log_candidates(install_dirs)
    if not candidates:
        print("[Finder] 安装目录下未找到 Power.log")
        print("[Finder] 安装路径:", install_dirs)
        return None

    candidates.sort(key=os.path.getmtime, reverse=True)
    chosen = candidates[0]
    print(f"[Finder] Power.log: {chosen}")
    if len(candidates) > 1:
        print(f"[Finder] 另有 {len(candidates) - 1} 个历史会话日志（已选最新）")
    return chosen


def find_hearthstone_logs() -> Optional[str]:
    """Power.log 所在目录（供 LogWatcherManager 使用）。"""
    power_log = find_power_log_path()
    return os.path.dirname(power_log) if power_log else None


def install_log_config():
    """
    安装 log.config 到炉石传说目录
    仿照 HDT 的配置
    """
    username = os.environ.get("USERNAME", "")
    config_path = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Blizzard",
        "Hearthstone",
        "log.config"
    )

    # 如果已存在，不覆盖
    if os.path.exists(config_path):
        print(f"[Config] log.config 已存在: {config_path}")
        return True

    # 读取我们的配置模板
    from hdt_python.app_paths import resource_path
    template_path = str(resource_path("log.config"))
    if not os.path.exists(template_path):
        print("[Config] 找不到 log.config 模板")
        return False

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 复制配置文件
        import shutil
        shutil.copy(template_path, config_path)
        print(f"[Config] 已安装 log.config 到: {config_path}")
        print("[Config] 请重启炉石传说以应用配置")
        return True

    except Exception as e:
        print(f"[Config] 安装失败: {e}")
        return False
