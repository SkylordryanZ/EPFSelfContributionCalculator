import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading
import urllib.request
import json
import sys
import csv
import os
import shutil
import uuid
import subprocess

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculator import calculate_epf, load_data, save_data, calculate_tax_2025, get_relief_categories, RECEIPTS_DIR

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Dynamic Material Colors (Light, Dark) ---
BG_COLOR = ("#F5F5F5", "#121212")
SURFACE_COLOR = ("#FFFFFF", "#1E1E1E")
PRIMARY_COLOR = ("#6200EE", "#BB86FC")  
PRIMARY_HOVER = ("#3700B3", "#9a67ea")
SECONDARY_COLOR = ("#018786", "#03DAC6")
ERROR_COLOR = ("#B00020", "#CF6679")
TEXT_COLOR = ("#000000", "#FFFFFF")

APP_VERSION = "1.0.5"
GITHUB_REPO = "SkylordryanZ/EPFSelfContributionCalculator"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # load persistent data
        self.user_data = load_data()

        # Window configuration
        self.title(f"EPF Self-Contribution Calculator v{APP_VERSION}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG_COLOR)

        # configure grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Handle the window close event to ensure a clean exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # create sidebar frame with navigation buttons
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=SURFACE_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="EPF Self-Contrib", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.add_record_btn = ctk.CTkButton(self.sidebar_frame, text="Add Record", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_add_record_frame)
        self.add_record_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.view_history_btn = ctk.CTkButton(self.sidebar_frame, text="View History", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_history_frame)
        self.view_history_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.dividend_btn = ctk.CTkButton(self.sidebar_frame, text="EPF Dividend", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_dividend_frame)
        self.dividend_btn.grid(row=3, column=0, padx=20, pady=10)
        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="Settings", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_settings_frame)
        self.settings_btn.grid(row=4, column=0, padx=20, pady=10)
        
        self.tax_btn = ctk.CTkButton(self.sidebar_frame, text="Tax Calculation", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_tax_frame)
        self.tax_btn.grid(row=5, column=0, padx=20, pady=10)
        
        self.receipt_btn = ctk.CTkButton(self.sidebar_frame, text="Receipt Manager", fg_color="transparent", hover_color=SURFACE_COLOR, text_color=PRIMARY_COLOR, command=self.show_receipt_frame)
        self.receipt_btn.grid(row=6, column=0, padx=20, pady=10)

        # Hidden by default until an update is downloaded
        self.restart_update_btn = ctk.CTkButton(self.sidebar_frame, text="↻ Restart to Update", fg_color=SECONDARY_COLOR, hover_color=SECONDARY_COLOR[0], text_color=TEXT_COLOR, command=self.apply_update)

        # create main frame areas
        self.add_record_frame = AddRecordFrame(self, self.user_data, self.update_data_callback)
        self.history_frame = HistoryFrame(self, self.user_data, self.update_data_callback)
        self.dividend_frame = DividendFrame(self, self.user_data)
        self.settings_frame = SettingsFrame(self)
        self.tax_frame = TaxFrame(self, self.user_data)
        self.receipt_frame = ReceiptFrame(self, self.user_data, self.update_data_callback)
        
        # Initialize default view
        self.show_add_record_frame()
        
        # Check for updates in the background
        threading.Thread(target=self.run_update_check, args=(False,), daemon=True).start()

    def run_update_check(self, is_manual=False):
        if is_manual and hasattr(self, 'settings_frame'):
            self.settings_frame.update_btn.configure(text="Checking...", state="disabled")
            self.update_idletasks()
            
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").lstrip("v")
                current_version = APP_VERSION.lstrip("v")
                
                # Check if we should update
                if latest_version and latest_version != current_version:
                    # Look for an .exe asset in the release
                    download_url = None
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe"):
                            download_url = asset.get("browser_download_url")
                            break
                            
                    if download_url:
                        # Automatically download and install
                        if is_manual:
                            self.after(500, lambda: messagebox.showinfo("Update Available", f"A new version (v{latest_version}) was found and is downloading in the background."))
                            
                        threading.Thread(target=self.execute_update, args=(download_url,), daemon=True).start()
                    else:
                        # Fallback if no .exe is attached to the release
                        msg = (f"A new version (v{latest_version}) is available!\n\n"
                               f"Please visit https://github.com/{GITHUB_REPO}/releases to download it.")
                        if is_manual:
                            self.settings_frame.update_btn.configure(text="Check for Updates", state="normal")
                        self.after(500, lambda: messagebox.showinfo("Update Available", msg))
                        
                elif is_manual:
                    self.settings_frame.update_btn.configure(text="Check for Updates", state="normal")
                    self.after(500, lambda: messagebox.showinfo("Up to Date", f"You are already running the latest version (v{current_version})."))
                    
        except Exception as e:
            print(f"Update check failed: {e}")
            if is_manual:
                self.settings_frame.update_btn.configure(text="Check for Updates", state="normal")
                self.after(500, lambda: messagebox.showerror("Update Error", f"Failed to check for updates.\n{e}"))

    def execute_update(self, download_url):
        if hasattr(self, 'settings_frame'):
            self.settings_frame.update_btn.configure(text="Downloading...", state="disabled")
            
        try:
            self.new_exe_name = "EPFSelfContributionCalc_update.exe"
            urllib.request.urlretrieve(download_url, self.new_exe_name)
            
            # Show restart button on sidebar once download is complete
            self.after(0, self.show_restart_button)
            
        except Exception as e:
            msg = f"Failed to download update.\n{e}"
            self.after(500, lambda: messagebox.showerror("Download Error", msg))
            if hasattr(self, 'settings_frame'):
                self.settings_frame.update_btn.configure(text="Check for Updates", state="normal")

    def show_restart_button(self):
        self.restart_update_btn.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="s")
        if hasattr(self, 'settings_frame'):
            self.settings_frame.update_btn.configure(text="Update Ready! Restart to Apply", state="normal", fg_color=SECONDARY_COLOR, hover_color=SECONDARY_COLOR[0], command=self.apply_update)

    def apply_update(self):
        if hasattr(self, 'new_exe_name'):
            self.generate_update_script(self.new_exe_name)

    def generate_update_script(self, new_exe_name):
        current_exe = sys.executable
        # If running as a python script, don't try to replace python.exe
        if not current_exe.endswith(".exe") or "python" in current_exe.lower():
            messagebox.showinfo("Update Downloaded", f"Update downloaded as {new_exe_name}. Since you are running from source, please swap the files manually.")
            return

        current_exe_name = os.path.basename(current_exe)
        current_dir = os.path.dirname(current_exe)
        bat_path = os.path.join(current_dir, "update_app.bat")
        
        # Batch script to wait, swap files, restart, and delete itself
        bat_content = f"""@echo off
echo Updating EPF Self-Contribution Calculator...
timeout /t 2 /nobreak > NUL
del "{current_exe_name}"
rename "{new_exe_name}" "{current_exe_name}"
start "" "{current_exe_name}"
del "%~f0"
"""
        with open(bat_path, "w") as f:
            f.write(bat_content)
            
        # Launch script and kill app natively
        os.startfile(bat_path)
        self.after(100, self.on_closing)

    def on_closing(self):
        """Called when the user clicks the X button to close the app."""
        self.quit()      # Stops the mainloop
        self.destroy()   # Destroys the UI
        sys.exit(0)      # Ensures all background python processes and threads are terminated

    def update_sidebar_buttons(self, active_button):
        for btn in [self.add_record_btn, self.view_history_btn, self.dividend_btn, self.tax_btn, self.receipt_btn, self.settings_btn]:
            if btn == active_button:
                btn.configure(fg_color=PRIMARY_COLOR, text_color=BG_COLOR, hover_color=PRIMARY_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=PRIMARY_COLOR, hover_color=SURFACE_COLOR)


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        # Re-draw charts with new colors
        self.add_record_frame.draw_pie_chart_last()
        self.history_frame.draw_bar_chart(self.user_data)
        
    def change_color_theme_event(self, new_theme: str):
        # Changing color themes in CTK dynamically is limited, usually requires restart
        # But we will apply it for new widgets and inform the user
        ctk.set_default_color_theme(new_theme.lower())
        messagebox.showinfo("Theme Changed", f"Color theme set to {new_theme}.\nPlease restart the app for full effect.")

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        ctk.set_window_scaling(new_scaling_float)


    def update_data_callback(self, new_data):
        self.user_data = new_data
        save_data(self.user_data)
        self.history_frame.refresh_data(self.user_data)
        self.dividend_frame.refresh_data(self.user_data)

    def hide_all_frames(self):
        self.add_record_frame.grid_forget()
        self.history_frame.grid_forget()
        self.dividend_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.tax_frame.grid_forget()
        self.receipt_frame.grid_forget()

    def show_add_record_frame(self):
        self.hide_all_frames()
        self.add_record_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.update_sidebar_buttons(self.add_record_btn)

    def show_history_frame(self):
        self.hide_all_frames()
        self.history_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.history_frame.refresh_data(self.user_data)
        self.update_sidebar_buttons(self.view_history_btn)
        
    def show_dividend_frame(self):
        self.hide_all_frames()
        self.dividend_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.dividend_frame.refresh_data(self.user_data)
        self.update_sidebar_buttons(self.dividend_btn)

    def show_settings_frame(self):
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.update_sidebar_buttons(self.settings_btn)

    def show_tax_frame(self):
        self.hide_all_frames()
        self.tax_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.tax_frame.refresh_data(self.user_data)
        self.update_sidebar_buttons(self.tax_btn)

    def show_receipt_frame(self):
        self.hide_all_frames()
        self.receipt_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.receipt_frame.refresh_data(self.user_data)
        self.update_sidebar_buttons(self.receipt_btn)


# ==========================================================
# AddRecord, History, Dividend frames ported below...
# ==========================================================

class AddRecordFrame(ctk.CTkFrame):
    def __init__(self, master, current_data, save_callback):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        self.current_data = current_data
        self.save_callback = save_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Add New Income Record", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        self.salary_label = ctk.CTkLabel(self.input_frame, text="Total Received (RM):", anchor="w", text_color=TEXT_COLOR)
        self.salary_label.grid(row=0, column=0, sticky="w", pady=(10, 2))
        self.salary_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. 5650", corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.salary_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        self.saving_label = ctk.CTkLabel(self.input_frame, text="Saving Target (%):", anchor="w", text_color=TEXT_COLOR)
        self.saving_label.grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.saving_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. 20", corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.saving_entry.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        self.year_label = ctk.CTkLabel(self.input_frame, text="Year:", anchor="w", text_color=TEXT_COLOR)
        self.year_label.grid(row=4, column=0, sticky="w", pady=(0, 2))
        current_year = datetime.now().year
        years = [str(y) for y in range(2020, current_year + 5)]
        self.year_entry = ctk.CTkOptionMenu(self.input_frame, values=years, corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.year_entry.set(str(current_year))
        self.year_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        
        self.month_label = ctk.CTkLabel(self.input_frame, text="Month:", anchor="w", text_color=TEXT_COLOR)
        self.month_label.grid(row=6, column=0, sticky="w", pady=(0, 2))
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.month_entry = ctk.CTkOptionMenu(self.input_frame, values=months, corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.month_entry.set(datetime.now().strftime('%B'))
        self.month_entry.grid(row=7, column=0, sticky="ew", pady=(0, 15))
        
        self.calc_button = ctk.CTkButton(self.input_frame, text="Calculate", command=self.calculate, fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER, corner_radius=8)
        self.calc_button.grid(row=8, column=0, sticky="ew", pady=(10, 10))
        
        self.save_button = ctk.CTkButton(self.input_frame, text="Save Record", command=self.save_record, fg_color=SECONDARY_COLOR, text_color=("#FFFFFF", "#121212"), hover_color=PRIMARY_HOVER, corner_radius=8, state="disabled")
        self.save_button.grid(row=9, column=0, sticky="ew", pady=(0, 10))
        
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(10, 20), pady=10)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_rowconfigure(2, weight=1)
        
        self.res_title = ctk.CTkLabel(self.results_frame, text="Breakdown", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR)
        self.res_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(0,5), sticky="w")
        
        self.labels_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.labels_frame.grid(row=1, column=0, sticky="nw", padx=10)
        
        self.result_labels = {}
        fields = ["Derived Basic Salary", "Employer EPF (13%)", "Employee EPF (11%)", "Total EPF", "Net Salary", "Saving Target", "Remaining Balance"]
        
        for i, field in enumerate(fields):
            lbl = ctk.CTkLabel(self.labels_frame, text=f"{field}: RM 0.00", font=ctk.CTkFont(size=13), text_color=TEXT_COLOR)
            lbl.grid(row=i, column=0, pady=5, sticky="w")
            self.result_labels[field] = lbl

        self.current_calc_data = None
        self.last_chart_data = None
        
        self.chart_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.chart_frame.grid(row=1, column=1, rowspan=2, sticky="nsew")
        self.canvas = None

    def draw_pie_chart_last(self):
        if self.last_chart_data:
            self.draw_pie_chart(*self.last_chart_data)

    def draw_pie_chart(self, employer_epf, employee_epf, saving, remaining):
        self.last_chart_data = (employer_epf, employee_epf, saving, remaining)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        bg_col = "#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#FFFFFF"
        fig.patch.set_facecolor(bg_col)
        
        labels = ['Employer EPF', 'Employee EPF', 'Savings', 'Remaining Spend']
        sizes = [employer_epf, employee_epf, saving, remaining]
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
        explode = (0, 0, 0.1, 0)
        
        text_color = 'white' if ctk.get_appearance_mode() == "Dark" else 'black'
        
        def func(pct, allvals):
            absolute = pct/100.*sum(allvals)
            return f"{pct:.1f}%\\n(RM {absolute:.0f})"

        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct=lambda pct: func(pct, sizes),
                                          shadow=False, startangle=90, textprops=dict(color=text_color, size=8))
        
        ax.axis('equal')
        plt.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def calculate(self):
        try:
            total_received_str = self.salary_entry.get().strip()
            if not total_received_str: raise ValueError()
            total_received = float(total_received_str)
            
            saving_str = self.saving_entry.get().strip()
            saving_percentage = float(saving_str) if saving_str else 0.0
            
            base_salary, employer_epf, employee_epf, net_salary, total_epf = calculate_epf(total_received)
            saving_amount = net_salary * (saving_percentage / 100)
            remaining_balance = net_salary - saving_amount
            
            self.result_labels["Derived Basic Salary"].configure(text=f"Derived Basic Salary: RM {base_salary:.2f}")
            self.result_labels["Employer EPF (13%)"].configure(text=f"Employer EPF (13%): RM {employer_epf:.2f}")
            self.result_labels["Employee EPF (11%)"].configure(text=f"Employee EPF (11%): RM {employee_epf:.2f}")
            self.result_labels["Total EPF"].configure(text=f"Total EPF: RM {total_epf:.2f}")
            self.result_labels["Net Salary"].configure(text=f"Net Salary: RM {net_salary:.2f}")
            self.result_labels["Saving Target"].configure(text=f"Saving Target: RM {saving_amount:.2f}")
            self.result_labels["Remaining Balance"].configure(text=f"Remaining Balance: RM {remaining_balance:.2f}")
            
            self.draw_pie_chart(employer_epf, employee_epf, saving_amount, remaining_balance)

            self.current_calc_data = {
                "total_received": total_received, "basic_salary": base_salary,
                "employer_epf": employer_epf, "employee_epf": employee_epf,
                "total_epf": total_epf, "net_salary": net_salary,
                "saving_percentage": saving_percentage, "saving_amount": saving_amount,
                "remaining_balance": remaining_balance
            }
            self.save_button.configure(state="normal")
            
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for Salary and Savings.")

    def save_record(self):
        if not self.current_calc_data: return
        year = self.year_entry.get().strip()
        month = self.month_entry.get().strip()
            
        if year not in self.current_data:
            self.current_data[year] = {}
        
        self.current_data[year][month] = self.current_calc_data
        self.save_callback(self.current_data)
        
        messagebox.showinfo("Success", f"Data for {month} {year} saved successfully!")
        self.save_button.configure(state="disabled")
        self.salary_entry.delete(0, 'end')
        self.saving_entry.delete(0, 'end')

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, current_data, save_callback):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        self.save_callback = save_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Saved History & Trends", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.graph_frame = ctk.CTkFrame(self, fg_color="transparent", height=200)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.canvas = None
        
        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.table_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8), weight=1)
        self.data_rows = []
        
        self.export_btn = ctk.CTkButton(self, text="Export to Excel (CSV)", fg_color=SECONDARY_COLOR, text_color=("#FFFFFF", "#121212"), hover_color=PRIMARY_HOVER, corner_radius=8, command=self.export_to_csv)
        self.export_btn.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="e")
        
    def export_to_csv(self):
        if not self.master.user_data:
            messagebox.showinfo("Export", "No data available to export.")
            return
            
        filename = f"EPF_History_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Write Header
                writer.writerow(["Year", "Month", "Total Received (RM)", "Basic Salary (RM)", "Employer EPF (RM)", "Employee EPF (RM)", "Total EPF (RM)", "Net Salary (RM)", "Savings (RM)", "Remaining (RM)"])
                
                # Write Data
                months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                for year in sorted(self.master.user_data.keys(), reverse=True):
                    sorted_months = sorted(self.master.user_data[year].keys(), key=lambda m: months_order.index(m) if m in months_order else 99)
                    for month in sorted_months:
                        d = self.master.user_data[year][month]
                        writer.writerow([
                            year, month,
                            f"{d.get('total_received', 0):.2f}",
                            f"{d.get('basic_salary', 0):.2f}",
                            f"{d.get('employer_epf', 0):.2f}",
                            f"{d.get('employee_epf', 0):.2f}",
                            f"{d.get('total_epf', 0):.2f}",
                            f"{d.get('net_salary', 0):.2f}",
                            f"{d.get('saving_amount', 0):.2f}",
                            f"{d.get('remaining_balance', 0):.2f}"
                        ])
            messagebox.showinfo("Export Success", f"Data successfully exported to:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{e}")
        
    def draw_bar_chart(self, data):
        if self.canvas: self.canvas.get_tk_widget().destroy()
        if not data: return
            
        fig, ax = plt.subplots(figsize=(8, 3), dpi=80)
        bg_col = "#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#FFFFFF"
        fig.patch.set_facecolor(bg_col)
        ax.set_facecolor(bg_col)
        
        months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        latest_year = max(data.keys())
        yearly_data = data[latest_year]
        sorted_months = sorted(yearly_data.keys(), key=lambda m: months_order.index(m) if m in months_order else 99)
        
        net_salaries = [yearly_data[m]['net_salary'] for m in sorted_months]
        savings = [yearly_data[m]['saving_amount'] for m in sorted_months]
        
        x = range(len(sorted_months))
        width = 0.35
        
        text_color = 'white' if ctk.get_appearance_mode() == "Dark" else 'black'
        ax.tick_params(colors=text_color)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['top'].set_visible(False) 
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(text_color)
        
        p1 = "#BB86FC" if ctk.get_appearance_mode() == "Dark" else "#6200EE"
        p2 = "#03DAC6" if ctk.get_appearance_mode() == "Dark" else "#018786"
        
        ax.bar([i - width/2 for i in x], net_salaries, width, label='Net Salary', color=p1)
        ax.bar([i + width/2 for i in x], savings, width, label='Savings', color=p2)
        
        ax.set_ylabel('RM', color=text_color)
        ax.set_title(f'Income & Savings Trends ({latest_year})', color=text_color)
        ax.set_xticks(x)
        short_months = [m[:3] for m in sorted_months]
        ax.set_xticklabels(short_months)
        ax.legend(facecolor=bg_col, labelcolor=text_color)
        
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def delete_record(self, year, month):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the record for {month} {year}?"):
            if year in self.master.user_data and month in self.master.user_data[year]:
                del self.master.user_data[year][month]
                if not self.master.user_data[year]:
                    del self.master.user_data[year]
                self.save_callback(self.master.user_data)
        
    def refresh_data(self, data):
        for widget in self.data_rows: widget.destroy()
        self.data_rows.clear()
        self.draw_bar_chart(data)
        
        if not data:
            lbl = ctk.CTkLabel(self.table_scroll, text="No records found.", font=ctk.CTkFont(size=14), text_color=TEXT_COLOR)
            lbl.grid(row=1, column=0, columnspan=9, pady=20)
            self.data_rows.append(lbl)
            return
            
        headers = ["Year", "Month", "Total Rcvd", "Basic", "Total EPF", "Net Salary", "Saved", "Remaining", "Action"]
        for col_idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.table_scroll, text=h, font=ctk.CTkFont(weight="bold", size=13), text_color=TEXT_COLOR)
            lbl.grid(row=1, column=col_idx, padx=5, pady=5, sticky="ew")
            self.data_rows.append(lbl)
            
        divider = ctk.CTkFrame(self.table_scroll, height=2, fg_color="gray")
        divider.grid(row=2, column=0, columnspan=9, sticky="ew", pady=5)
        self.data_rows.append(divider)
        
        months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        current_row = 3
        for year in sorted(data.keys(), reverse=True):
            sorted_months = sorted(data[year].keys(), key=lambda m: months_order.index(m) if m in months_order else 99)
            for month in sorted_months:
                details = data[year][month]
                row_data = [year, month, f"{details.get('total_received', 0):.2f}", f"{details.get('basic_salary', 0):.2f}", 
                            f"{details.get('total_epf', 0):.2f}", f"{details.get('net_salary', 0):.2f}", 
                            f"{details.get('saving_amount', 0):.2f}", f"{details.get('remaining_balance', 0):.2f}"]
                for col_idx, val in enumerate(row_data):
                    lbl = ctk.CTkLabel(self.table_scroll, text=str(val), font=ctk.CTkFont(size=12), text_color=TEXT_COLOR)
                    lbl.grid(row=current_row, column=col_idx, padx=5, pady=2, sticky="ew")
                    self.data_rows.append(lbl)
                    
                del_btn = ctk.CTkButton(self.table_scroll, text="Del", width=40, height=24, fg_color=ERROR_COLOR, hover_color="#b65060", corner_radius=6,
                                        command=lambda y=year, m=month: self.delete_record(y, m))
                del_btn.grid(row=current_row, column=8, padx=5, pady=2)
                self.data_rows.append(del_btn)
                current_row += 1

class DividendFrame(ctk.CTkFrame):
    def __init__(self, master, current_data):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        self.current_data = current_data
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Annual EPF Dividend Calculator", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.info_label = ctk.CTkLabel(self, text="Estimate your yearly dividends based on your documented contributions.", font=ctk.CTkFont(size=14), text_color="gray")
        self.info_label.grid(row=1, column=0, padx=20, sticky="w")
        
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        
        self.year_label = ctk.CTkLabel(self.controls_frame, text="Select Year:", font=ctk.CTkFont(weight="bold"), text_color=TEXT_COLOR)
        self.year_label.grid(row=0, column=0, padx=(0,10), pady=10, sticky="e")
        
        self.year_menu = ctk.CTkOptionMenu(self.controls_frame, values=["No Data"], command=self.calculate_dividend, corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.year_menu.grid(row=0, column=1, padx=10, pady=10)
        
        self.rate_label = ctk.CTkLabel(self.controls_frame, text="Dividend Rate (%):", font=ctk.CTkFont(weight="bold"), text_color=TEXT_COLOR)
        self.rate_label.grid(row=0, column=2, padx=(20,10), pady=10, sticky="e")
        
        self.rate_entry = ctk.CTkEntry(self.controls_frame, width=80, corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.rate_entry.insert(0, "6.5") 
        self.rate_entry.grid(row=0, column=3, padx=10, pady=10)
        
        self.calc_btn = ctk.CTkButton(self.controls_frame, text="Calculate", command=self.calculate_dividend, fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER, corner_radius=8)
        self.calc_btn.grid(row=0, column=4, padx=20, pady=10)
        
        self.res_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=BG_COLOR)
        self.res_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        
        self.lbl_contributions = ctk.CTkLabel(self.res_frame, text="Documented Total EPF for Year: RM 0.00", font=ctk.CTkFont(size=16), text_color=TEXT_COLOR)
        self.lbl_contributions.pack(pady=(20, 10))
        
        self.lbl_dividend = ctk.CTkLabel(self.res_frame, text="Estimated Dividend: RM 0.00", font=ctk.CTkFont(size=20, weight="bold"), text_color=SECONDARY_COLOR)
        self.lbl_dividend.pack(pady=(10, 20))

    def refresh_data(self, data):
        self.current_data = data
        if data:
            years = sorted(list(data.keys()), reverse=True)
            self.year_menu.configure(values=years)
            self.year_menu.set(years[0])
            self.calculate_dividend()
        else:
            self.year_menu.configure(values=["No Data"])
            self.year_menu.set("No Data")
            self.lbl_contributions.configure(text="Documented Total EPF for Year: RM 0.00")
            self.lbl_dividend.configure(text="Estimated Dividend: RM 0.00")

    def calculate_dividend(self, *args):
        if not self.current_data: return
        selected_year = self.year_menu.get()
        if selected_year not in self.current_data: return
            
        try: rate = float(self.rate_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric dividend rate.")
            return

        total_epf_year = sum([details.get('total_epf', 0) for details in self.current_data[selected_year].values()])
        dividend = total_epf_year * (rate / 100)
        
        self.lbl_contributions.configure(text=f"Documented Total EPF for {selected_year}: RM {total_epf_year:,.2f}")
        self.lbl_dividend.configure(text=f"Estimated Dividend ({rate}%): RM {dividend:,.2f}")

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Settings & Customization", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="w")
        
        # Appearance Options
        self.appearance_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.appearance_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.app_title = ctk.CTkLabel(self.appearance_frame, text="Appearance", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR)
        self.app_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.mode_label = ctk.CTkLabel(self.appearance_frame, text="Theme Mode:", text_color=TEXT_COLOR)
        self.mode_label.grid(row=1, column=0, sticky="w", pady=5)
        self.mode_menu = ctk.CTkOptionMenu(self.appearance_frame, values=["Dark", "Light", "System"], command=self.master.change_appearance_mode_event)
        self.mode_menu.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        self.mode_menu.set(ctk.get_appearance_mode())
        
        self.color_label = ctk.CTkLabel(self.appearance_frame, text="Color Theme:", text_color=TEXT_COLOR)
        self.color_label.grid(row=2, column=0, sticky="w", pady=5)
        self.color_menu = ctk.CTkOptionMenu(self.appearance_frame, values=["Blue", "Green", "Dark-Blue"], command=self.master.change_color_theme_event)
        self.color_menu.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        self.scale_label = ctk.CTkLabel(self.appearance_frame, text="UI Scaling:", text_color=TEXT_COLOR)
        self.scale_label.grid(row=3, column=0, sticky="w", pady=5)
        self.scale_menu = ctk.CTkOptionMenu(self.appearance_frame, values=["80%", "90%", "100%", "110%", "120%"], command=self.master.change_scaling_event)
        self.scale_menu.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        self.scale_menu.set("100%")
        
        # About & Updates
        self.about_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.about_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        
        self.about_title = ctk.CTkLabel(self.about_frame, text="About & Updates", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR)
        self.about_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.version_label = ctk.CTkLabel(self.about_frame, text=f"Current Version: v{APP_VERSION}", text_color=TEXT_COLOR)
        self.version_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.update_btn = ctk.CTkButton(self.about_frame, text="Check for Updates", fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER, command=lambda: threading.Thread(target=self.master.run_update_check, args=(True,), daemon=True).start())
        self.update_btn.grid(row=2, column=0, sticky="w", pady=10)
        
        self.author_label = ctk.CTkLabel(self.about_frame, text="Created by: SkylordryanZ (MIT License)", text_color="gray", font=ctk.CTkFont(size=12))
        self.author_label.grid(row=3, column=0, sticky="w", pady=(20,0))

class TaxFrame(ctk.CTkFrame):
    def __init__(self, master, current_data):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        self.current_data = current_data
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(self, text="End of Year Tax Calculation (YA 2025)", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.info_label = ctk.CTkLabel(self, text="Estimate your tax liability based on actual records and future forecasts.", font=ctk.CTkFont(size=14), text_color="gray")
        self.info_label.grid(row=1, column=0, padx=20, sticky="w")
        
        # Controls Frame (Year Selection)
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        
        self.year_label = ctk.CTkLabel(self.controls_frame, text="Select Year:", font=ctk.CTkFont(weight="bold"), text_color=TEXT_COLOR)
        self.year_label.grid(row=0, column=0, padx=(0,10), pady=10, sticky="e")
        
        self.year_menu = ctk.CTkOptionMenu(self.controls_frame, values=["No Data"], command=self.update_view, corner_radius=8, fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.year_menu.grid(row=0, column=1, padx=10, pady=10)
        
        # Comparison Frame (Actual vs Forecast)
        self.comparison_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.comparison_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.comparison_frame.grid_columnconfigure(0, weight=1)
        self.comparison_frame.grid_columnconfigure(1, weight=1)
        
        # Actual Column
        self.actual_card = self.create_tax_card(self.comparison_frame, "Year-to-Date (Actual)", 0)
        
        # Forecast Column
        self.forecast_card = self.create_tax_card(self.comparison_frame, "Year-End (Forecast)", 1)

    def create_tax_card(self, parent, title, column):
        card = ctk.CTkFrame(parent, corner_radius=15, fg_color=BG_COLOR)
        card.grid(row=0, column=column, sticky="nsew", padx=10, pady=10)
        card.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=PRIMARY_COLOR)
        lbl_title.pack(pady=15)
        
        data_frame = ctk.CTkFrame(card, fg_color="transparent")
        data_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        fields = [
            ("Total Basic Salary", "RM 0.00"),
            ("EPF Relief (Employee)", "RM 0.00"),
            ("Individual Relief", "RM 9,000.00"),
            ("Chargeable Income", "RM 0.00"),
            ("Adjusted Tax (After Rebate)", "RM 0.00")
        ]
        
        labels = {}
        for field, default in fields:
            row = ctk.CTkFrame(data_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            f_lbl = ctk.CTkLabel(row, text=f"{field}:", text_color="gray", font=ctk.CTkFont(size=12))
            f_lbl.pack(side="left")
            
            v_lbl = ctk.CTkLabel(row, text=default, text_color=TEXT_COLOR, font=ctk.CTkFont(size=13, weight="normal"))
            v_lbl.pack(side="right")
            labels[field] = v_lbl
            
        return labels

    def refresh_data(self, data):
        self.current_data = data
        if data:
            years = sorted(list(data.keys()), reverse=True)
            self.year_menu.configure(values=years)
            self.year_menu.set(years[0])
            self.update_view()
        else:
            self.year_menu.configure(values=["No Data"])
            self.year_menu.set("No Data")

    def update_view(self, *args):
        selected_year = self.year_menu.get()
        if selected_year not in self.current_data:
            return
            
        year_records = self.current_data[selected_year]
        months_recorded = len(year_records)
        
        # Calculate Actuals
        actual_basic = sum([d.get('basic_salary', 0) for d in year_records.values()])
        actual_ee_epf = sum([d.get('employee_epf', 0) for d in year_records.values()])
        
        self.update_card_labels(self.actual_card, actual_basic, actual_ee_epf)
        
        # Calculate Forecast
        # Average per month * 12
        avg_basic = actual_basic / months_recorded
        avg_ee_epf = actual_ee_epf / months_recorded
        
        forecast_basic = avg_basic * 12
        forecast_ee_epf = avg_ee_epf * 12
        
        self.update_card_labels(self.forecast_card, forecast_basic, forecast_ee_epf)

    def update_card_labels(self, labels, basic, epf):
        # Reliefs
        individual_relief = 9000.0
        epf_relief = min(4000.0, epf) # Capped at 4000
        
        chargeable_income = max(0, basic - individual_relief - epf_relief)
        tax, rebate = calculate_tax_2025(chargeable_income)
        
        labels["Total Basic Salary"].configure(text=f"RM {basic:,.2f}")
        labels["EPF Relief (Employee)"].configure(text=f"RM {epf_relief:,.2f}")
        labels["Chargeable Income"].configure(text=f"RM {chargeable_income:,.2f}")
        
        tax_color = SECONDARY_COLOR if tax > 0 else "gray"
        tax_color = SECONDARY_COLOR if tax > 0 else "gray"
        labels["Adjusted Tax (After Rebate)"].configure(text=f"RM {tax:,.2f}", text_color=tax_color, font=ctk.CTkFont(size=14, weight="bold"))

class ReceiptFrame(ctk.CTkFrame):
    def __init__(self, master, current_data, save_callback):
        super().__init__(master, corner_radius=15, fg_color=SURFACE_COLOR)
        self.current_data = current_data
        self.save_callback = save_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(self, text="Receipt Manager", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Upper section: Upload Form
        self.form_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=15)
        self.form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # --- Form Fields ---
        # File Selection
        self.file_path = None
        self.file_btn = ctk.CTkButton(self.form_frame, text="Select Receipt (PDF/Img)", command=self.select_file, fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER)
        self.file_btn.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        self.file_label = ctk.CTkLabel(self.form_frame, text="No file selected", text_color="gray", font=ctk.CTkFont(size=11))
        self.file_label.grid(row=1, column=0, padx=15, pady=(0, 15))
        
        # Category
        ctk.CTkLabel(self.form_frame, text="Category:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=15, pady=(15, 0), sticky="w")
        self.cat_menu = ctk.CTkOptionMenu(self.form_frame, values=get_relief_categories(), width=250)
        self.cat_menu.grid(row=1, column=1, padx=15, pady=(0, 15), sticky="ew")
        
        # Amount & Description
        input_subframe = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        input_subframe.grid(row=0, column=2, rowspan=2, padx=15, pady=15, sticky="nsew")
        
        self.amount_entry = ctk.CTkEntry(input_subframe, placeholder_text="Amount (RM)")
        self.amount_entry.pack(fill="x", pady=5)
        
        self.desc_entry = ctk.CTkEntry(input_subframe, placeholder_text="Description (e.g. New Shoes)")
        self.desc_entry.pack(fill="x", pady=5)
        
        self.save_btn = ctk.CTkButton(self.form_frame, text="Save Receipt", command=self.save_receipt, fg_color=SECONDARY_COLOR, text_color=("#FFFFFF", "#121212"), hover_color=PRIMARY_HOVER)
        self.save_btn.grid(row=2, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="ew")

        # Lower section: List of Receipts
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.list_frame, text="Saved Receipts", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.list_frame, fg_color=BG_COLOR, corner_radius=10)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=2)
        self.scroll_frame.grid_columnconfigure(4, weight=1) # Actions
        
        self.receipt_rows = []

    def select_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Select Receipt", 
                                          filetypes=[("Image/PDF files", "*.jpg *.jpeg *.png *.pdf"), ("All files", "*.*")])
        if path:
            self.file_path = path
            self.file_label.configure(text=os.path.basename(path), text_color=TEXT_COLOR)

    def save_receipt(self):
        if not self.file_path:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please select a file first.")
            return
            
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please enter a valid amount.")
            return
            
        category = self.cat_menu.get()
        desc = self.desc_entry.get().strip() or "No description"
        
        # 1. Copy file to RECEIPTS_DIR with unique name
        ext = os.path.splitext(self.file_path)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        dest_path = os.path.join(RECEIPTS_DIR, unique_name)
        
        try:
            shutil.copy(self.file_path, dest_path)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save file: {e}")
            return
            
        # 2. Update data
        if "receipts" not in self.current_data:
            self.current_data["receipts"] = []
            
        receipt_entry = {
            "id": str(uuid.uuid4()),
            "file_name": unique_name,
            "original_name": os.path.basename(self.file_path),
            "category": category,
            "amount": amount,
            "description": desc,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.current_data["receipts"].append(receipt_entry)
        self.save_callback(self.current_data)
        
        # 3. Reset Form
        self.file_path = None
        self.file_label.configure(text="No file selected", text_color="gray")
        self.amount_entry.delete(0, 'end')
        self.desc_entry.delete(0, 'end')
        
        self.refresh_data(self.current_data)
        from tkinter import messagebox
        messagebox.showinfo("Success", "Receipt saved successfully!")

    def refresh_data(self, data):
        self.current_data = data
        for widget in self.receipt_rows:
            widget.destroy()
        self.receipt_rows.clear()
        
        if "receipts" not in data or not data["receipts"]:
            lbl = ctk.CTkLabel(self.scroll_frame, text="No receipts found.", font=ctk.CTkFont(size=14), text_color="gray")
            lbl.grid(row=0, column=0, columnspan=5, pady=20)
            self.receipt_rows.append(lbl)
            return

        # Headers
        headers = ["Date", "Category", "Amount", "Description", "Actions"]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_frame, text=h, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.receipt_rows.append(lbl)
            
        # Rows
        for idx, r in enumerate(reversed(data["receipts"])):
            row_idx = idx + 1
            
            # Date (shortened)
            d_lbl = ctk.CTkLabel(self.scroll_frame, text=r['date'][:10], font=ctk.CTkFont(size=11))
            d_lbl.grid(row=row_idx, column=0, padx=5, pady=2)
            self.receipt_rows.append(d_lbl)
            
            # Category
            c_lbl = ctk.CTkLabel(self.scroll_frame, text=r['category'].split(' ')[0], font=ctk.CTkFont(size=11))
            c_lbl.grid(row=row_idx, column=1, padx=5, pady=2)
            self.receipt_rows.append(c_lbl)
            
            # Amount
            a_lbl = ctk.CTkLabel(self.scroll_frame, text=f"RM {r['amount']:.2f}", font=ctk.CTkFont(size=11, weight="bold"))
            a_lbl.grid(row=row_idx, column=2, padx=5, pady=2)
            self.receipt_rows.append(a_lbl)
            
            # Description
            desc_text = r['description']
            if len(desc_text) > 20: desc_text = desc_text[:17] + "..."
            desc_lbl = ctk.CTkLabel(self.scroll_frame, text=desc_text, font=ctk.CTkFont(size=11))
            desc_lbl.grid(row=row_idx, column=3, padx=5, pady=2)
            self.receipt_rows.append(desc_lbl)
            
            # Actions
            action_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            action_frame.grid(row=row_idx, column=4, padx=5, pady=2)
            self.receipt_rows.append(action_frame)
            
            open_btn = ctk.CTkButton(action_frame, text="👁", width=30, height=24, command=lambda fname=r['file_name']: self.open_file(fname))
            open_btn.pack(side="left", padx=2)
            
            del_btn = ctk.CTkButton(action_frame, text="🗑", width=30, height=24, fg_color=ERROR_COLOR, hover_color="#b65060", command=lambda rid=r['id']: self.delete_receipt(rid))
            del_btn.pack(side="left", padx=2)

    def open_file(self, file_name):
        path = os.path.join(RECEIPTS_DIR, file_name)
        if os.path.exists(path):
            try:
                if os.name == 'nt': # Windows
                    os.startfile(path)
                elif os.name == 'posix': # macOS/Linux
                    subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', path])
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Could not open file: {e}")
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "File not found.")

    def delete_receipt(self, receipt_id):
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this receipt?"):
            receipt = next((r for r in self.current_data["receipts"] if r["id"] == receipt_id), None)
            if receipt:
                # Delete file
                path = os.path.join(RECEIPTS_DIR, receipt["file_name"])
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
                
                # Update data
                self.current_data["receipts"] = [r for r in self.current_data["receipts"] if r["id"] != receipt_id]
                self.save_callback(self.current_data)
                self.refresh_data(self.current_data)

if __name__ == "__main__":
    app = App()
    app.mainloop()
