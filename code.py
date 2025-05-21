import json
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, filedialog

# Constants
DATA_FILE = "study_timer_data.json"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
IDLE_THRESHOLD = 300  # 5 minutes in seconds

class StudyTimer:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.load_data()
        self.last_activity_time = datetime.now()
        self.check_idle()
        self.update_timer()

    def setup_ui(self):
        self.root.title("Study Timer Pro")
        self.root.geometry("500x450")
        self.root.minsize(400, 400)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Timer display
        self.timer_label = ttk.Label(
            main_frame, 
            text="00:00:00", 
            font=("Helvetica", 48, "bold"),
            foreground="#2c3e50"
        )
        self.timer_label.pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10, fill=tk.X)
        
        self.start_button = ttk.Button(btn_frame, text="Start", command=self.start_timer)
        self.pause_button = ttk.Button(btn_frame, text="Pause", command=self.pause_timer, state=tk.DISABLED)
        self.reset_button = ttk.Button(btn_frame, text="Reset", command=self.reset_timer)
        
        for btn in [self.start_button, self.pause_button, self.reset_button]:
            btn.pack(side=tk.LEFT, expand=True, padx=5)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.session_label = ttk.Label(stats_frame, text="Session: 00:00:00")
        self.today_label = ttk.Label(stats_frame, text="Today: 00:00:00")
        self.total_label = ttk.Label(stats_frame, text="Total: 00:00:00")
        self.credit_label = ttk.Label(stats_frame, text="Powered by Nineyxl", foreground="gray")
        
        for lbl in [self.session_label, self.today_label, self.total_label, self.credit_label]:
            lbl.pack(anchor=tk.W)
        
        self.setup_menu()
        self.root.bind("<Motion>", self.record_activity)
        self.root.bind("<Key>", self.record_activity)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Session History", command=self.show_history)
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menubar)

    def load_data(self):
        default_data = {
            "total_seconds": 0,
            "today_seconds": 0,
            "sessions": [],
            "last_session": {"start_time": None, "paused_time": None, "accumulated_seconds": 0}
        }
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    self.data = json.load(f)
                    # Ensure all keys exist
                    for key in default_data:
                        if key not in self.data:
                            self.data[key] = default_data[key]
                    # Ensure sessions is a list
                    if not isinstance(self.data["sessions"], list):
                        self.data["sessions"] = []
                    # Ensure last_session keys exist
                    for k in default_data["last_session"]:
                        if k not in self.data["last_session"]:
                            self.data["last_session"][k] = default_data["last_session"][k]
                    # Convert timestamps back to datetime objects
                    for k in ["start_time", "paused_time"]:
                        if self.data["last_session"][k]:
                            self.data["last_session"][k] = datetime.strptime(self.data["last_session"][k], DATE_FORMAT)
            else:
                self.data = default_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.data = default_data
            
        self.check_new_day()
        self.running = False
        self.accumulated_seconds = self.data["last_session"]["accumulated_seconds"]

    def save_data(self):
        try:
            save_data = {
                "total_seconds": self.data["total_seconds"],
                "today_seconds": self.data["today_seconds"],
                "sessions": self.data["sessions"],
                "last_session": {
                    "start_time": self.start_time.strftime(DATE_FORMAT) if hasattr(self, 'start_time') and self.start_time else None,
                    "paused_time": self.paused_time.strftime(DATE_FORMAT) if hasattr(self, 'paused_time') and self.paused_time else None,
                    "accumulated_seconds": self.accumulated_seconds
                }
            }
            with open(DATA_FILE, "w") as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def check_new_day(self):
        today = datetime.now().date()
        last_date = None
        
        if self.data["last_session"]["start_time"]:
            last_date = self.data["last_session"]["start_time"].date()
        elif self.data["last_session"]["paused_time"]:
            last_date = self.data["last_session"]["paused_time"].date()
        
        if last_date and last_date < today:
            self.data["today_seconds"] = 0

    def record_activity(self, event=None):
        self.last_activity_time = datetime.now()

    def check_idle(self):
        if self.running and (datetime.now() - self.last_activity_time).total_seconds() > IDLE_THRESHOLD:
            self.pause_timer()
            messagebox.showwarning("Idle Detected", "Timer paused due to inactivity")
        self.root.after(10000, self.check_idle)

    def start_timer(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            
            if hasattr(self, 'paused_time') and self.paused_time:
                pause_duration = (datetime.now() - self.paused_time).total_seconds()
                self.start_time = datetime.now() - timedelta(seconds=self.accumulated_seconds + pause_duration)
                self.paused_time = None
            else:
                self.start_time = datetime.now()

    def pause_timer(self):
        if self.running:
            self.running = False
            self.pause_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.paused_time = datetime.now()
            if self.start_time is not None and self.paused_time is not None:
                self.accumulated_seconds = (self.paused_time - self.start_time).total_seconds()
            else:
                self.accumulated_seconds = 0

    def reset_timer(self):
        if not self.running and self.accumulated_seconds > 0:
            # Ensure sessions is a list before appending
            if "sessions" not in self.data or not isinstance(self.data["sessions"], list):
                self.data["sessions"] = []
            self.data["sessions"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "duration": self.accumulated_seconds,
                "start_time": self.start_time.strftime(DATE_FORMAT) if hasattr(self, 'start_time') and self.start_time else None,
                "end_time": datetime.now().strftime(DATE_FORMAT)
            })
            
            self.running = False
            self.start_time = None
            self.paused_time = None
            self.accumulated_seconds = 0
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def update_timer(self):
        elapsed = self.accumulated_seconds
        if self.running and hasattr(self, 'start_time') and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.accumulated_seconds = elapsed
        
        today_seconds = self.data["today_seconds"] + (elapsed if self.running else 0)
        total_seconds = self.data["total_seconds"] + (elapsed if self.running else 0)
        
        self.timer_label.config(text=self.format_time(elapsed))
        self.session_label.config(text=f"Session: {self.format_time(elapsed)}")
        self.today_label.config(text=f"Today: {self.format_time(today_seconds)}")
        self.total_label.config(text=f"Total: {self.format_time(total_seconds)}")
        self.root.after(1000, self.update_timer)

    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def export_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="study_timer_export.json"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.data, f, indent=2)
                messagebox.showinfo("Success", "Data exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Session History")
        history_window.geometry("600x400")
        
        tree = ttk.Treeview(history_window, columns=("date", "duration", "start", "end"), show="headings")
        for col in ["date", "duration", "start", "end"]:
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=150 if col in ["start", "end"] else 100)
        
        for session in reversed(self.data.get("sessions", [])):
            tree.insert("", tk.END, values=(
                session.get("date", ""),
                self.format_time(session.get("duration", 0)),
                session.get("start_time", ""),
                session.get("end_time", "")
            ))
        
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_close(self):
        if self.running and hasattr(self, 'start_time') and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.data["total_seconds"] += elapsed
            self.data["today_seconds"] += elapsed
        elif hasattr(self, 'paused_time') and self.paused_time:
            self.data["total_seconds"] += self.accumulated_seconds
            self.data["today_seconds"] += self.accumulated_seconds
        
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyTimer(root)
    root.mainloop()
