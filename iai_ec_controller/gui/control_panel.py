"""
图形化控制面板
基于tkinter的简单GUI界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Dict, Any
from loguru import logger

from ..core.ec_controller import ECController
from ..commands.motion import MotionCommands
from ..commands.parameter import ParameterCommands
from ..commands.status import StatusCommands


class ControlPanel:
    """EC电缸控制面板"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化控制面板

        Args:
            config: 配置字典
        """
        self.config = config
        self.controller = ECController(config)
        self.motion = MotionCommands(self.controller)
        self.parameters = ParameterCommands(self.controller)
        self.status = StatusCommands(self.controller)

        self.root = tk.Tk()
        self.root.title("IAI EC电缸控制面板")
        self.root.geometry("800x600")

        self._create_widgets()
        self._layout_widgets()

        # 状态更新
        self.update_timer = None

    def _create_widgets(self):
        """创建控件"""
        # 连接框架
        self.conn_frame = ttk.LabelFrame(self.root, text="连接", padding=10)
        self.ip_label = ttk.Label(self.conn_frame, text="IP地址:")
        self.ip_entry = ttk.Entry(self.conn_frame, width=15)
        self.ip_entry.insert(0, self.config['connection']['ip_address'])
        self.connect_btn = ttk.Button(self.conn_frame, text="连接",
                                      command=self._connect)
        self.disconnect_btn = ttk.Button(self.conn_frame, text="断开",
                                         command=self._disconnect, state='disabled')

        # 状态框架
        self.status_frame = ttk.LabelFrame(self.root, text="状态", padding=10)
        self.pos_label = ttk.Label(self.status_frame, text="当前位置: ---")
        self.alarm_label = ttk.Label(self.status_frame, text="报警状态: ---")
        self.io_text = tk.Text(self.status_frame, height=6, width=30)

        # 运动控制框架
        self.motion_frame = ttk.LabelFrame(self.root, text="运动控制", padding=10)

        # 原点复位
        self.home_btn = ttk.Button(self.motion_frame, text="原点复位",
                                   command=self._home, state='disabled')

        # 位置移动
        self.pos_move_frame = ttk.Frame(self.motion_frame)
        self.target_pos_label = ttk.Label(self.pos_move_frame, text="目标位置:")
        self.target_pos_entry = ttk.Entry(self.pos_move_frame, width=10)
        self.target_pos_entry.insert(0, "0")
        self.speed_label = ttk.Label(self.pos_move_frame, text="速度:")
        self.speed_entry = ttk.Entry(self.pos_move_frame, width=10)
        self.speed_entry.insert(0, "100")
        self.move_btn = ttk.Button(self.pos_move_frame, text="移动",
                                   command=self._move, state='disabled')

        # 点动控制
        self.jog_frame = ttk.Frame(self.motion_frame)
        self.jog_minus_btn = ttk.Button(self.jog_frame, text="◄ 反向",
                                        state='disabled')
        self.jog_minus_btn.bind("<ButtonPress-1>", lambda e: self._jog_start(False))
        self.jog_minus_btn.bind("<ButtonRelease-1>", lambda e: self._jog_stop())

        self.stop_btn = ttk.Button(self.jog_frame, text="停止",
                                   command=self._stop, state='disabled')

        self.jog_plus_btn = ttk.Button(self.jog_frame, text="正向 ►",
                                       state='disabled')
        self.jog_plus_btn.bind("<ButtonPress-1>", lambda e: self._jog_start(True))
        self.jog_plus_btn.bind("<ButtonRelease-1>", lambda e: self._jog_stop())

        # 参数框架
        self.param_frame = ttk.LabelFrame(self.root, text="参数", padding=10)
        self.param_notebook = ttk.Notebook(self.param_frame)

        # 基本参数
        self.basic_param_frame = ttk.Frame(self.param_notebook)
        self.param_notebook.add(self.basic_param_frame, text="基本参数")

        self.motion_range_label = ttk.Label(self.basic_param_frame, text="动作范围:")
        self.motion_range_var = tk.StringVar(value="330")
        self.motion_range_entry = ttk.Entry(self.basic_param_frame,
                                            textvariable=self.motion_range_var,
                                            width=10)

        self.ls_range_label = ttk.Label(self.basic_param_frame, text="LS检测范围:")
        self.ls_range_var = tk.StringVar(value="0.1")
        self.ls_range_entry = ttk.Entry(self.basic_param_frame,
                                        textvariable=self.ls_range_var,
                                        width=10)

        # 高级参数
        self.adv_param_frame = ttk.Frame(self.param_notebook)
        self.param_notebook.add(self.adv_param_frame, text="高级参数")

        self.smooth_var = tk.BooleanVar()
        self.smooth_check = ttk.Checkbutton(self.adv_param_frame,
                                            text="平滑加减速",
                                            variable=self.smooth_var)

        self.power_save_var = tk.BooleanVar()
        self.power_save_check = ttk.Checkbutton(self.adv_param_frame,
                                                text="省电模式",
                                                variable=self.power_save_var)

        self.param_read_btn = ttk.Button(self.param_frame, text="读取参数",
                                         command=self._read_params, state='disabled')
        self.param_write_btn = ttk.Button(self.param_frame, text="写入参数",
                                          command=self._write_params, state='disabled')

        # 日志框架
        self.log_frame = ttk.LabelFrame(self.root, text="日志", padding=10)
        self.log_text = tk.Text(self.log_frame, height=10)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient='vertical',
                                        command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

    def _layout_widgets(self):
        """布局控件"""
        # 连接框架
        self.conn_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.ip_label.grid(row=0, column=0, padx=5)
        self.ip_entry.grid(row=0, column=1, padx=5)
        self.connect_btn.grid(row=0, column=2, padx=5)
        self.disconnect_btn.grid(row=0, column=3, padx=5)

        # 状态框架
        self.status_frame.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.pos_label.grid(row=0, column=0, columnspan=2, sticky='w')
        self.alarm_label.grid(row=1, column=0, columnspan=2, sticky='w')
        self.io_text.grid(row=2, column=0, columnspan=2, pady=5)

        # 运动控制框架
        self.motion_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        self.home_btn.grid(row=0, column=0, padx=5, pady=5)

        self.pos_move_frame.grid(row=1, column=0, columnspan=3, pady=5)
        self.target_pos_label.grid(row=0, column=0)
        self.target_pos_entry.grid(row=0, column=1)
        self.speed_label.grid(row=0, column=2, padx=(10, 0))
        self.speed_entry.grid(row=0, column=3)
        self.move_btn.grid(row=0, column=4, padx=10)

        self.jog_frame.grid(row=2, column=0, columnspan=3, pady=5)
        self.jog_minus_btn.grid(row=0, column=0, padx=5)
        self.stop_btn.grid(row=0, column=1, padx=5)
        self.jog_plus_btn.grid(row=0, column=2, padx=5)

        # 参数框架
        self.param_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        self.param_notebook.grid(row=0, column=0, columnspan=2, pady=5)

        # 基本参数
        self.motion_range_label.grid(row=0, column=0, padx=5, pady=2)
        self.motion_range_entry.grid(row=0, column=1, padx=5, pady=2)
        self.ls_range_label.grid(row=1, column=0, padx=5, pady=2)
        self.ls_range_entry.grid(row=1, column=1, padx=5, pady=2)

        # 高级参数
        self.smooth_check.grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.power_save_check.grid(row=1, column=0, padx=5, pady=2, sticky='w')

        self.param_read_btn.grid(row=1, column=0, padx=5, pady=5)
        self.param_write_btn.grid(row=1, column=1, padx=5, pady=5)

        # 日志框架
        self.log_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')
        self.log_text.grid(row=0, column=0, sticky='nsew')
        self.log_scroll.grid(row=0, column=1, sticky='ns')

        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

    def _connect(self):
        """连接电缸"""
        self.controller.client.ip_address = self.ip_entry.get()

        def connect_thread():
            if self.controller.connect():
                self._log("成功连接到电缸")
                self.root.after(0, self._on_connected)
            else:
                self._log("连接失败", 'error')

        threading.Thread(target=connect_thread, daemon=True).start()

    def _disconnect(self):
        """断开连接"""
        self.controller.disconnect()
        self._on_disconnected()
        self._log("已断开连接")

    def _on_connected(self):
        """连接成功后的处理"""
        # 更新按钮状态
        self.connect_btn.config(state='disabled')
        self.disconnect_btn.config(state='normal')
        self.home_btn.config(state='normal')
        self.move_btn.config(state='normal')
        self.stop_btn.config(state='normal')
        self.jog_plus_btn.config(state='normal')
        self.jog_minus_btn.config(state='normal')
        self.param_read_btn.config(state='normal')
        self.param_write_btn.config(state='normal')

        # 开始状态更新
        self._start_status_update()

    def _on_disconnected(self):
        """断开连接后的处理"""
        # 停止状态更新
        self._stop_status_update()

        # 更新按钮状态
        self.connect_btn.config(state='normal')
        self.disconnect_btn.config(state='disabled')
        self.home_btn.config(state='disabled')
        self.move_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.jog_plus_btn.config(state='disabled')
        self.jog_minus_btn.config(state='disabled')
        self.param_read_btn.config(state='disabled')
        self.param_write_btn.config(state='disabled')

    def _home(self):
        """原点复位"""

        def home_thread():
            self._log("开始原点复位...")
            if self.controller.home():
                self._log("原点复位完成")
            else:
                self._log("原点复位失败", 'error')

        threading.Thread(target=home_thread, daemon=True).start()

    def _move(self):
        """移动到目标位置"""
        try:
            position = float(self.target_pos_entry.get())
            speed = float(self.speed_entry.get())

            def move_thread():
                self._log(f"移动到 {position}度，速度 {speed}度/秒")
                if self.controller.move_to_position(position, speed):
                    self._log("移动完成")
                else:
                    self._log("移动失败", 'error')

            threading.Thread(target=move_thread, daemon=True).start()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")

    def _jog_start(self, forward: bool):
        """开始点动"""
        if forward:
            self.motion.jog_forward()
            self._log("正向点动开始")
        else:
            self.motion.jog_backward()
            self._log("反向点动开始")

    def _jog_stop(self):
        """停止点动"""
        self.motion.stop_jog()
        self._log("点动停止")

    def _stop(self):
        """紧急停止"""
        self.controller.stop()
        self._log("紧急停止", 'warning')

    def _read_params(self):
        """读取参数"""

        def read_thread():
            params = self.parameters.read_all_parameters()

            # 更新界面
            self.root.after(0, lambda: self._update_param_display(params))
            self._log("参数读取完成")

        threading.Thread(target=read_thread, daemon=True).start()

    def _write_params(self):
        """写入参数"""
        if messagebox.askyesno("确认", "写入参数后需要重启控制器，是否继续？"):
            def write_thread():
                # 写入基本参数
                self.parameters.set_motion_range(float(self.motion_range_var.get()))
                self.parameters.set_ls_detection_range(float(self.ls_range_var.get()))

                # 写入高级参数
                self.parameters.set_smooth_motion(self.smooth_var.get())
                self.parameters.set_power_save(self.power_save_var.get())

                self._log("参数写入完成，请重启控制器")

            threading.Thread(target=write_thread, daemon=True).start()

    def _update_param_display(self, params: Dict[str, Any]):
        """更新参数显示"""
        if 'motion_range' in params:
            self.motion_range_var.set(str(params['motion_range']))
        if 'ls_detection_range' in params:
            self.ls_range_var.set(str(params['ls_detection_range']))
        if 'smooth_motion' in params:
            self.smooth_var.set(bool(params['smooth_motion']))
        if 'power_save' in params:
            self.power_save_var.set(bool(params['power_save']))

    def _start_status_update(self):
        """开始状态更新"""

        def update():
            if self.controller.client.connected:
                status = self.controller.get_status()

                # 更新位置
                pos = status.get('position', '---')
                self.pos_label.config(text=f"当前位置: {pos:.2f}度" if pos != '---' else "当前位置: ---")

                # 更新报警
                alarm = status.get('alarm', False)
                self.alarm_label.config(
                    text=f"报警状态: {'有报警' if alarm else '正常'}",
                    foreground='red' if alarm else 'green'
                )

                # 更新I/O状态
                io_status = self.status.get_io_status()
                io_text = "I/O状态:\n"
                for signal, value in io_status.items():
                    io_text += f"{signal}: {'ON' if value else 'OFF'}\n"
                self.io_text.delete(1.0, tk.END)
                self.io_text.insert(1.0, io_text)

                # 继续更新
                self.update_timer = self.root.after(100, update)

        update()

    def _stop_status_update(self):
        """停止状态更新"""
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
            self.update_timer = None

    def _log(self, message: str, level: str = 'info'):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 根据级别设置颜色
        if level == 'error':
            tag = 'error'
            prefix = '[错误]'
        elif level == 'warning':
            tag = 'warning'
            prefix = '[警告]'
        else:
            tag = 'info'
            prefix = '[信息]'

        # 插入日志
        self.log_text.insert(tk.END, f"{timestamp} {prefix} {message}\n")
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('info', foreground='black')

        # 滚动到底部
        self.log_text.see(tk.END)

        # 同时记录到文件
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

    def run(self):
        """运行GUI"""
        self.root.mainloop()