import sys
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pyautogui
from pynput import keyboard
import threading
import winsound

# -------------------- 资源路径处理 --------------------
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

# -------------------- 声音文件路径 --------------------
START_SOUND = resource_path(os.path.join("声音文件", "按键开启.wav"))
STOP_SOUND = resource_path(os.path.join("声音文件", "按键关闭.wav"))

# -------------------- 配置与全局变量 --------------------
DEFAULT_INTERVAL = 60  # 默认间隔（毫秒）
custom_keys = []  # 存储结构：[{"key": "a", "var": BooleanVar, "frame": 行容器}]
is_running = False  # 运行状态
start_key = "f1"    # 启动键（F1）
stop_key = "f2"     # 停止键（F2）
interval = DEFAULT_INTERVAL  # 按键间隔
sound_enabled = True  # 声音开关（核心控制变量）


def play_sound(sound_path):
    """播放声音（严格检查声音开关）"""
    # 只有当声音开关开启、文件存在且是WAV格式时才播放
    if (sound_enabled 
        and os.path.exists(sound_path) 
        and sound_path.lower().endswith(".wav")):
        try:
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            status_label.config(text="声音播放失败", foreground="#e74c3c")
    # 若关闭了声音开关，直接显示状态（不播放）
    elif not sound_enabled:
        status_label.config(text="声音已关闭", foreground="#95a5a6")


def add_custom_key():
    """添加带复选框的自定义按键"""
    key = simpledialog.askstring(
        "添加按键", 
        "支持：\n"
        "- 字母（大小写均可，自动转小写）\n"
        "- 功能键（如 f1、space，需用英文小写）\n"
        "- 符号（如 `、-、= 等）"
    )
    if not key:
        return
    
    key = key.strip().lower()
    is_valid = False
    try:
        pyautogui.press(key)
        is_valid = True
    except:
        if len(key) == 1 and key.isalpha():
            is_valid = True
    
    if is_valid:
        var = tk.BooleanVar(value=True)
        frame = tk.Frame(keys_frame, bg="#f5f5f5", bd=1, relief=tk.SOLID, highlightbackground="#ddd")
        frame.pack(fill=tk.X, padx=10, pady=3)
        frame.bind("<Button-1>", lambda e: frame.focus_set())
        
        cb = ttk.Checkbutton(frame, variable=var)
        cb.pack(side=tk.LEFT, padx=10, pady=5)
        
        lbl = ttk.Label(frame, text=key, font=("微软雅黑", 10))
        lbl.pack(side=tk.LEFT, pady=5)
        
        custom_keys.append({"key": key, "var": var, "frame": frame})
        status_label.config(text=f"已添加按键: {key}", foreground="#2c3e50")
    else:
        messagebox.showerror(
            "无效按键", 
            f"无法识别：{key}\n\n"
            "✅ 正确示例：a（大写A自动转a）、f1、space\n"
            "❌ 错误示例：Fg（应为f1）、@（需用对应名称）"
        )


def delete_custom_key():
    """删除选中的自定义按键"""
    for idx, item in enumerate(custom_keys):
        if item["frame"].winfo_ismapped() and item["frame"] == root.focus_get():
            item["frame"].config(bg="#ffebee")
            root.update()
            root.after(200)
            item["frame"].destroy()
            del custom_keys[idx]
            status_label.config(text=f"已删除按键: {item['key']}", foreground="#e74c3c")
            return
    messagebox.showerror("错误", "请先点击要删除的按键行！")


def apply_settings():
    """应用配置（确保声音开关状态正确同步）"""
    global start_key, stop_key, interval, sound_enabled
    try:
        start_key = start_key_var.get().lower()
        stop_key = stop_key_var.get().lower()
        interval = int(interval_var.get())
        # 关键：将复选框状态同步到全局变量
        sound_enabled = sound_var.get()
        
        status_label.config(text="设置已生效！", foreground="#27ae60")
        root.after(1000, lambda: status_label.config(
            text=f"启动键: {start_key} | 停止键: {stop_key} | 间隔: {interval}ms | 声音: {'开启' if sound_enabled else '关闭'}", 
            foreground="#2c3e50"
        ))
    except ValueError:
        messagebox.showerror("错误", "间隔必须为数字！")


def simulate_keys():
    """后台线程：发送勾选的按键"""
    global is_running
    while is_running:
        for item in custom_keys:
            if item["var"].get():
                try:
                    pyautogui.press(item["key"])
                    status_label.config(text=f"已发送: {item['key']}", foreground="#3498db")
                except:
                    status_label.config(text=f"无效按键跳过: {item['key']}", foreground="#e74c3c")
        pyautogui.sleep(interval / 1000)


def on_key_press(key):
    """监听启动/停止键"""
    global is_running
    key_name = getattr(key, "name", getattr(key, "char", None))
    
    if key_name == start_key and not is_running:
        is_running = True
        threading.Thread(target=simulate_keys, daemon=True).start()
        # 启动时播放声音（受开关控制）
        play_sound(START_SOUND)
        status_label.config(text=f"已启动（{start_key}），按{stop_key}停止", foreground="#27ae60")
        root.config(bg="#f0fdf4")
        root.after(300, lambda: root.config(bg="#ffffff"))
        
    elif key_name == stop_key and is_running:
        is_running = False
        # 停止时播放声音（受开关控制）
        play_sound(STOP_SOUND)
        status_label.config(text=f"已停止（{stop_key}），按{start_key}启动", foreground="#e74c3c")
        root.config(bg="#fff5f5")
        root.after(300, lambda: root.config(bg="#ffffff"))


# -------------------- GUI 界面构建 --------------------
root = tk.Tk()
root.title("智能按键模拟工具")
root.geometry("680x580")  # 加宽窗口以显示完整状态
root.resizable(False, False)
root.config(bg="#ffffff")

# 设置ttk主题和样式
style = ttk.Style()
style.theme_use('clam')

style.configure("TLabel", font=("微软雅黑", 10), background="#ffffff", foreground="#2c3e50")
style.configure("TButton", font=("微软雅黑", 10), padding=5)
style.configure("TCombobox", font=("微软雅黑", 10), padding=3)
style.configure("TCheckbutton", font=("微软雅黑", 10), background="#ffffff")
style.configure("TLabelframe", font=("微软雅黑", 10, "bold"), background="#ffffff")
style.configure("TLabelframe.Label", foreground="#34495e")

# 标题区域
title_frame = tk.Frame(root, bg="#3498db", height=60)
title_frame.pack(fill=tk.X)
title_frame.pack_propagate(False)

title_label = ttk.Label(
    title_frame, 
    text="智能按键模拟工具", 
    font=("微软雅黑", 16, "bold"),
    foreground="#ffffff",
    background="#3498db"
)
title_label.pack(pady=15)

# 1. 自定义按键区域
keys_label = ttk.Label(
    root, 
    text="自定义按键列表（勾选生效）", 
    font=("微软雅黑", 11, "bold"),
    foreground="#34495e"
)
keys_label.pack(anchor=tk.W, padx=30, pady=(20, 5))

keys_container = ttk.LabelFrame(root, text="按键列表", padding=10)
keys_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

keys_frame = tk.Frame(keys_container, bg="#ffffff")
keys_frame.pack(fill=tk.BOTH, expand=True)

# 2. 操作按钮区域
btn_frame = tk.Frame(root, bg="#ffffff")
btn_frame.pack(pady=10)

add_btn = ttk.Button(btn_frame, text="添加按键", command=add_custom_key, width=12)
add_btn.pack(side=tk.LEFT, padx=10)

del_btn = ttk.Button(btn_frame, text="删除按键", command=delete_custom_key, width=12)
del_btn.pack(side=tk.LEFT, padx=10)

# 3. 核心配置区域
config_label = ttk.Label(
    root, 
    text="参数配置", 
    font=("微软雅黑", 11, "bold"),
    foreground="#34495e"
)
config_label.pack(anchor=tk.W, padx=30, pady=(15, 5))

config_container = ttk.LabelFrame(root, text="设置", padding=15)
config_container.pack(fill=tk.X, padx=30, pady=5)

config_container.columnconfigure(1, weight=1)
config_container.columnconfigure(3, weight=1)

# 启动键
ttk.Label(config_container, text="启动键：").grid(row=0, column=0, sticky=tk.W, pady=8, padx=(5, 10))
start_key_var = tk.StringVar(value=start_key)
start_combobox = ttk.Combobox(
    config_container,
    textvariable=start_key_var,
    values=["f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12",
            "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",
            "`","1","2","3","4","5","6","7","8","9","0","-","=",
            "space","enter","escape","tab","backspace","ctrl","alt","shift"],
    width=15
)
start_combobox.grid(row=0, column=1, sticky=tk.W, pady=8)

# 停止键
ttk.Label(config_container, text="停止键：").grid(row=0, column=2, sticky=tk.W, pady=8, padx=(20, 10))
stop_key_var = tk.StringVar(value=stop_key)
stop_combobox = ttk.Combobox(
    config_container,
    textvariable=stop_key_var,
    values=start_combobox["values"],
    width=15
)
stop_combobox.grid(row=0, column=3, sticky=tk.W, pady=8)

# 按键间隔
ttk.Label(config_container, text="间隔(ms)：").grid(row=1, column=0, sticky=tk.W, pady=8, padx=(5, 10))
interval_var = tk.StringVar(value=str(interval))
interval_entry = ttk.Entry(config_container, textvariable=interval_var, width=15)
interval_entry.grid(row=1, column=1, sticky=tk.W, pady=8)

# 声音开关（核心控件）
sound_var = tk.BooleanVar(value=sound_enabled)
sound_checkbox = ttk.Checkbutton(
    config_container,
    text="启用声音提醒",
    variable=sound_var
)
sound_checkbox.grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=10, pady=8)

# 应用按钮
apply_btn = ttk.Button(root, text="应用设置", command=apply_settings, width=20)
apply_btn.pack(pady=15)

# 状态提示区域（显示声音开关状态）
status_frame = tk.Frame(root, bg="#f8f9fa", height=35, bd=1, relief=tk.SUNKEN)
status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
status_frame.pack_propagate(False)

status_label = ttk.Label(
    status_frame, 
    text=f"状态：就绪 - 按{start_key}启动 | 声音: 开启", 
    font=("微软雅黑", 10),
    foreground="#2c3e50",
    background="#f8f9fa"
)
status_label.pack(side=tk.LEFT, padx=20, pady=7)

# -------------------- 启动键盘监听 --------------------
key_listener = keyboard.Listener(on_press=on_key_press)
key_listener.start()

root.mainloop()
    