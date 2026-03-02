import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading
import urllib.request
import json

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculator import calculate_epf, load_data, save_data

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

APP_VERSION = "1.0.0"
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
        
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w", text_color=TEXT_COLOR)
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main frame areas
        self.add_record_frame = AddRecordFrame(self, self.user_data, self.update_data_callback)
        self.history_frame = HistoryFrame(self, self.user_data, self.update_data_callback)
        self.dividend_frame = DividendFrame(self, self.user_data)
        
        # Initialize default view
        self.show_add_record_frame()
        
        # Check for updates in the background
        threading.Thread(target=self.run_update_check, daemon=True).start()

    def run_update_check(self):
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").lstrip("v")
                current_version = APP_VERSION.lstrip("v")
                if latest_version and latest_version != current_version:
                    msg = (f"A new version (v{latest_version}) is available!\n\n"
                           f"You are currently running v{current_version}.\n"
                           f"Please visit https://github.com/{GITHUB_REPO}/releases to download the latest update.")
                    self.after(2000, lambda: messagebox.showinfo("Update Available", msg))
        except Exception as e:
            print(f"Update check failed: {e}")

    def update_sidebar_buttons(self, active_button):
        for btn in [self.add_record_btn, self.view_history_btn, self.dividend_btn]:
            if btn == active_button:
                btn.configure(fg_color=PRIMARY_COLOR, text_color=BG_COLOR, hover_color=PRIMARY_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=PRIMARY_COLOR, hover_color=SURFACE_COLOR)


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        # Re-draw charts with new colors
        self.add_record_frame.draw_pie_chart_last()
        self.history_frame.draw_bar_chart(self.user_data)


    def update_data_callback(self, new_data):
        self.user_data = new_data
        save_data(self.user_data)
        self.history_frame.refresh_data(self.user_data)
        self.dividend_frame.refresh_data(self.user_data)

    def hide_all_frames(self):
        self.add_record_frame.grid_forget()
        self.history_frame.grid_forget()
        self.dividend_frame.grid_forget()

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

if __name__ == "__main__":
    app = App()
    app.mainloop()
