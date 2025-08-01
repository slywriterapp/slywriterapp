# tab_stats.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import config
import typing_engine as engine

class StatsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text='Typing Diagnostics', font=('Segoe UI',11))\
            .pack(anchor='w', padx=10, pady=(10,0))

        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.txt = tk.Text(frame, height=10, wrap='none')
        sb = ttk.Scrollbar(frame, orient='vertical', command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        self.txt.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        try:
            with open(config.LOG_FILE, 'r', encoding='utf-8') as logf:
                lines = logf.readlines()
            display = f"Total sessions: {len(lines)}\n\nLast 5 entries:\n{''.join(lines[-5:])}"
            self.txt.insert('1.0', display)
        except FileNotFoundError:
            self.txt.insert('1.0', 'No log file found yet.')

        self.txt.configure(state='disabled')

        ttk.Button(self, text='Export CSV', command=self.export_csv)\
            .pack(pady=(5,10))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path:
            return
        try:
            with open(config.LOG_FILE, 'r', encoding='utf-8') as src, \
                 open(path, 'w', newline='', encoding='utf-8') as dst:
                writer = csv.writer(dst)
                writer.writerow(['timestamp','text'])
                for line in src:
                    parts = line.strip().split('] ',1)
                    if len(parts)==2:
                        writer.writerow([parts[0].lstrip('['), parts[1]])
            messagebox.showinfo('Exported', f'Log exported to {path}')
        except FileNotFoundError:
            messagebox.showwarning('Error', 'No log file to export.')
