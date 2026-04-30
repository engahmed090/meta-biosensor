import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BiosensorDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Metamaterial Biosensor Simulation Dashboard")
        self.geometry("1100x700")
        self.configure(fg_color="#121212") # Deep dark background

        # Disease / Sample Profiles
        self.profiles = {
            "Normal Blood": {
                "f_res": 10.0, 
                "depth": -40.0, 
                "shift_mhz": 0, 
                "diagnosis": "NORMAL: No significant abnormalities detected.", 
                "color": "#00FF00"
            },
            "Breast Cancer (MCF-7)": {
                "f_res": 9.6, 
                "depth": -38.0, 
                "shift_mhz": -400, 
                "diagnosis": "WARNING: BREAST CANCER (MCF-7) DETECTED", 
                "color": "#FF3333"
            },
            "Leukemia": {
                "f_res": 9.2, 
                "depth": -35.0, 
                "shift_mhz": -800, 
                "diagnosis": "CRITICAL: LEUKEMIA DETECTED", 
                "color": "#FF0000"
            },
            "High Glucose (Diabetes)": {
                "f_res": 10.3, 
                "depth": -42.0, 
                "shift_mhz": 300, 
                "diagnosis": "ALERT: HIGH GLUCOSE (DIABETES) DETECTED", 
                "color": "#FFA500"
            }
        }

        # Main Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------
        # Left Panel (Controls & Diagnostics)
        # ---------------------------------------------------------
        self.left_panel = ctk.CTkFrame(self, width=320, corner_radius=15, fg_color="#1e1e1e", border_width=2, border_color="#333333")
        self.left_panel.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_panel.grid_rowconfigure(8, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self.left_panel, 
            text="BIOSENSOR\nCONTROL PANEL", 
            font=ctk.CTkFont(family="Roboto", size=26, weight="bold"), 
            text_color="#00FFFF"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        # Dropdown
        self.sample_label = ctk.CTkLabel(self.left_panel, text="Select Blood Sample Profile:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cccccc")
        self.sample_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")

        self.sample_menu = ctk.CTkOptionMenu(
            self.left_panel, 
            values=list(self.profiles.keys()), 
            font=ctk.CTkFont(size=14),
            fg_color="#333333",
            button_color="#444444",
            button_hover_color="#555555"
        )
        self.sample_menu.grid(row=2, column=0, padx=20, pady=(0, 30), sticky="ew")

        # Run Button
        self.run_button = ctk.CTkButton(
            self.left_panel, 
            text="RUN ANALYSIS", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            fg_color="#0055ff", 
            hover_color="#0033cc", 
            corner_radius=8,
            height=45,
            command=self.start_analysis
        )
        self.run_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Progress Bar
        self.progress_label = ctk.CTkLabel(self.left_panel, text="Scan Progress:", font=ctk.CTkFont(size=12), text_color="#aaaaaa")
        self.progress_label.grid(row=4, column=0, padx=20, pady=(15, 0), sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.left_panel, mode="determinate", height=10, progress_color="#00FFFF")
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(5, 30), sticky="ew")
        self.progress_bar.set(0)

        # Diagnostic Results Box
        self.diag_frame = ctk.CTkFrame(self.left_panel, corner_radius=10, fg_color="#121212", border_width=1, border_color="#444444")
        self.diag_frame.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.diag_frame, text="DIAGNOSTIC RESULTS", font=ctk.CTkFont(size=14, weight="bold"), text_color="#aaaaaa").pack(pady=(15, 10))
        
        self.shift_label = ctk.CTkLabel(self.diag_frame, text="Δf: -- MHz", font=ctk.CTkFont(family="Courier", size=22, weight="bold"), text_color="#ffffff")
        self.shift_label.pack(pady=10)

        self.status_label = ctk.CTkLabel(self.diag_frame, text="STATUS: STANDBY", font=ctk.CTkFont(size=15, weight="bold"), text_color="#555555", wraplength=240)
        self.status_label.pack(pady=(10, 20), padx=15)

        # ---------------------------------------------------------
        # Right Panel (Live Graph)
        # ---------------------------------------------------------
        self.right_panel = ctk.CTkFrame(self, corner_radius=15, fg_color="#1e1e1e", border_width=2, border_color="#333333")
        self.right_panel.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        self.is_running = False
        self.setup_plot()

    def setup_plot(self):
        # Matplotlib Dark Theme
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 6), facecolor='#1e1e1e')
        self.ax.set_facecolor('#121212')
        
        # Axes labels and limits
        self.ax.set_title("S₁₁ Parameter (Return Loss) Response", color='white', fontsize=16, pad=15, fontweight='bold')
        self.ax.set_xlabel("Frequency (GHz)", color='#dddddd', fontsize=13, labelpad=10)
        self.ax.set_ylabel("S₁₁ (dB)", color='#dddddd', fontsize=13, labelpad=10)
        self.ax.set_xlim(8, 12)
        self.ax.set_ylim(-50, 0)
        
        # Grid styling
        self.ax.grid(True, linestyle='--', alpha=0.3, color='#888888')
        self.ax.tick_params(colors='#dddddd', labelsize=11)
        
        # Spines styling
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444444')

        self.fig.tight_layout()

        # Embed plot into CustomTkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

        # Generate X axis data points
        self.f = np.linspace(8, 12, 500)
        
        # Plot Reference Line (Normal Blood)
        ref_f_res = self.profiles["Normal Blood"]["f_res"]
        ref_depth = self.profiles["Normal Blood"]["depth"]
        self.ref_y = self.generate_lorentzian(self.f, ref_f_res, ref_depth)
        self.ax.plot(self.f, self.ref_y, color='#888888', linestyle='--', linewidth=2, label="Reference (Normal Blood)")
        
        self.legend = self.ax.legend(facecolor='#1e1e1e', edgecolor='#444444', labelcolor='white', fontsize=11, loc='upper right')

        # Initialize the animated line as empty
        self.scan_line, = self.ax.plot([], [], color='#00FFFF', linewidth=3, label="Current Scan")
        self.canvas.draw()

    def generate_lorentzian(self, f, f_res, depth, q_factor=30):
        """
        Generates a realistic S11 curve using a Lorentzian resonance function.
        f: array of frequencies
        f_res: resonant frequency
        depth: depth of the dip in dB (negative)
        q_factor: quality factor, dictates the sharpness of the dip
        """
        gamma = f_res / (2 * q_factor)
        # Inverse Lorentzian (dip instead of peak)
        dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
        return dip

    def start_analysis(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.run_button.configure(state="disabled")
        self.sample_menu.configure(state="disabled")
        self.shift_label.configure(text="Δf: Scanning...")
        self.status_label.configure(text="STATUS: SCANNING IN PROGRESS...", text_color="#00FFFF")
        self.progress_bar.set(0)
        
        # Reset the scanning line
        self.scan_line.set_data([], [])
        self.scan_line.set_color("#00FFFF") # Default scanning color
        self.canvas.draw()

        selected_profile = self.sample_menu.get()
        # Run animation in a separate thread to keep UI responsive
        threading.Thread(target=self.animate_scan, args=(selected_profile,), daemon=True).start()

    def animate_scan(self, profile_name):
        profile = self.profiles[profile_name]
        f_res = profile["f_res"]
        depth = profile["depth"]
        
        # Pre-calculate the full target Y array
        target_y = self.generate_lorentzian(self.f, f_res, depth)
        
        steps = 80 # Number of animation frames
        sleep_time = 0.025 # Time between frames
        
        for i in range(1, steps + 1):
            time.sleep(sleep_time)
            # Take a slice of the data up to the current progress
            slice_index = int(len(self.f) * (i / steps))
            current_x = self.f[:slice_index]
            current_y = target_y[:slice_index]
            
            # Update GUI from background thread using after() to be thread-safe
            self.after(0, self.update_plot, current_x, current_y, i / steps)

        # Finish up and display diagnosis
        self.after(0, self.finish_analysis, profile)

    def update_plot(self, x, y, progress):
        self.scan_line.set_data(x, y)
        self.progress_bar.set(progress)
        self.canvas.draw()

    def finish_analysis(self, profile):
        self.is_running = False
        self.run_button.configure(state="normal")
        self.sample_menu.configure(state="normal")
        
        # Update shift display
        shift = profile["shift_mhz"]
        sign = "+" if shift > 0 else ""
        self.shift_label.configure(text=f"Δf: {sign}{shift} MHz")
        
        # Update diagnosis text and color
        self.status_label.configure(text=profile["diagnosis"], text_color=profile["color"])

        # Change the plotted line color to match the diagnosis severity
        self.scan_line.set_color(profile["color"])
        
        # Update legend to reflect the scanned sample
        self.scan_line.set_label(f"Scan: {self.sample_menu.get()}")
        self.legend = self.ax.legend(facecolor='#1e1e1e', edgecolor='#444444', labelcolor='white', fontsize=11, loc='upper right')
        
        self.canvas.draw()

if __name__ == "__main__":
    app = BiosensorDashboard()
    app.mainloop()
