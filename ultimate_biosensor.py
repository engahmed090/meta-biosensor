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
import webbrowser

# Appearance configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UltimateBiosensorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Ultimate Digital Twin Biosensor & HTML AI Reporter")
        self.geometry("1600x1000")
        
        # Maximize the window automatically
        self.after(0, lambda: self.state('zoomed'))
        
        self.configure(fg_color="#050505")
        
        # Extended AI Database with Severity Classification
        self.profiles = {
            "Normal Blood (Reference)": {"f_res": 9.2, "depth": -40.0, "color": "#00FF00", "severity": "HEALTHY"},
            "Chronic Diabetes (High Glucose)": {"f_res": 9.4, "depth": -38.0, "color": "#FFA500", "severity": "CHRONIC"},
            "High Cholesterol": {"f_res": 9.6, "depth": -39.0, "color": "#FFD700", "severity": "CHRONIC"},
            "Breast Cancer (MCF-7)": {"f_res": 8.8, "depth": -35.0, "color": "#FF3333", "severity": "CRITICAL"},
            "Prostate Cancer (PC-3)": {"f_res": 8.9, "depth": -32.0, "color": "#FF00FF", "severity": "CRITICAL"},
            "Lung Cancer (A549)": {"f_res": 8.6, "depth": -30.0, "color": "#FF8C00", "severity": "CRITICAL"},
            "Blood Cancer (Leukemia)": {"f_res": 8.2, "depth": -28.0, "color": "#FF0000", "severity": "CRITICAL"}
        }
        
        self.is_scanning = False
        self.em_wave_plots = []
        self.last_scan_result = None
        self.droplet_surface = None
        
        self.setup_ui()
        self.setup_plots()
        
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(self, width=500, fg_color="#0a0a0a", border_width=1, border_color="#222222")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.left_panel.grid_rowconfigure(10, weight=1)
        
        ctk.CTkLabel(
            self.left_panel, 
            text="DIGITAL TWIN\nLABORATORY", 
            font=ctk.CTkFont(family="Courier New", size=44, weight="bold"), 
            text_color="#00FFFF"
        ).grid(row=0, column=0, padx=25, pady=(40, 25))
        
        self.patient_entry = ctk.CTkEntry(self.left_panel, placeholder_text="Enter Patient Name...", height=50, font=ctk.CTkFont(size=18))
        self.patient_entry.grid(row=1, column=0, padx=25, pady=15, sticky="ew")
        
        self.calib_btn = ctk.CTkButton(self.left_panel, text="Calibrate Reference System", height=60, font=ctk.CTkFont(size=18, weight="bold"), fg_color="#222222", hover_color="#333333", command=self.calibrate)
        self.calib_btn.grid(row=2, column=0, padx=25, pady=15, sticky="ew")
        
        ctk.CTkLabel(self.left_panel, text="Select Biomaterial Sample:", font=ctk.CTkFont(size=18, weight="bold")).grid(row=3, column=0, padx=25, pady=(20, 5), sticky="w")
        
        self.sample_var = ctk.StringVar(value="Normal Blood (Reference)")
        self.sample_menu = ctk.CTkOptionMenu(self.left_panel, values=list(self.profiles.keys()), variable=self.sample_var, height=45, font=ctk.CTkFont(size=16))
        self.sample_menu.grid(row=4, column=0, padx=25, pady=10, sticky="ew")
        
        self.scan_btn = ctk.CTkButton(self.left_panel, text="INITIATE AI SCAN", height=70, font=ctk.CTkFont(size=24, weight="bold"), fg_color="#880000", hover_color="#aa0000", command=self.run_scan, state="disabled")
        self.scan_btn.grid(row=5, column=0, padx=25, pady=30, sticky="ew")
        
        self.report_btn = ctk.CTkButton(self.left_panel, text="Generate Official HTML Lab Report", height=60, font=ctk.CTkFont(size=18, weight="bold"), fg_color="#0055ff", hover_color="#0033aa", command=self.generate_html_report)
        self.report_btn.grid(row=6, column=0, padx=25, pady=15, sticky="ew")
        
        ctk.CTkLabel(self.left_panel, text="AI DIAGNOSTIC TERMINAL", font=ctk.CTkFont(family="Courier New", size=20, weight="bold"), text_color="#00ffcc").grid(row=7, column=0, padx=25, pady=(25, 0), sticky="w")
        
        self.terminal = ctk.CTkTextbox(self.left_panel, fg_color="#020804", text_color="#00ff00", font=ctk.CTkFont(family="Courier New", size=20, weight="bold"), border_width=2, border_color="#00ffcc")
        self.terminal.grid(row=8, column=0, padx=25, pady=15, sticky="nsew", rowspan=2)
        self.terminal.insert("end", "System Initialized.\nWaiting for calibration...\n")
        self.terminal.configure(state="disabled")

    def setup_plots(self):
        plt.style.use('dark_background')
        
        self.right_panel = ctk.CTkFrame(self, fg_color="#050505")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        self.top_right = ctk.CTkFrame(self.right_panel, corner_radius=15, fg_color="#0a0a0a", border_width=1, border_color="#222222")
        self.top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        self.bottom_right = ctk.CTkFrame(self.right_panel, corner_radius=15, fg_color="#0a0a0a", border_width=1, border_color="#222222")
        self.bottom_right.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # --- Ultra-Realistic 3D Digital Twin Setup ---
        self.fig3d = plt.Figure(figsize=(10, 8), facecolor='#0a0a0a')
        self.ax3d = self.fig3d.add_subplot(111, projection='3d')
        self.ax3d.set_facecolor('#0a0a0a')
        self.ax3d.axis('off')
        
        self.draw_3d_lab()
        
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, master=self.top_right)
        self.canvas3d.draw()
        self.canvas3d.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- 2D VNA Screen ---
        self.fig2d = plt.Figure(figsize=(10, 6), facecolor='#0a0a0a')
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.set_facecolor('#020202')
        self.ax2d.set_title("Live Vector Network Analyzer Display", color='#00FFFF', fontsize=22, fontweight='bold', pad=20)
        self.ax2d.set_xlabel("Frequency (GHz)", color='#dddddd', fontsize=18)
        self.ax2d.set_ylabel("S₁₁ Return Loss (dB)", color='#dddddd', fontsize=18)
        self.ax2d.set_xlim(8, 11)
        self.ax2d.set_ylim(-45, 0)
        self.ax2d.grid(True, linestyle='--', color='#222222')
        self.ax2d.tick_params(labelsize=14)
        
        for spine in self.ax2d.spines.values():
            spine.set_color('#333333')
            
        self.f_array = np.linspace(8, 11, 500)
        self.ref_line, = self.ax2d.plot([], [], color='#666666', linestyle='--', linewidth=3, label="Reference Baseline")
        self.scan_line, = self.ax2d.plot([], [], color='#00FFFF', linewidth=4, label="Active Scan")
        self.legend2d = self.ax2d.legend(facecolor='#0a0a0a', edgecolor='#333333', loc='upper right', labelcolor='white', fontsize=16)
        
        self.canvas2d = FigureCanvasTkAgg(self.fig2d, master=self.bottom_right)
        self.canvas2d.draw()
        self.canvas2d.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def draw_cylinder(self, ax, x_start, y_center, z_center, radius, length, color, orientation='x'):
        z = np.linspace(0, length, 15)
        theta = np.linspace(0, 2*np.pi, 20)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_c = radius * np.cos(theta_grid)
        y_c = radius * np.sin(theta_grid)
        
        if orientation == 'x':
            X = z_grid + x_start
            Y = x_c + y_center
            Z = y_c + z_center
        return ax.plot_surface(X, Y, Z, color=color, alpha=1.0, shade=True)

    def draw_hemisphere(self, ax, xc, yc, zc, radius, color):
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi / 2, 20) 
        X = xc + radius * np.outer(np.cos(u), np.sin(v))
        Y = yc + radius * np.outer(np.sin(u), np.sin(v))
        Z = zc + radius * np.outer(np.ones(np.size(u)), np.cos(v))
        return ax.plot_surface(X, Y, Z, color=color, alpha=0.9, shade=True, antialiased=True)

    def draw_3d_lab(self):
        # Extremely zoomed-in limits to fill the entire 3D frame
        self.ax3d.set_xlim(-11.5, 3.5)
        self.ax3d.set_ylim(-4.5, 4.5)
        self.ax3d.set_zlim(0, 14.5)
        self.ax3d.view_init(elev=15, azim=40)
        
        # 1. VNA Machine (Main Body & Ports)
        self.draw_rect_3d(self.ax3d, -9, 0, 0, 5, 8, 12, color='#888888', edge_color='#555555')
        # Bright Screen on front face (Right face is at x = -6.5)
        self.draw_rect_3d(self.ax3d, -6.45, -1, 5, 0.15, 5, 5, color='#00FFFF', edge_color='#008B8B')
        # VNA RF Port (Cylinder protruding from front panel)
        self.draw_cylinder(self.ax3d, -6.5, 2.0, 8.0, 0.4, 0.8, color='silver', orientation='x')
        
        # 2. Pyramidal Horn Antenna (Brass/Gold)
        self.draw_realistic_horn(self.ax3d, 0, 0, 14, 11, 5)
        
        # 3. The Coaxial Cable
        t = np.linspace(0, 1, 60)
        cx = -5.7 + 5.1*t
        cy = 2.0 * (1 - t)
        cz = 8.0 * (1 - t) + 12.5 * t - 4.5*np.sin(np.pi*t) 
        self.ax3d.plot(cx, cy, cz, color='#1A1A1A', linewidth=6, solid_capstyle='round')
        
        # 4. Metamaterial Absorber Sensor 
        self.draw_rect_3d(self.ax3d, 0, 0, 0, 7, 7, 0.8, color='#2e8b57', edge_color='#006400') # Green FR-4 Base
        self.draw_rect_3d(self.ax3d, 0, 0, 0.8, 3, 3, 0.1, color='#FF8C00', edge_color='#CD6600') # Copper Patch
        
        # 5. Blood Droplet Hemisphere
        self.droplet_surface = self.draw_hemisphere(self.ax3d, 0, 0, 0.9, 0.6, color='#FF0000')

    def draw_rect_3d(self, ax, xc, yc, zc, w, d, h, color, edge_color, alpha=1.0):
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
        poly3d = Poly3DCollection(faces, facecolors=color, linewidths=1.2, edgecolors=edge_color, alpha=alpha, shade=True)
        ax.add_collection3d(poly3d)

    def draw_realistic_horn(self, ax, xc, yc, z_top, z_flare, z_bottom):
        w_guide = 1.2
        # Waveguide Box
        self.draw_rect_3d(ax, xc, yc, z_flare, w_guide, w_guide, z_top-z_flare, color='#b5a642', edge_color='#8B6508')
        
        w_top = w_guide / 2
        w_bot = 5.5 / 2
        
        t1, t2, t3, t4 = [xc-w_top, yc-w_top, z_flare], [xc+w_top, yc-w_top, z_flare], [xc+w_top, yc+w_top, z_flare], [xc-w_top, yc+w_top, z_flare]
        b1, b2, b3, b4 = [xc-w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc+w_bot, z_bottom], [xc-w_bot, yc+w_bot, z_bottom]
        
        # Hollow bottom
        faces = [[t1, t2, b2, b1], [t2, t3, b3, b2], [t3, t4, b4, b3], [t4, t1, b1, b4]]
        poly3d = Poly3DCollection(faces, facecolors='#FFD700', edgecolors='#B8860B', linewidths=1.5, shade=True)
        ax.add_collection3d(poly3d)

    def terminal_print(self, text):
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"> {text}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def generate_noisy_s11(self, f, f_res, depth, q_factor=20):
        gamma = f_res / (2 * q_factor)
        dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
        noise = np.random.normal(0, 0.4, size=len(f)) + np.random.uniform(-0.2, 0.2, size=len(f))
        ripple = 0.5 * np.sin(2 * np.pi * 5 * f)
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
        if self.droplet_surface is not None:
            self.droplet_surface.remove()
            self.droplet_surface = None
            
        for z in np.linspace(6, 1.2, 10):
            self.droplet = self.ax3d.scatter([0], [0], [z], color='red', s=250)
            self.canvas3d.draw()
            time.sleep(0.04)
            if z > 1.2: self.droplet.remove()
            
        self.droplet_surface = self.draw_hemisphere(self.ax3d, 0, 0, 0.9, 0.6, color='#FF0000')
        self.canvas3d.draw()
        
        self.terminal_print("Sample settled. Initiating Microwave Sweep...")
        time.sleep(0.5)
        
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
                    wave, = self.ax3d.plot(wx, wy, [current_z]*20, color='cyan', alpha=0.5, linewidth=3.5)
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
        
        time.sleep(0.5)
        self.after(0, self.terminal_print, "Extracting Features: Resonant Freq, Q-Factor, Min Amplitude...")
        time.sleep(1.0)
        
        delta_f = (prof['f_res'] - 9.2) * 1000
        self.after(0, self.terminal_print, f"Comparing against Baseline... Δf = {delta_f:+.0f} MHz")
        time.sleep(1.2)
        
        diag = sample
        if prof['severity'] == "HEALTHY":
            conf = random.uniform(97.5, 99.2)
        else:
            conf = random.uniform(92.1, 98.8)
            
        self.after(0, self.terminal_print, f"AI Prediction: {diag}")
        time.sleep(0.5)
        self.after(0, self.terminal_print, f"Confidence Score: {conf:.2f}%")
        
        self.last_scan_result = {
            "f_res": prof['f_res'],
            "depth": prof['depth'],
            "delta_f": delta_f,
            "diagnosis": diag,
            "confidence": conf,
            "severity": prof['severity']
        }
        
        self.after(0, self.finish_scan)
        
    def finish_scan(self):
        self.is_scanning = False
        self.scan_btn.configure(state="normal")
        self.scan_line.set_label(f"Active Scan ({self.sample_var.get()})")
        self.legend2d = self.ax2d.legend(facecolor='#0a0a0a', edgecolor='#333333', loc='upper right', labelcolor='white', fontsize=16)
        self.canvas2d.draw()

    def generate_html_report(self):
        patient_name = self.patient_entry.get().strip()
        if not patient_name:
            patient_name = "UNKNOWN_PATIENT"
            
        if not self.last_scan_result:
            self.terminal_print("ERROR: No scan data available. Please run a scan first.")
            return
            
        res = self.last_scan_result
        filename = f"{patient_name.replace(' ', '_')}_Report.html"
        
        severity = res['severity']
        
        if severity == "HEALTHY":
            alert_color = "#155724"
            alert_bg = "#d4edda"
            alert_border = "#c3e6cb"
            doctor_notes = "The microwave dielectric profile of the blood sample aligns perfectly with healthy baseline metrics. No cellular abnormalities or metabolic imbalances detected. Continue standard healthy lifestyle routines."
            severity_label = "HEALTHY"
        elif severity == "CHRONIC":
            alert_color = "#856404"
            alert_bg = "#fff3cd"
            alert_border = "#ffeeba"
            doctor_notes = "The S11 parameter shift indicates a chronic metabolic condition (e.g., elevated glucose or lipids). While this is a manageable chronic disease, it requires lifestyle modifications, dietary control, and routine follow-ups. This is highly treatable and not immediately life-threatening if managed properly."
            severity_label = "CHRONIC (MANAGEABLE)"
        else: # CRITICAL
            alert_color = "#721c24"
            alert_bg = "#f8d7da"
            alert_border = "#f5c6cb"
            doctor_notes = "<strong>URGENT:</strong> The significant frequency shift (&Delta;f) indicates severe cellular abnormalities consistent with malignant tissue presence. Immediate referral to an oncology specialist for comprehensive biopsy and imaging is strictly required."
            severity_label = "CRITICAL (ONCOLOGY)"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Diagnostic Report - {patient_name}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 40px; }}
                .container {{ background-color: #fff; max-width: 800px; margin: auto; padding: 40px; border-top: 6px solid #0056b3; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 4px; }}
                .header {{ border-bottom: 2px solid #0056b3; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
                .header h1 {{ color: #0056b3; margin: 0; font-size: 28px; letter-spacing: 1px; }}
                .header p {{ color: #777; margin: 8px 0 0 0; font-size: 15px; font-weight: bold; }}
                .info-section {{ display: flex; justify-content: space-between; margin-bottom: 30px; font-size: 16px; background: #f8f9fa; padding: 15px; border-radius: 4px; border: 1px solid #e9ecef; }}
                .info-section span {{ font-weight: bold; color: #495057; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 35px; }}
                th, td {{ padding: 14px; border: 1px solid #dee2e6; text-align: left; font-size: 15px; }}
                th {{ background-color: #f8f9fa; color: #0056b3; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
                .alert-box {{ background-color: {alert_bg}; color: {alert_color}; border: 1px solid {alert_border}; padding: 25px; text-align: left; border-radius: 6px; margin-bottom: 40px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }}
                .alert-box .diag-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {alert_border}; padding-bottom: 10px; margin-bottom: 15px; }}
                .alert-box h2 {{ margin: 0; font-size: 22px; text-transform: uppercase; }}
                .alert-box .severity-badge {{ padding: 6px 12px; border-radius: 4px; background-color: {alert_color}; color: #fff; font-size: 14px; font-weight: bold; }}
                .alert-box p.diag {{ margin: 0 0 15px 0; font-size: 20px; font-weight: bold; }}
                .alert-box p.conf {{ font-size: 15px; margin-top: 0; font-weight: normal; }}
                
                .interpretation-section {{ background: #fdfdfe; border-left: 4px solid #0056b3; padding: 20px; margin-bottom: 40px; }}
                .interpretation-section h3 {{ margin-top: 0; color: #0056b3; font-size: 18px; }}
                .interpretation-section p {{ line-height: 1.6; margin-bottom: 0; font-size: 15px; color: #444; }}
                
                .footer {{ margin-top: 60px; font-size: 14px; color: #6c757d; }}
                .signature-box {{ margin-top: 50px; display: flex; justify-content: space-between; }}
                .signature {{ border-top: 1px solid #343a40; width: 250px; padding-top: 10px; text-align: center; font-style: italic; color: #343a40; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ISIA BIOMEDICAL RESEARCH FACILITY</h1>
                    <p>OFFICIAL MICROWAVE BIOSENSOR DIAGNOSTIC REPORT</p>
                </div>
                
                <div class="info-section">
                    <div><span>Patient Name:</span> {patient_name}</div>
                    <div><span>Date & Time:</span> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
                </div>
                
                <table>
                    <tr>
                        <th colspan="2">Raw Microwave Sensor Data</th>
                    </tr>
                    <tr>
                        <td><strong>Reference Baseline Frequency</strong></td>
                        <td>9.200 GHz</td>
                    </tr>
                    <tr>
                        <td><strong>Detected Resonance Frequency</strong></td>
                        <td>{res['f_res']:.3f} GHz</td>
                    </tr>
                    <tr>
                        <td><strong>Frequency Shift (&Delta;f)</strong></td>
                        <td>{res['delta_f']:+.0f} MHz</td>
                    </tr>
                    <tr>
                        <td><strong>S11 Minimum Return Loss</strong></td>
                        <td>{res['depth']:.1f} dB</td>
                    </tr>
                </table>
                
                <div class="alert-box">
                    <div class="diag-header">
                        <h2>AI Diagnosis Result</h2>
                        <div class="severity-badge">{severity_label}</div>
                    </div>
                    <p class="diag">{res['diagnosis']}</p>
                    <p class="conf">AI Confidence Score: <strong>{res['confidence']:.2f}%</strong></p>
                </div>
                
                <div class="interpretation-section">
                    <h3>Detailed Clinical Interpretation & Doctor's Notes</h3>
                    <p>{doctor_notes}</p>
                </div>
                
                <div class="footer">
                    <p><strong>Remarks:</strong> This diagnostic test utilizes advanced metamaterial electromagnetic absorption for cellular dielectric profiling. Signals are processed through high-frequency Vector Network Analyzers to extract precise cellular shifts.</p>
                    <div class="signature-box">
                        <div></div>
                        <div class="signature">
                            Lead Biomedical Engineer
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        filepath = os.path.abspath(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        self.terminal_print(f"HTML Report Generated: {filename}")
        
        try:
            webbrowser.open('file://' + filepath)
        except Exception as e:
            self.terminal_print(f"Failed to open browser: {e}")

if __name__ == "__main__":
    app = UltimateBiosensorApp()
    app.mainloop()
