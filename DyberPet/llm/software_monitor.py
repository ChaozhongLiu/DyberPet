from datetime import datetime
import psutil
import time
import os
from threading import Thread
import win32process  # 新增
import win32gui  # 新增

class SoftwareMonitor:
    def __init__(self):
        self.active_processes = {}  # 记录所有用户进程
        self.last_check_time = datetime.now()
        self.last_active_window = None  # 当前活跃窗口
        self.current_user = os.getlogin()  # 获取当前用户名
        
        # 初始化进程监控
        self.monitor_running = True
        self._new_software_opened = None
        self._software_closed = None
        self._is_first_check = True  # 添加一个标志，标记是否是第一次检查
        self.start_process_monitor()
    
    def start_process_monitor(self):
        """初始化进程监控，但不创建单独线程"""
        # 初始化系统进程PID列表
        self.system_parent_pids = set()
        
        # 获取系统进程PID
        try:
            explorer_pid = None
            system_pids = set()
            
            # 找到explorer.exe的PID和其他系统进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == 'explorer.exe':
                        explorer_pid = proc.pid
                    if proc.info['name'].lower() in ['system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe']:
                        system_pids.add(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 添加explorer和系统进程到父进程列表
            if explorer_pid:
                self.system_parent_pids.add(explorer_pid)
            self.system_parent_pids.update(system_pids)
        except Exception as e:
            print(f"获取系统进程错误: {e}")
        
        # 初始化上次检查的进程列表
        self.last_processes = set()
        
        # 进行一次初始扫描
        self._check_processes()

    def _check_processes(self):
        """检查进程状态，更新活跃进程列表"""
        try:
            # 获取当前所有进程
            current_processes = set()
            main_apps = {}  # 存储主要应用程序
            
            # 收集所有用户的主要应用程序
            for proc in psutil.process_iter(['pid', 'name', 'username', 'exe', 'ppid']):
                try:
                    # 只处理当前用户的进程
                    if proc.info['username'] and self.current_user in proc.info['username']:
                        process_name = proc.info['name']
                        ppid = proc.info['ppid']
                        
                        # 新增判断：检查进程是否有可见窗口
                        try:
                            import win32gui
                            import win32process
                            # 获取进程的所有窗口
                            def enum_window_callback(hwnd, pid):
                                if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
                                    if win32gui.IsWindowVisible(hwnd):
                                        return True
                                return False
                            
                            has_visible_window = False
                            windows = []
                            win32gui.EnumWindows(lambda hwnd, param: windows.append(hwnd) if enum_window_callback(hwnd, proc.pid) else None, None)
                            has_visible_window = len(windows) > 0
                        except:
                            # 如果无法检查窗口，则回退到原始逻辑
                            has_visible_window = ppid in self.system_parent_pids
                        
                        # 只关注有可见窗口或由explorer启动的应用
                        if has_visible_window or ppid in self.system_parent_pids:
                            # 排除一些常见的系统工具
                            if process_name.lower() not in ['svchost.exe', 'conhost.exe', 'rundll32.exe', 'dllhost.exe']:
                                current_processes.add(process_name)
                                main_apps[process_name] = {
                                    'pid': proc.pid,
                                    'exe': proc.info.get('exe', ''),
                                    'has_window': has_visible_window
                                }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 检测新打开的主要应用
            for process_name in current_processes:
                if process_name not in self.last_processes and process_name not in self.active_processes:
                    # 直接在这里处理新进程
                    self.active_processes[process_name] = {
                        'pid': main_apps[process_name]['pid'],
                        'start_time': datetime.now(),
                        'window_title': ''  # 初始化窗口标题
                    }
                    
                    # 只有在非首次检查时才设置新打开的软件
                    if not self._is_first_check:
                        self._new_software_opened = process_name
                    
            # 检测已关闭的主要应用
            closed_processes = self.last_processes - current_processes
            for process_name in closed_processes:
                if process_name in self.active_processes:
                    # 直接在这里处理进程关闭
                    self._software_closed = process_name
                    
                    # 从活跃进程列表中移除
                    del self.active_processes[process_name]
                    
            # 更新当前活跃窗口和窗口标题
            try:
                # 使用win32gui获取前台窗口进程和标题
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                # 重置活跃窗口标志
                self.last_active_window = None
                
                # 查找对应的进程名
                for name, info in self.active_processes.items():
                    if info['pid'] == pid:
                        # 更新窗口标题
                        self.active_processes[name]['window_title'] = window_title
                        
                        # 设置当前活跃窗口
                        self.last_active_window = name
                        break
            except:
                pass
            
            self.last_processes = current_processes.copy()
            
            # 第一次检查完成后，将标志设置为False
            if self._is_first_check:
                self._is_first_check = False
                
        except Exception as e:
            print(f"进程监控错误: {e}")

    def update(self):
        """
        更新软件使用统计，返回三个参数：
        1. 当前活跃窗口信息
        2. 新打开的软件名称（如果有）
        3. 关闭的软件名称（如果有）
        """
        # 在每次调用update时检查进程状态
        self._check_processes()
        
        current_time = datetime.now()
        self.last_check_time = current_time
        
        # 获取当前活跃窗口信息
        active_window = None
        if self.last_active_window:
            active_window = {
                'name': self.last_active_window,
                'pid': self.active_processes[self.last_active_window]['pid'],
                'title': self.active_processes[self.last_active_window].get('window_title', '')
            }
        
        # 获取新打开和关闭的软件名称
        new_software_opened = self._new_software_opened
        software_closed = self._software_closed
        
        # 重置事件标记
        self._new_software_opened = None
        self._software_closed = None
        
        return active_window, new_software_opened, software_closed

# 测试代码
if __name__ == "__main__":
    # 创建软件监控实例
    monitor = SoftwareMonitor()
    print("此程序将监控用户打开和关闭的应用程序，以及当前活跃的窗口")
    print("按Ctrl+C退出测试")
    
    try:
        while True:
            # 更新并获取监控数据
            active_window, new_software, closed_software = monitor.update()
            
            print("\n" + "="*10 + "活跃进程:" + "="*10)
            # 创建副本避免迭代时修改
            active_processes = list(monitor.active_processes.items())
            for name, info in active_processes:
                print(f"    {name}")
            
            print("\n" + "="*10 + "当前活跃窗口:" + "="*10)
            if active_window:
                if active_window['title']:
                    print(f"  {active_window['name']} - {active_window['title']}")
                else:
                    print(f"  {active_window['name']}")
            else:
                print("  无活跃窗口")
            
            if new_software:
                print("\n" + "="*10 + "新打开的软件:" + "="*10)
                print(f"  {new_software}")
            
            if closed_software:
                print("\n" + "="*10 + "关闭的软件:" + "="*10)
                print(f"  {closed_software}")
            
            print("="*30)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n监控已停止")
        monitor.monitor_running = False  # 停止进程监控