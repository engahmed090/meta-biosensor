import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import threading
import time
import random
import os
import datetime

# Appearance configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DigitalTwinApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Ultra-Realistic Digital Twin Biosensor & AI")
        self.geometry("1500x950")
        self.configure(fg_color="#050505") # Extremely dark background
        
        # Extended AI Database
        self.profiles = {
            "Normal Blood (Reference)": {"f_res": 9.2, "depth": -40.0, "color": "#00FF00"},
            "Breast Cancer (MCF-7)": {"f_res": 8.8, "depth": -35.0, "color": "#FF3333"},
            "Prostate Cancer (PC-3)": {"f_res": 8.9, "depth": -32.0, "color": "#FF00FF"},
            "Lung Cancer (A549)": {"f_res": 8.6, "depth": -30.0, "color": "#FFA500"},
            "Blood Cancer (Severe Leukemia)": {"f_res": 8.2, "depth": -25.0, "color": "#FF0000"}
        }
        
        self.is_scanning = False
        self.em_wave_plots = []
        self.last_scan_result = None
        
        self.setup_ui()
        self.setup_plots()
        
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(self, width=420, fg_color="#0d0d0d", border_width=1, border_color="#1a1a1a")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.left_panel.grid_rowconfigure(10, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.left_panel, 
            text="DIGITAL TWIN\nLABORATORY", 
            font=ctk.CTkFont(family="Courier New", size=36, weight="bold"), 
            text_color="#00FFFF"
        ).grid(row=0, column=0, padx=20, pady=(30, 20))
        
        # Patient Name Entry
        self.patient_entry = ctk.CTkEntry(self.left_panel, placeholder_text="Enter Patient Name...", height=40, font=ctk.CTkFont(size=14))
        self.patient_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Buttons
        self.calib_btn = ctk.CTkButton(self.left_panel, text="Calibrate Reference System", height=45, fg_color="#222222", hover_color="#333333", command=self.calibrate)
        self.calib_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.left_panel, text="Select Biomaterial Sample:", font=ctk.CTkFont(size=14)).grid(row=3, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.sample_var = ctk.StringVar(value="Breast Cancer (MCF-7)")
        self.sample_menu = ctk.CTkOptionMenu(self.left_panel, values=list(self.profiles.keys()), variable=self.sample_var, height=35)
        self.sample_menu.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        self.scan_btn = ctk.CTkButton(self.left_panel, text="INITIATE AI SCAN", height=55, font=ctk.CTkFont(size=18, weight="bold"), fg_color="#880000", hover_color="#aa0000", command=self.run_scan, state="disabled")
        self.scan_btn.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.report_btn = ctk.CTkButton(self.left_panel, text="Generate Official Lab Report", height=45, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#0055ff", hover_color="#0033aa", command=self.generate_report)
        self.report_btn.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        # AI Terminal
        ctk.CTkLabel(self.left_panel, text="AI DIAGNOSTIC TERMINAL", font=ctk.CTkFont(family="Courier New", size=16, weight="bold"), text_color="#00ffcc").grid(row=7, column=0, padx=20, pady=(20, 0), sticky="w")
        
        self.terminal = ctk.CTkTextbox(self.left_panel, fg_color="#020804", text_color="#00ff00", font=ctk.CTkFont(family="Courier New", size=16, weight="bold"), border_width=2, border_color="#00ffcc")
        self.terminal.grid(row=8, column=0, padx=20, pady=10, sticky="nsew", rowspan=2)
        self.terminal.insert("end", "System Initialized.\nWaiting for calibration...\n")
        self.terminal.configure(state="disabled")

    def setup_plots(self):
        plt.style.use('dark_background')
        
        # --- Right Panel ---
        self.right_panel = ctk.CTkFrame(self, fg_color="#050505")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        self.top_right = ctk.CTkFrame(self.right_panel, corner_radius=15, fg_color="#0a0a0a", border_width=1, border_color="#222222")
        self.top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        self.bottom_right = ctk.CTkFrame(self.right_panel, corner_radius=15, fg_color="#0a0a0a", border_width=1, border_color="#222222")
        self.bottom_right.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # --- Massive 3D Digital Twin Setup ---
        self.fig3d = plt.Figure(figsize=(8, 6), facecolor='#0a0a0a')
        self.ax3d = self.fig3d.add_subplot(111, projection='3d')
        self.ax3d.set_facecolor('#0a0a0a')
        self.ax3d.axis('off')
        
        # Draw Lab Environment Elements
        self.draw_3d_lab()
        
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, master=self.top_right)
        self.canvas3d.draw()
        self.canvas3d.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- 2D VNA Screen ---
        self.fig2d = plt.Figure(figsize=(8, 5), facecolor='#0a0a0a')
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.set_facecolor('#020202')
        self.ax2d.set_title("Live Vector Network Analyzer Display", color='#00FFFF', fontsize=16, fontweight='bold', pad=15)
        self.ax2d.set_xlabel("Frequency (GHz)", color='#dddddd', fontsize=14)
        self.ax2d.set_ylabel("S₁₁ Return Loss (dB)", color='#dddddd', fontsize=14)
        self.ax2d.set_xlim(8, 11)
        self.ax2d.set_ylim(-45, 0)
        self.ax2d.grid(True, linestyle='--', color='#222222')
        self.ax2d.tick_params(labelsize=12)
        
        for spine in self.ax2d.spines.values():
            spine.set_color('#333333')
            
        self.f_array = np.linspace(8, 11, 500)
        self.ref_line, = self.ax2d.plot([], [], color='#666666', linestyle='--', linewidth=2, label="Reference Baseline")
        self.scan_line, = self.ax2d.plot([], [], color='#00FFFF', linewidth=3, label="Active Scan")
        self.legend2d = self.ax2d.legend(facecolor='#0a0a0a', edgecolor='#333333', loc='upper right', labelcolor='white', fontsize=12)
        
        self.canvas2d = FigureCanvasTkAgg(self.fig2d, master=self.bottom_right)
        self.canvas2d.draw()
        self.canvas2d.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def draw_3d_lab(self):
        # Tighter limits for a more zoomed-in, massive look
        self.ax3d.set_xlim(-12, 6)
        self.ax3d.set_ylim(-6, 6)
        self.ax3d.set_zlim(0, 16)
        self.ax3d.view_init(elev=18, azim=45)
        
        # 1. VNA Machine (Large robust box at left)
        self.draw_rect_3d(self.ax3d, -9, 0, 0, 5, 8, 12, color='#111111', edge_color='#444444', alpha=1.0)
        # VNA Screen glow
        self.draw_rect_3d(self.ax3d, -6.4, 0, 5, 0.2, 6, 5, color='#003366', edge_color='#00FFFF', alpha=1.0)
        
        # 2. Heavy Coaxial Cable
        t = np.linspace(0, 1, 50)
        cx = -6.5 + 6.5*t
        cy = np.zeros(50)
        cz = 10 + 3*np.sin(np.pi*t) # Cable arcs up and to the horn
        self.ax3d.plot(cx, cy, cz, color='#1a1a1a', linewidth=6, solid_capstyle='round')
        
        # 3. Robust Horn Antenna
        self.draw_horn_antenna(self.ax3d, 0, 0, 6, 12)
        
        # 4. Metamaterial Absorber Sensor (Base)
        self.draw_rect_3d(self.ax3d, 0, 0, 0, 7, 7, 0.8, color='#2e4d3a', edge_color='#1a3322', alpha=0.95) # Substrate
        self.draw_rect_3d(self.ax3d, 0, 0, 0.8, 3, 3, 0.1, color='#d47835', edge_color='#aa4400', alpha=1.0) # Copper Patch

    def draw_rect_3d(self, ax, xc, yc, zc, w, d, h, color, edge_color='black', alpha=1.0):
        x0, x1 = xc - w/2, xc + w/2
        y0, y1 = yc - d/2, yc + d/2
        z0, z1 = zc, zc + h

        faces = [
            [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], # Bottom
            [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], # Top
            [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], # Front
            [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]], # Right
            [[x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1]], # Back
            [[x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1]]  # Left
        ]
        poly3d = Poly3DCollection(faces, facecolors=color, linewidths=1.5, edgecolors=edge_color, alpha=alpha)
        ax.add_collection3d(poly3d)

    def draw_horn_antenna(self, ax, xc, yc, z_bottom, z_top):
        w_top, w_bot = 1.0, 4.5
        t1, t2, t3, t4 = [xc-w_top, yc-w_top, z_top], [xc+w_top, yc-w_top, z_top], [xc+w_top, yc+w_top, z_top], [xc-w_top, yc+w_top, z_top]
        b1, b2, b3, b4 = [xc-w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc+w_bot, z_bottom], [xc-w_bot, yc+w_bot, z_bottom]
        
        faces = [[t1, t2, b2, b1], [t2, t3, b3, b2], [t3, t4, b4, b3], [t4, t1, b1, b4]]
        poly3d = Poly3DCollection(faces, facecolors='#aaaaaa', linewidths=1.5, edgecolors='#444444', alpha=0.95)
        ax.add_collection3d(poly3d)

    def terminal_print(self, text):
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"> {text}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def generate_noisy_s11(self, f, f_res, depth, q_factor=20):
        gamma = f_res / (2 * q_factor)
        dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
        noise = np.random.normal(0, 0.5, size=len(f)) 
        ripple = 0.6 * np.sin(2 * np.pi * 4 * f)
        return dip + noise + ripple

    def calibrate(self):
        self.terminal.delete("1.0", "end")
        self.terminal_print("Initiating VNA Calibration Sequence...")
        
        prof = self.profiles["Normal Blood (Reference)"]
        y = self.generate_noisy_s11(self.f_array, prof["f_res"], prof["depth"])
        self.ref_line.set_data(self.f_array, y)
        self.canvas2d.draw()
        
        self.calib_btn.configure(text="Reference Calibrated ✓", fg_color="#006600", state="disabled")
        self.scan_btn.configure(state="normal")
        self.terminal_print("Calibration successful. Baseline Locked.")

    def run_scan(self):
        if self.is_scanning: return
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        
        sample = self.sample_var.get()
        self.terminal.delete("1.0", "end")
        self.terminal_print(f"Loading sample: {sample} onto patch...")
        
        threading.Thread(target=self.scan_routine, args=(sample,), daemon=True).start()

    def scan_routine(self, sample):
        # 1. Droplet animation
        if hasattr(self, 'droplet'): self.droplet.remove()
        
        for z in np.linspace(6, 1.2, 10):
            self.droplet = self.ax3d.scatter([0], [0], [z], color='red', s=150)
            self.canvas3d.draw()
            time.sleep(0.04)
            if z > 1.2: self.droplet.remove()
            
        self.droplet = self.ax3d.scatter([0], [0], [1.1], color='red', s=200)
        self.terminal_print("Sample settled. Initiating Microwave Sweep...")
        time.sleep(0.5)
        
        # 2. Sweep + EM waves
        prof = self.profiles[sample]
        q_fac = 12 if "Leukemia" in sample else 20
        target_y = self.generate_noisy_s11(self.f_array, prof["f_res"], prof["depth"], q_factor=q_fac)
        self.scan_line.set_color(prof["color"])
        
        steps = 60
        wave_z = np.linspace(6, 1.5, 6) 
        
        for i in range(1, steps + 1):
            for plot in self.em_wave_plots: plot.remove()
            self.em_wave_plots.clear()
            
            offset = (i % 10) / 10.0 * 1.5
            for wz in wave_z:
                current_z = wz - offset
                if current_z > 1.5:
                    radius = (6 - current_z) * 0.9
                    theta = np.linspace(0, 2*np.pi, 20)
                    wx = radius * np.cos(theta)
                    wy = radius * np.sin(theta)
                    wave, = self.ax3d.plot(wx, wy, [current_z]*20, color='cyan', alpha=0.5, linewidth=2.5)
                    self.em_wave_plots.append(wave)
            
            self.canvas3d.draw()
            
            idx = int(len(self.f_array) * (i/steps))
            self.scan_line.set_data(self.f_array[:idx], target_y[:idx])
            self.canvas2d.draw()
            time.sleep(0.02)
            
        for plot in self.em_wave_plots: plot.remove()
        self.em_wave_plots.clear()
        self.canvas3d.draw()
        
        self.terminal_print("Microwave Sweep Complete.")
        
        # 3. Mock AI Logic
        time.sleep(0.5)
        self.after(0, self.terminal_print, "Extracting Features: Resonant Freq, Q-Factor, Min Amplitude...")
        time.sleep(1.0)
        
        delta_f = (prof['f_res'] - 9.2) * 1000
        self.after(0, self.terminal_print, f"Comparing against Baseline... Δf = {delta_f:+.0f} MHz")
        time.sleep(1.2)
        
        if "Normal" in sample:
            diag = "Normal Blood Profile"
            conf = random.uniform(97.5, 99.2)
        else:
            diag = sample
            conf = random.uniform(92.1, 98.8)
            
        self.after(0, self.terminal_print, f"AI Prediction: {diag}")
        time.sleep(0.5)
        self.after(0, self.terminal_print, f"Confidence Score: {conf:.2f}%")
        
        # Save scan result for report
        self.last_scan_result = {
            "f_res": prof['f_res'],
            "depth": prof['depth'],
            "delta_f": delta_f,
            "diagnosis": diag,
            "confidence": conf
        }
        
        self.after(0, self.finish_scan)
        
    def finish_scan(self):
        self.is_scanning = False
        self.scan_btn.configure(state="normal")
        self.scan_line.set_label(f"Active Scan ({self.sample_var.get()})")
        self.legend2d = self.ax2d.legend(facecolor='#0a0a0a', edgecolor='#333333', loc='upper right', labelcolor='white')
        self.canvas2d.draw()

    def generate_report(self):
        patient_name = self.patient_entry.get().strip()
        if not patient_name:
            patient_name = "UNKNOWN_PATIENT"
            
        if not self.last_scan_result:
            self.terminal_print("ERROR: No scan data available. Please run a scan first.")
            return
            
        res = self.last_scan_result
        filename = f"{patient_name.replace(' ', '_')}_LabReport.txt"
        
        report_content = f"""
=========================================================
      UNIVERSITY & HOSPITAL BIOMEDICAL LABORATORY
      OFFICIAL MICROWAVE BIOSENSOR DIAGNOSTIC REPORT
=========================================================
Date & Time    : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Patient Name   : {patient_name}
---------------------------------------------------------
[ RAW MICROWAVE SENSOR DATA ]
Reference Baseline Freq : 9.200 GHz
Detected Resonance Freq : {res['f_res']:.3f} GHz
Frequency Shift (Δf)    : {res['delta_f']:+.0f} MHz
S11 Minimum Return Loss : {res['depth']:.1f} dB
---------------------------------------------------------
[ ARTIFICIAL INTELLIGENCE DIAGNOSIS ]
AI Prediction           : {res['diagnosis']}
Confidence Score        : {res['confidence']:.2f}%
---------------------------------------------------------
Remarks: 
This test uses advanced Metamaterial Electromagnetic 
absorption for cellular dielectric profiling.

Authorized Signature:
___________________________________
Lead Biomedical Engineer
=========================================================
"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        self.terminal_print(f"Report Generated: {filename}")
        
        try:
            os.startfile(filename)
        except Exception as e:
            self.terminal_print(f"Failed to open report automatically: {e}")

if __name__ == "__main__":
    app = DigitalTwinApp()
    app.mainloop()
