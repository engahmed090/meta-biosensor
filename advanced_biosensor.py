import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import threading
import time
import random

# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MockAIEngine:
    """Mock AI Diagnostic Engine using distance-based logic."""
    def __init__(self):
        self.reference_freq = 9.2 # GHz
    
    def analyze(self, current_freq):
        # Calculate Delta f in MHz
        delta_f_mhz = (current_freq - self.reference_freq) * 1000
        
        # Knowledge base of known classes
        classes = {
            "Normal Blood": 9.2,
            "Breast Cancer (MCF-7)": 8.8,
            "Leukemia": 8.5
        }
        
        # Distance-based classification (K-Nearest Neighbors logic)
        distances = {k: abs(current_freq - v) for k, v in classes.items()}
        best_match = min(distances, key=distances.get)
        min_dist = distances[best_match]
        
        # Confidence calculation
        confidence = max(0.0, 100.0 - (min_dist * 100))
        if best_match != "Normal Blood":
            # Add some realistic mock AI variance
            confidence -= random.uniform(0.1, 3.5) 
        
        confidence = min(99.9, max(0.1, confidence))
        
        return best_match, confidence, delta_f_mhz

class AdvancedBiosensorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Advanced 3D Metamaterial Biosensor Simulator")
        self.geometry("1280x850")
        self.configure(fg_color="#0a0a0a")
        
        self.ai_engine = MockAIEngine()
        
        # Physical Profiles
        self.profiles = {
            "Normal Blood": {"f_res": 9.2, "depth": -40.0, "color": "#00FF00"},
            "Breast Cancer (MCF-7)": {"f_res": 8.8, "depth": -38.0, "color": "#FF3333"},
            "Leukemia": {"f_res": 8.5, "depth": -25.0, "color": "#FF9933"} # Shallower dip
        }
        
        self.setup_ui()
        self.setup_plots()
        
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ---------------------------------------------------------
        # Left Panel (Controls & AI)
        # ---------------------------------------------------------
        self.left_panel = ctk.CTkFrame(self, width=380, corner_radius=0, fg_color="#121212", border_width=1, border_color="#222222")
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(9, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.left_panel, 
            text="AI BIOSENSOR\nCONTROL", 
            font=ctk.CTkFont(family="Roboto", size=30, weight="bold"), 
            text_color="#00FFFF"
        ).grid(row=0, column=0, padx=20, pady=(40, 30))
        
        # Calibrate Button
        self.calib_btn = ctk.CTkButton(
            self.left_panel, 
            text="Calibrate Reference\n(Normal Blood)", 
            height=55, 
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#333333", 
            hover_color="#444444", 
            command=self.calibrate
        )
        self.calib_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Sample Selection
        ctk.CTkLabel(self.left_panel, text="Select Blood Sample:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cccccc").grid(row=2, column=0, padx=20, pady=(30, 5), sticky="w")
        
        self.sample_var = ctk.StringVar(value="Breast Cancer (MCF-7)")
        self.sample_menu = ctk.CTkOptionMenu(
            self.left_panel, 
            values=["Breast Cancer (MCF-7)", "Leukemia"], 
            variable=self.sample_var,
            font=ctk.CTkFont(size=14),
            height=35
        )
        self.sample_menu.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        # Scan Button
        self.scan_btn = ctk.CTkButton(
            self.left_panel, 
            text="RUN AI SCAN", 
            height=55, 
            font=ctk.CTkFont(size=18, weight="bold"), 
            fg_color="#aa0000", 
            hover_color="#cc0000", 
            command=self.run_scan, 
            state="disabled"
        )
        self.scan_btn.grid(row=4, column=0, padx=20, pady=30, sticky="ew")
        
        # AI Engine Output Panel
        self.ai_frame = ctk.CTkFrame(self.left_panel, fg_color="#181818", border_width=1, border_color="#00FFFF")
        self.ai_frame.grid(row=5, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(self.ai_frame, text="AI DIAGNOSTIC ENGINE", font=ctk.CTkFont(size=15, weight="bold"), text_color="#00FFFF").pack(pady=(15, 5))
        
        self.ai_diag_label = ctk.CTkLabel(self.ai_frame, text="Awaiting Scan...", font=ctk.CTkFont(size=16), text_color="#ffffff", wraplength=300)
        self.ai_diag_label.pack(pady=15, padx=15)
        
        self.ai_conf_label = ctk.CTkLabel(self.ai_frame, text="Confidence: --%", font=ctk.CTkFont(size=16, weight="bold"))
        self.ai_conf_label.pack(pady=5)
        
        self.ai_shift_label = ctk.CTkLabel(self.ai_frame, text="Δf: -- MHz", font=ctk.CTkFont(size=16, weight="bold"))
        self.ai_shift_label.pack(pady=(5, 20))
        
        # ---------------------------------------------------------
        # Right Panel (3D Sensor + 2D VNA)
        # ---------------------------------------------------------
        self.right_panel = ctk.CTkFrame(self, fg_color="#0a0a0a")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        self.top_right = ctk.CTkFrame(self.right_panel, corner_radius=10, fg_color="#161616", border_width=1, border_color="#333333")
        self.top_right.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        
        self.bottom_right = ctk.CTkFrame(self.right_panel, corner_radius=10, fg_color="#161616", border_width=1, border_color="#333333")
        self.bottom_right.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

    def setup_plots(self):
        plt.style.use('dark_background')
        
        # --- 3D Plot (Top Right) ---
        self.fig3d = plt.Figure(figsize=(6, 4), facecolor='#161616')
        self.ax3d = self.fig3d.add_subplot(111, projection='3d')
        self.ax3d.set_facecolor('#161616')
        
        self.ax3d.set_xlim(-10, 10)
        self.ax3d.set_ylim(-10, 10)
        self.ax3d.set_zlim(0, 15)
        self.ax3d.axis('off') # Clean futuristic look
        self.ax3d.set_title("3D Metamaterial Sensor View", color='#00FFFF', pad=0)
        
        # Draw Substrate (FR-4): P=16mm, thickness=1.6mm
        self.draw_rect_3d(self.ax3d, 0, 0, 0, 16, 16, 1.6, '#2e4d3a', alpha=0.85)
        # Draw Patch (Copper): wm=6.4mm
        self.draw_rect_3d(self.ax3d, 0, 0, 1.6, 6.4, 6.4, 0.1, '#d47835', alpha=1.0)
        
        # Draw VNA Probe
        self.ax3d.plot([0, 0], [0, 0], [1.8, 12], color='silver', linewidth=3)
        self.ax3d.plot([-1, 1], [0, 0], [12, 12], color='silver', linewidth=5)
        
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, master=self.top_right)
        self.canvas3d.draw()
        self.canvas3d.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- 2D Plot (Bottom Right) ---
        self.fig2d = plt.Figure(figsize=(6, 4), facecolor='#161616')
        self.ax2d = self.fig2d.add_subplot(111)
        self.ax2d.set_facecolor('#0d0d0d')
        
        self.ax2d.set_title("VNA Screen (S₁₁ Response)", color='white', pad=10, fontsize=14, fontweight='bold')
        self.ax2d.set_xlabel("Frequency (GHz)", color='#dddddd')
        self.ax2d.set_ylabel("S₁₁ (dB)", color='#dddddd')
        self.ax2d.set_xlim(8, 11)
        self.ax2d.set_ylim(-45, 0)
        self.ax2d.grid(True, linestyle='--', color='#333333')
        
        for spine in self.ax2d.spines.values():
            spine.set_color('#444444')
            
        self.f_array = np.linspace(8, 11, 500)
        self.ref_line, = self.ax2d.plot([], [], color='#888888', linestyle='--', linewidth=2, label="Reference (Normal Blood)")
        self.scan_line, = self.ax2d.plot([], [], color='#FF0000', linewidth=3, label="Current Scan")
        self.legend2d = self.ax2d.legend(facecolor='#161616', edgecolor='#444444', loc='upper right')
        
        self.canvas2d = FigureCanvasTkAgg(self.fig2d, master=self.bottom_right)
        self.canvas2d.draw()
        self.canvas2d.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
    def draw_rect_3d(self, ax, x_center, y_center, z_bottom, width, height, thickness, color, alpha=1.0):
        """Helper to draw 3D rectangular prisms for the metamaterial patch."""
        x0, x1 = x_center - width/2, x_center + width/2
        y0, y1 = y_center - height/2, y_center + height/2
        z0, z1 = z_bottom, z_bottom + thickness

        faces = [
            [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], # Bottom
            [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], # Top
            [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], # Front
            [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]], # Right
            [[x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1]], # Back
            [[x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1]]  # Left
        ]
        poly3d = Poly3DCollection(faces, facecolors=color, linewidths=0.5, edgecolors='black', alpha=alpha)
        ax.add_collection3d(poly3d)

    def generate_s11(self, f, f_res, depth, q_factor=20):
        """Mathematical generation of realistic S11 Lorentzian curve."""
        gamma = f_res / (2 * q_factor)
        dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
        return dip

    def calibrate(self):
        """Draws the Normal Blood baseline."""
        prof = self.profiles["Normal Blood"]
        y = self.generate_s11(self.f_array, prof["f_res"], prof["depth"])
        self.ref_line.set_data(self.f_array, y)
        self.canvas2d.draw()
        
        self.calib_btn.configure(text="Reference Calibrated ✓", fg_color="#006600", state="disabled")
        self.scan_btn.configure(state="normal", fg_color="#0055ff", hover_color="#0033cc")

    def run_scan(self):
        """Triggers the full 3D and 2D scan sequence."""
        self.scan_btn.configure(state="disabled")
        self.sample_menu.configure(state="disabled")
        self.ai_diag_label.configure(text="Scanning...", text_color="#aaaaaa")
        self.ai_conf_label.configure(text="Confidence: --%", text_color="#aaaaaa")
        self.ai_shift_label.configure(text="Δf: -- MHz", text_color="#aaaaaa")
        
        # Clear previous scan line
        self.scan_line.set_data([], [])
        self.canvas2d.draw()
        
        sample = self.sample_var.get()
        threading.Thread(target=self.animate_process, args=(sample,), daemon=True).start()

    def animate_process(self, sample):
        # 1. 3D Droplet falling animation
        if hasattr(self, 'droplet'):
            self.droplet.remove()
            
        for z in np.linspace(10, 1.8, 20):
            self.droplet = self.ax3d.scatter([0], [0], [z], color='red', s=80)
            self.canvas3d.draw()
            time.sleep(0.02)
            if z > 1.8:
                self.droplet.remove()
                
        # Leave droplet on the patch
        self.droplet = self.ax3d.scatter([0], [0], [1.75], color='red', s=120)
        self.canvas3d.draw()
                
        # 2. 2D VNA Scan animation
        prof = self.profiles[sample]
        target_y = self.generate_s11(self.f_array, prof["f_res"], prof["depth"], q_factor=15 if sample=="Leukemia" else 25)
        self.scan_line.set_color(prof["color"])
        
        steps = 50
        for i in range(1, steps + 1):
            idx = int(len(self.f_array) * (i/steps))
            self.scan_line.set_data(self.f_array[:idx], target_y[:idx])
            self.canvas2d.draw()
            time.sleep(0.015)
            
        # 3. AI Diagnosis Logic execution
        diag, conf, delta = self.ai_engine.analyze(prof["f_res"])
        
        # 4. Update UI safely
        self.after(0, self.display_results, diag, conf, delta, prof["color"])

    def display_results(self, diag, conf, delta, color):
        self.scan_btn.configure(state="normal")
        self.sample_menu.configure(state="normal")
        
        # Update Legend
        self.scan_line.set_label(f"Scan: {self.sample_var.get()}")
        self.legend2d = self.ax2d.legend(facecolor='#161616', edgecolor='#444444', loc='upper right', labelcolor='white')
        self.canvas2d.draw()
        
        # Display AI Results
        if diag == "Normal Blood":
            msg = "AI Diagnosis: Normal Blood Profile Detected."
        else:
            msg = f"AI Diagnosis: {diag} Detected."
            
        self.ai_diag_label.configure(text=msg, text_color=color)
        
        conf_color = "#00FF00" if conf > 90 else "#FFFF00"
        self.ai_conf_label.configure(text=f"Confidence: {conf:.1f}%", text_color=conf_color)
        
        shift_text = f"+{abs(delta):.0f}" if delta > 0 else f"-{abs(delta):.0f}"
        self.ai_shift_label.configure(text=f"Δf: {shift_text} MHz", text_color="#ffffff")

if __name__ == "__main__":
    app = AdvancedBiosensorApp()
    app.mainloop()
