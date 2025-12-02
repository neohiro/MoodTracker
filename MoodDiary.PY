import json
import os
import datetime
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

# File to store your history
DATA_FILE = "mood_tracker_data.json"

class MoodTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mood Tracker")
        self.root.geometry("1000x850") # Increased height slightly for the note box
        
        # --- Modern Color Palette ---
        self.colors = {
            "bg": "#f0f2f5",          # Light gray background
            "card_bg": "#ffffff",     # White cards
            "text_primary": "#1f2937",# Dark gray text
            "text_secondary": "#6b7280", # Lighter gray text
            "accent": "#6366f1",      # Indigo/Blue accent (Middle value)
            "accent_hover": "#4f46e5",
            "success": "#10b981",     # Green (High value)
            "danger": "#ef4444",      # Red (Low value)
            "border": "#e5e7eb"       # Subtle border
        }

        self.root.configure(bg=self.colors["bg"])
        
        # --- Typography ---
        self.fonts = {
            "h1": ("Segoe UI", 20, "bold"),
            "h2": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 11),
            "label": ("Segoe UI", 10, "bold"),
            "small": ("Segoe UI", 9)
        }
        
        # Load Data
        self.data = self.load_data()
        
        # --- Style Configuration ---
        self.setup_styles()
        
        # Create Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Tab 1: Input
        self.tab_input = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tab_input, text="  Today's Mood  ")
        
        # Tab 2: History
        self.tab_history = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(self.tab_history, text="  History Trends  ")
        
        # Initialize
        self.sliders = {} 
        self.score_labels = {} 
        self.note_text_widget = None # Reference for the text box
        self.build_input_tab()
        self.build_history_tab()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # General Frames
        self.style.configure("Main.TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card_bg"], relief="flat")
        
        # Typography
        self.style.configure("H1.TLabel", background=self.colors["bg"], foreground=self.colors["text_primary"], font=self.fonts["h1"])
        self.style.configure("H2.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_primary"], font=self.fonts["h2"])
        self.style.configure("Body.TLabel", background=self.colors["card_bg"], foreground=self.colors["text_secondary"], font=self.fonts["body"])
        
        # Buttons (Modern Flat Look)
        self.style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=10
        )
        self.style.map("Accent.TButton", background=[("active", self.colors["accent_hover"])])

        self.style.configure(
            "Secondary.TButton",
            background=self.colors["card_bg"],
            foreground=self.colors["accent"],
            font=("Segoe UI", 10),
            borderwidth=1,
            bordercolor=self.colors["accent"],
            padding=6
        )
        
        # Danger/Remove Button Style
        self.style.configure(
            "Danger.TButton",
            background=self.colors["card_bg"],
            foreground=self.colors["danger"],
            font=("Segoe UI", 10),
            borderwidth=1,
            bordercolor=self.colors["danger"],
            padding=6
        )
        self.style.map("Danger.TButton", background=[("active", "#fee2e2")])
        
        # --- Slider Styling ---
        # Make the slider handle (thumb) the accent color so it pops
        self.style.configure("Horizontal.TScale", 
                             background=self.colors["accent"], # This sets the handle color in 'clam'
                             troughcolor="#e5e7eb",            # A light grey track
                             bordercolor=self.colors["card_bg"],
                             lightcolor=self.colors["accent"], 
                             darkcolor=self.colors["accent"])
        
        self.style.map("Horizontal.TScale", 
                       background=[("pressed", self.colors["accent_hover"]), 
                                   ("active", self.colors["accent_hover"])])

        # Notebook (Tabs)
        self.style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                             padding=[20, 10], 
                             font=("Segoe UI", 11, "bold"),
                             background=self.colors["bg"],
                             foreground=self.colors["text_secondary"])
        self.style.map("TNotebook.Tab", 
                       background=[("selected", self.colors["card_bg"])],
                       foreground=[("selected", self.colors["accent"])])

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            default_data = {
                "kpis": ["Happiness", "Energy", "Sleep Quality"],
                "history": []
            }
            return default_data
        with open(DATA_FILE, 'r') as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_today_entry(self):
        today = datetime.date.today().isoformat()
        for entry in self.data['history']:
            if entry['date'] == today:
                return entry
        return None

    def get_score_color(self, value):
        """
        Interpolates color based on value:
        0 = Red, 5 = Blue, 10 = Green
        """
        val = float(value)
        
        def hex_to_rgb(hex_col):
            return tuple(int(hex_col.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        red = hex_to_rgb(self.colors["danger"])   # 0
        blue = hex_to_rgb(self.colors["accent"])  # 5
        green = hex_to_rgb(self.colors["success"]) # 10
        
        if val <= 5:
            ratio = val / 5.0
            r = int(red[0] * (1 - ratio) + blue[0] * ratio)
            g = int(red[1] * (1 - ratio) + blue[1] * ratio)
            b = int(red[2] * (1 - ratio) + blue[2] * ratio)
        else:
            ratio = (val - 5) / 5.0
            r = int(blue[0] * (1 - ratio) + green[0] * ratio)
            g = int(blue[1] * (1 - ratio) + green[1] * ratio)
            b = int(blue[2] * (1 - ratio) + green[2] * ratio)
            
        return rgb_to_hex((r, g, b))

    def center_dialog(self, dialog, width, height):
        """Centers a toplevel dialog relative to the main window."""
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def build_input_tab(self):
        for widget in self.tab_input.winfo_children():
            widget.destroy()

        # --- Header Section ---
        header_frame = ttk.Frame(self.tab_input, style="Main.TFrame")
        header_frame.pack(fill='x', pady=(10, 20), padx=10)
        
        date_str = datetime.date.today().strftime('%A, %B %d')
        lbl_date = ttk.Label(header_frame, text=f"How are you feeling this {date_str}?", style="H1.TLabel")
        lbl_date.pack(side='left')

        # --- Scrollable Card Area ---
        canvas = tk.Canvas(self.tab_input, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_input, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Main.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        frame_window_id = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas.itemconfig(frame_window_id, width=event.width)
            
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        # --- Content ---
        today_entry = self.get_today_entry()
        current_scores = today_entry['scores'] if today_entry else {}
        current_note = today_entry.get('note', '') if today_entry else ""

        self.sliders = {}
        self.score_labels = {}

        for kpi in self.data['kpis']:
            card = ttk.Frame(self.scrollable_frame, style="Card.TFrame", padding=20)
            card.pack(fill='x', pady=8, padx=5)
            
            top_row = ttk.Frame(card, style="Card.TFrame")
            top_row.pack(fill='x', pady=(0, 10))
            
            ttk.Label(top_row, text=kpi, style="H2.TLabel").pack(side='left')
            
            initial_val = current_scores.get(kpi, 5.0)
            
            # Use dynamic color for initial label
            initial_color = self.get_score_color(initial_val)
            val_lbl = ttk.Label(top_row, text=f"{initial_val:.1f}", font=("Segoe UI", 18, "bold"), foreground=initial_color, background=self.colors["card_bg"])
            val_lbl.pack(side='right')
            self.score_labels[kpi] = val_lbl

            scale = ttk.Scale(
                card, 
                from_=0, 
                to=10, 
                orient='horizontal', 
                command=lambda v, k=kpi: self.update_label(k, v)
            )
            scale.set(initial_val)
            scale.pack(fill='x', expand=True)
            
            self.sliders[kpi] = scale

        # Footer / Save Button
        footer_frame = ttk.Frame(self.tab_input, style="Main.TFrame")
        footer_frame.pack(fill='x', pady=20, padx=10)
        
        btn_save = ttk.Button(
            footer_frame, 
            text="Save Daily Log", 
            style="Accent.TButton",
            command=self.save_today
        )
        btn_save.pack(fill='x', padx=100)

        # Management Buttons (Stacked vertically below save)
        manage_frame = ttk.Frame(footer_frame, style="Main.TFrame")
        manage_frame.pack(pady=(15, 0))

        btn_remove = ttk.Button(manage_frame, text="- Remove Metric", style="Danger.TButton", command=self.remove_kpi_dialog)
        btn_remove.pack(fill='x', pady=5)

        btn_add = ttk.Button(manage_frame, text="+ Add Metric", style="Secondary.TButton", command=self.add_kpi)
        btn_add.pack(fill='x', pady=5)
        
        # --- Note Section (Below Add Metric) ---
        note_frame = ttk.Frame(footer_frame, style="Main.TFrame")
        note_frame.pack(fill='x', pady=(20, 10))
        
        # Centered label and narrower box (height increased to 8, width reduced to 25)
        ttk.Label(note_frame, text="Daily Note / Reflection:", style="Body.TLabel", background=self.colors["bg"]).pack(anchor="center")
        
        self.note_text_widget = tk.Text(note_frame, height=8, width=25, font=self.fonts["body"], bd=1, relief="solid")
        self.note_text_widget.pack(pady=(5, 0))
        
        if current_note:
            self.note_text_widget.insert("1.0", current_note)

    def update_label(self, kpi, value):
        color = self.get_score_color(value)
        self.score_labels[kpi].config(text=f"{float(value):.1f}", foreground=color)

    def add_kpi(self):
        width, height = 350, 180
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Metric")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root) 
        
        # Center the dialog
        self.center_dialog(dialog, width, height)

        ttk.Label(dialog, text="What would you like to track?", background=self.colors["bg"], font=self.fonts["body"]).pack(pady=(20, 10))

        entry_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=entry_var, font=self.fonts["body"])
        entry.pack(pady=5, padx=30, fill='x')
        entry.focus_set()

        def confirm_add(event=None):
            new_kpi = entry_var.get().strip()
            if not new_kpi:
                return
            
            if new_kpi not in self.data['kpis']:
                self.data['kpis'].append(new_kpi)
                self.save_data()
                self.build_input_tab()
                dialog.destroy()
                messagebox.showinfo("Success", f"Now tracking '{new_kpi}'!", parent=self.root)
            else:
                messagebox.showwarning("Duplicate", "You are already tracking this.", parent=dialog)

        dialog.bind('<Return>', confirm_add)

        btn_frame = ttk.Frame(dialog, style="Main.TFrame")
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Add", style="Accent.TButton", command=confirm_add).pack(side="left", padx=5)

    def remove_kpi_dialog(self):
        if not self.data['kpis']:
            messagebox.showinfo("Info", "No metrics to remove.")
            return

        width, height = 350, 180
        dialog = tk.Toplevel(self.root)
        dialog.title("Remove Metric")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        
        # Center the dialog
        self.center_dialog(dialog, width, height)
        
        ttk.Label(dialog, text="Select a metric to stop tracking:", background=self.colors["bg"], font=self.fonts["body"]).pack(pady=(20, 10))
        
        combo = ttk.Combobox(dialog, values=self.data['kpis'], state="readonly", font=self.fonts["body"])
        combo.pack(pady=5, padx=30, fill='x')
        if self.data['kpis']:
            combo.current(0)
        
        def confirm_remove():
            selected = combo.get()
            if not selected:
                return
            
            if messagebox.askyesno("Confirm Removal", f"Are you sure you want to stop tracking '{selected}'?\n\n(Note: Past data for this metric will be preserved in the file but hidden from graphs.)", parent=dialog):
                self.data['kpis'].remove(selected)
                self.save_data()
                self.build_input_tab()
                dialog.destroy()
                messagebox.showinfo("Removed", f"'{selected}' has been removed from your list.")

        btn_frame = ttk.Frame(dialog, style="Main.TFrame")
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove", style="Danger.TButton", command=confirm_remove).pack(side="left", padx=5)

    def save_today(self):
        today = datetime.date.today().isoformat()
        new_scores = {kpi: float(scale.get()) for kpi, scale in self.sliders.items()}
        
        # Get note content
        note_content = self.note_text_widget.get("1.0", tk.END).strip()
        
        today_entry = self.get_today_entry()
        if today_entry:
            today_entry['scores'] = new_scores
            today_entry['note'] = note_content
        else:
            self.data['history'].append({
                "date": today, 
                "scores": new_scores,
                "note": note_content
            })
            
        self.save_data()
        messagebox.showinfo("Saved", "✨ Daily log saved successfully!")

    def build_history_tab(self):
        header_frame = ttk.Frame(self.tab_history, style="Main.TFrame")
        header_frame.pack(fill='x', pady=(10, 10), padx=10)
        
        ttk.Label(header_frame, text="Wellbeing Trends", style="H1.TLabel").pack(side='left')
        ttk.Button(header_frame, text="Export PDF Report", style="Secondary.TButton", command=self.export_to_pdf).pack(side='right')

        graph_card = ttk.Frame(self.tab_history, style="Card.TFrame", padding=10)
        graph_card.pack(fill='both', expand=True, padx=10, pady=10)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor(self.colors["card_bg"])
        self.ax = self.figure.add_subplot(111)
        
        self.canvas_widget = FigureCanvasTkAgg(self.figure, master=graph_card)
        self.canvas_widget.get_tk_widget().pack(fill='both', expand=True)
        
        # --- Hover Annotation ---
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w", ec="gray", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        
        def hover(event):
            vis = self.annot.get_visible()
            if event.inaxes == self.ax:
                # Find closest date index
                if not self.data['history']:
                    return
                    
                # Matplotlib plots categorical strings as 0, 1, 2... on x-axis
                if event.xdata is not None:
                    idx = int(round(event.xdata))
                    if 0 <= idx < len(self.data['history']):
                        entry = self.data['history'][idx]
                        note = entry.get('note', '')
                        if note:
                            # Update annotation
                            self.annot.xy = (idx, event.ydata)
                            text = f"{entry['date']}\n{note}"
                            self.annot.set_text(text)
                            self.annot.set_visible(True)
                            self.canvas_widget.draw_idle()
                            return

            if vis:
                self.annot.set_visible(False)
                self.canvas_widget.draw_idle()

        self.canvas_widget.mpl_connect("motion_notify_event", hover)

    def on_tab_change(self, event):
        selected_tab = event.widget.select()
        tab_text = event.widget.tab(selected_tab, "text")
        if "History" in tab_text:
            self.refresh_graph()

    def refresh_graph(self):
        self.ax.clear()
        self.ax.set_facecolor(self.colors["card_bg"])
        
        if not self.data['history']:
            self.ax.text(0.5, 0.5, "No data logged yet.", ha='center', va='center', fontsize=12, color=self.colors["text_secondary"])
            self.canvas_widget.draw()
            return

        dates = [entry['date'] for entry in self.data['history']]
        
        for kpi in self.data['kpis']:
            scores = [entry['scores'].get(kpi, None) for entry in self.data['history']]
            self.ax.plot(dates, scores, marker='o', label=kpi, linewidth=2.5, markersize=6, alpha=0.9)

        self.ax.set_ylim(0, 10.5)
        self.ax.grid(True, linestyle=':', alpha=0.4, color=self.colors["text_secondary"])
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.colors["border"])
        self.ax.spines['bottom'].set_color(self.colors["border"])
        
        self.ax.tick_params(axis='x', colors=self.colors["text_secondary"], rotation=45)
        self.ax.tick_params(axis='y', colors=self.colors["text_secondary"])
        
        self.ax.legend(frameon=False, loc='upper left', bbox_to_anchor=(1, 1))
        self.figure.tight_layout()
        self.canvas_widget.draw()
        
    def export_to_pdf(self):
        if not self.data['history']:
            messagebox.showwarning("Empty", "No data to export.")
            return

        filename = "mood_report.pdf"
        try:
            with PdfPages(filename) as pdf:
                # --- Page 1: Graph ---
                fig_graph = plt.figure(figsize=(10, 6))
                
                dates = [entry['date'] for entry in self.data['history']]
                for kpi in self.data['kpis']:
                    scores = [entry['scores'].get(kpi, None) for entry in self.data['history']]
                    plt.plot(dates, scores, marker='o', label=kpi)
                
                plt.title('Wellbeing History', fontsize=16)
                plt.ylim(0, 10.5)
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                pdf.savefig(fig_graph)
                plt.close(fig_graph)

                # --- Page 2: Scores Table ---
                fig_table, ax = plt.subplots(figsize=(11, 8))
                ax.axis('tight')
                ax.axis('off')
                
                columns = ["Date"] + self.data['kpis']
                cell_text = []
                for entry in self.data['history']:
                    row = [entry['date']]
                    for kpi in self.data['kpis']:
                        row.append(str(entry['scores'].get(kpi, "-")))
                    cell_text.append(row)

                table = ax.table(cellText=cell_text, colLabels=columns, loc='center', cellLoc='center')
                table.scale(1, 1.5)
                table.auto_set_font_size(False)
                
                # Style headers and cells
                for (row, col), cell in table.get_celld().items():
                    if row == 0:
                        # Headers
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(self.colors["accent"])
                        cell.set_edgecolor('white')
                    else:
                        # Data Cells - Color numeric values
                        try:
                            val_text = cell.get_text().get_text()
                            val = float(val_text)
                            col_hex = self.get_score_color(val)
                            cell.get_text().set_color(col_hex)
                            cell.get_text().set_weight('bold')
                        except ValueError:
                            pass # Not a number (e.g., date or "-")
                
                plt.title("Detailed Logs", pad=20, fontsize=14)
                pdf.savefig(fig_table)
                plt.close(fig_table)
                
                # --- Page 3: Notes Table ---
                # Filter entries that actually have notes
                entries_with_notes = [e for e in self.data['history'] if e.get('note', '').strip()]
                
                if entries_with_notes:
                    fig_notes, ax = plt.subplots(figsize=(11, 8))
                    ax.axis('tight')
                    ax.axis('off')
                    
                    columns = ["Date", "Note"]
                    cell_text = []
                    for entry in entries_with_notes:
                        # Limit note length for display or let it wrap (matplotlib table wrap is manual, we'll keep it simple)
                        # We simply replace newlines with spaces for a cleaner single-row table, or let column be wide
                        note_txt = entry.get('note', '').replace('\n', ' ') 
                        cell_text.append([entry['date'], note_txt])

                    table = ax.table(cellText=cell_text, colLabels=columns, loc='top', cellLoc='left', colWidths=[0.2, 0.8])
                    table.scale(1, 1.5)
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    
                    # Style headers
                    for (row, col), cell in table.get_celld().items():
                        if row == 0:
                            cell.set_text_props(weight='bold', color='white')
                            cell.set_facecolor(self.colors["accent"])
                            cell.set_edgecolor('white')
                    
                    plt.title("Daily Reflections", pad=20, fontsize=14)
                    pdf.savefig(fig_notes)
                    plt.close(fig_notes)

            messagebox.showinfo("Success", f"Report saved as {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = MoodTrackerApp(root)
    root.mainloop()