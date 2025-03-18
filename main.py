import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import subprocess
import os
import sys
import ctypes
import win32con
import win32gui
import win32process
import pystray
from PIL import Image, ImageDraw
import threading
import shutil
import psutil
import atexit

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(argv=None, debug=False):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        return True

    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        arguments = map(str, argv[1:])
    else:
        arguments = map(str, argv)
    argument_line = u' '.join(arguments)
    executable = str(sys.executable)
    if debug:
        print('Command line: ', executable, argument_line)
    ret = shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
    if int(ret) <= 32:
        return False
    return None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def hide_console(window_title):
    def enum_windows_callback(hwnd, pid):
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                return False
        return True

    win32gui.EnumWindows(enum_windows_callback, os.getpid())

def safe_remove_directory(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not remove directory {path}: {str(e)}")

class NetworkBypassTool:
    def __init__(self, master):
        self.master = master
        master.title("w/e v0.0.2")
        master.geometry("400x600")
        master.configure(bg='#1e1e1e')
        master.resizable(False, False)
        icon = tk.PhotoImage(file=resource_path("ico.png"))
        master.iconphoto(False, icon)
        
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.main_frame = tk.Frame(master, bg='#1e1e1e')
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        title_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        title_frame.pack(fill='x', pady=20, padx=20)
        
        title_label = tk.Label(
            title_frame, 
            text="w/e v0.0.2", 
            font=("Helvetica", 24, "bold"),
            fg='#ffffff',
            bg='#1e1e1e'
        )
        title_label.pack(side='left')
        
        by_label = tk.Label(
            title_frame,
            text="by Tevasu",
            font=("Helvetica", 12),
            fg='#ffffff',
            bg='#1e1e1e'
        )
        by_label.pack(side='right')
        
        self.status_label = tk.Label(
            self.main_frame,
            text="Status: Disabled",
            font=("Helvetica", 12),
            fg='#ff0000',
            bg='#1e1e1e'
        )
        self.status_label.pack(pady=10)
        
        button_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        button_frame.pack(expand=True, fill='both', padx=40)
        
        button_style = {
            'font': ('Helvetica', 14),
            'bg': '#333333',
            'fg': '#ffffff',
            'activebackground': '#4a4a4a',
            'activeforeground': '#ffffff',
            'relief': 'flat',
            'borderwidth': 0,
            'highlightthickness': 0,
            'pady': 10
        }
        
        self.discord_button = tk.Button(
            button_frame,
            text="Only Discord",
            command=self.run_discord_network,
            **button_style
        )
        self.discord_button.pack(fill='x', pady=10)
        
        self.bypass_button = tk.Button(
            button_frame,
            text="Bypass All",
            command=self.bypass_all,
            **button_style
        )
        self.bypass_button.pack(fill='x', pady=10)
        
        self.off_button = tk.Button(
            button_frame,
            text="Disconnect",
            command=self.disable_and_exit,
            **button_style
        )
        self.off_button.pack(fill='x', pady=10)
        
        self.sites_label = tk.Label(
            self.main_frame,
            text="Unblocked sites:",
            font=("Helvetica", 12),
            fg='#ffffff',
            bg='#1e1e1e'
        )
        self.sites_label.pack(pady=(20, 5))
        
        self.sites_text = scrolledtext.ScrolledText(
            self.main_frame,
            width=40,
            height=5,
            font=("Helvetica", 10),
            bg='#2e2e2e',
            fg='#ffffff'
        )
        self.sites_text.pack(pady=5)
        
        self.load_sites()
        
        self.add_site_button = tk.Button(
            self.main_frame,
            text="Add Site",
            command=self.add_site,
            **button_style
        )
        self.add_site_button.pack(pady=10)
        
        self.telegram_label = tk.Label(
            self.main_frame,
            text="t.me/tevasu",
            font=("Helvetica", 10),
            fg='#aaaaaa',
            bg='#1e1e1e',
            cursor="hand2"
        )
        self.telegram_label.pack(side='bottom', pady=10)
        self.telegram_label.bind("<Button-1>", lambda e: self.open_telegram())
        
        self.processes = []
        self.create_tray_icon()
        self.icon.visible = False
        
        atexit.register(self.cleanup)

    def create_tray_icon(self):
        try:
            image = Image.open(resource_path("ico.png"))
        except FileNotFoundError:
            print("Warning: ico.png not found. Creating a simple icon.")
            image = Image.new('RGB', (64, 64), color='#1e1e1e')
            d = ImageDraw.Draw(image)
            d.rectangle([20, 20, 44, 44], fill='#ffffff')
        
        menu = pystray.Menu(
            pystray.MenuItem("Открыть", self.show_window),
            pystray.MenuItem("Закрыть", self.exit_application)
        )
        self.icon = pystray.Icon("name", image, "w/e tools", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self):
        self.master.deiconify()
        self.icon.visible = False

    def hide_window(self):
        self.master.withdraw()
        self.icon.visible = True

    def on_closing(self):
        self.hide_window()

    def exit_application(self):
        self.cleanup()
        self.master.quit()
        sys.exit(0)

    def run_command(self, command, window_title):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        try:
            process = subprocess.Popen(command, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            self.processes.append(process)
            self.master.after(100, lambda: hide_console(window_title))
            return process
        except Exception as e:
            print(f"Failed to run command: {str(e)}")
            return None

    def run_discord_network(self):
        if not is_admin():
            print("This operation requires administrator privileges. The application will restart with elevated permissions.")
            run_as_admin()
            self.master.quit()
            return

        bin_path = resource_path("bin")
        
        if not os.path.exists(os.path.join(bin_path, "we_tool.exe")):
            print("File we_tool.exe not found!")
            return

        self.run_command([os.path.join(bin_path, "we_tool.exe")], "we_tool")
        self.master.after(2000, self.run_we_tool_discord)

    def run_we_tool_discord(self):
        bin_path = resource_path("bin")

        if not os.path.exists(os.path.join(bin_path, "we_tool.exe")):
            print("File we_tool.exe not found!")
            return

        command = [
            os.path.join(bin_path, "we_tool.exe"),
            "--wf-tcp=443", "--wf-udp=443,50000-50100",
            "--filter-udp=443", f"--hostlist={resource_path('list-discord.txt')}", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            f"--dpi-desync-fake-quic={os.path.join(bin_path, 'quic_initial_www_google_com.bin')}", "--new",
            "--filter-udp=50000-50100", f"--ipset={resource_path('ipset-discord.txt')}", "--dpi-desync=fake",
            "--dpi-desync-any-protocol", "--dpi-desync-cutoff=d3", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=443", f"--hostlist={resource_path('list-discord.txt')}", "--dpi-desync=fake,split",
            "--dpi-desync-autottl=2", "--dpi-desync-repeats=6", "--dpi-desync-fooling=badseq",
            f"--dpi-desync-fake-tls={os.path.join(bin_path, 'tls_clienthello_www_google_com.bin')}"
        ]
        
        self.process = self.run_command(command, "zapret: discord")
        if self.process:
            self.hide_window()
            self.status_label.config(text="Status: Activated", fg='#00ff00')

    def bypass_all(self):
        if not is_admin():
            print("This operation requires administrator privileges. The application will restart with elevated permissions.")
            run_as_admin()
            self.master.quit()
            return

        bin_path = resource_path("bin")
        
        if not os.path.exists(os.path.join(bin_path, "we_tool.exe")):
            print("File we_tool.exe not found!")
            return

        self.run_command([os.path.join(bin_path, "we_tool.exe")], "we_tool")
        self.master.after(2000, self.run_we_tool_all)

    def run_we_tool_all(self):
        bin_path = resource_path("bin")

        if not os.path.exists(os.path.join(bin_path, "we_tool.exe")):
            print("File we_tool.exe not found!")
            return

        command = [
            os.path.join(bin_path, "we_tool.exe"),
            "--wf-tcp=80,443", "--wf-udp=443,50000-50100",
            "--filter-udp=443", f"--hostlist={resource_path('list-general.txt')}", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            f"--dpi-desync-fake-quic={os.path.join(bin_path, 'quic_initial_www_google_com.bin')}", "--new",
            "--filter-udp=50000-50100", f"--ipset={resource_path('ipset-discord.txt')}", "--dpi-desync=fake",
            "--dpi-desync-any-protocol", "--dpi-desync-cutoff=d3", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=80", f"--hostlist={resource_path('list-general.txt')}", "--dpi-desync=fake,split2",
            "--dpi-desync-autottl=2", "--dpi-desync-fooling=md5sig", "--new",
            "--filter-tcp=443", f"--hostlist={resource_path('list-general.txt')}", "--dpi-desync=fake",
            "--dpi-desync-repeats=6", "--dpi-desync-fooling=md5sig",
            f"--dpi-desync-fake-tls={os.path.join(bin_path, 'tls_clienthello_www_google_com.bin')}"
        ]
        
        self.process = self.run_command(command, "zapret: general")
        if self.process:
            self.hide_window()
            self.status_label.config(text="Status: Activated", fg='#00ff00')

    def disable_network(self):
        for process in self.processes:
            try:
                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.terminate()
                parent.terminate()
            except psutil.NoSuchProcess:
                pass
        self.processes = []

        # Clean up any temporary directories
        temp_dir = os.environ.get('TEMP', os.path.expanduser('~'))
        for item in os.listdir(temp_dir):
            if item.startswith('_MEI'):
                safe_remove_directory(os.path.join(temp_dir, item))

        bin_path = resource_path("bin")
        if os.path.exists(os.path.join(bin_path, "we_tool.exe")):
            process = self.run_command([os.path.join(bin_path, "we_tool.exe"), "--clean"], "we_tool clean")
            if process:
                print("Network operations have been stopped and changes removed.")
                self.status_label.config(text="Status: Disabled", fg='#ff0000')
        else:
            print("we_tool.exe not found. Unable to clean up changes.")

    def disable_and_exit(self):
        self.disable_network()
        self.exit_application()

    def load_sites(self):
        try:
            with open(resource_path('list-general.txt'), 'r') as f:
                sites = f.read()
            self.sites_text.delete('1.0', tk.END)
            self.sites_text.insert(tk.END, sites)
        except FileNotFoundError:
            print("list-general.txt not found!")

    def add_site(self):
        new_site = simpledialog.askstring("W/E Tool", "Enter the site to unblock:")
        if new_site:
            with open(resource_path('list-general.txt'), 'a') as f:
                f.write(f"\n{new_site}")
            self.load_sites()
            messagebox.showinfo("Site Added", f"The site '{new_site}' has been added to the list.")

    def open_telegram(self):
        import webbrowser
        webbrowser.open("https://t.me/tevasu")

    def cleanup(self):
        self.disable_network()
        if self.icon:
            self.icon.stop()
        self.execute_cleanup_commands()

    def execute_cleanup_commands(self):
        try:
            subprocess.run(["sc", "stop", "WinDivert"], check=True)
            subprocess.run(["sc", "delete", "WinDivert"], check=True)
            print("Successfully executed cleanup commands.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing cleanup commands: {e}")

def hide_console_window():
    kernel32 = ctypes.WinDLL('kernel32')
    user32 = ctypes.WinDLL('user32')
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 0)

def main():
    hide_console_window()
    if not is_admin():
        if run_as_admin() is None:
            sys.exit()
    root = tk.Tk()
    app = NetworkBypassTool(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_application)
    root.mainloop()

if __name__ == "__main__":
    main()