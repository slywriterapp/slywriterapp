# tab_schedule.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ScheduleTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Schedule a typing task:", font=("Segoe UI", 11))\
            .pack(anchor="w", padx=10, pady=(10, 0))

        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=10, pady=5)
        ttk.Label(frm, text="Date (YYYY-MM-DD):", font=("Segoe UI", 10))\
            .grid(row=0, column=0, sticky="w")
        self.date_ent = tk.Entry(frm)
        self.date_ent.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(frm, text="Time (HH:MM):", font=("Segoe UI", 10))\
            .grid(row=1, column=0, sticky="w")
        self.time_ent = tk.Entry(frm)
        self.time_ent.grid(row=1, column=1, sticky="ew", padx=5)

        ttk.Button(frm, text="Add Task", command=self.add_schedule)\
            .grid(row=2, column=0, columnspan=2, pady=8)
        frm.columnconfigure(1, weight=1)

        self.task_list = tk.Listbox(self, height=5)
        self.task_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for entry in self.app.cfg["settings"].get("schedule", []):
            self.task_list.insert("end", f"{entry['date']} {entry['time']}")

    def add_schedule(self):
        date_str = self.date_ent.get().strip()
        time_str = self.time_ent.get().strip()
        try:
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return messagebox.showwarning("Invalid", "Enter a valid date and time.")
        self.app.cfg["settings"].setdefault("schedule", []).append({
            "date": date_str,
            "time": time_str
        })
        self.app.save_config()
        self.task_list.insert("end", f"{date_str} {time_str}")
        self.date_ent.delete(0, "end")
        self.time_ent.delete(0, "end")
