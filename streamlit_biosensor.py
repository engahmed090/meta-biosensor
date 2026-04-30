import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import random
import time
import base64

st.set_page_config(page_title="ISIA BIOMEDICAL", layout="wide")
plt.style.use('dark_background')

# --- CSS Injection ---
svg_bg = """
<svg xmlns='http://www.w3.org/2000/svg' width='200' height='100' viewBox='0 0 200 100'>
    <path d='M0 50 Q 50 0 100 50 T 200 50' fill='none' stroke='#00ffff' stroke-width='1.5' opacity='0.1'/>
    <path d='M0 50 Q 50 100 100 50 T 200 50' fill='none' stroke='#ff00ff' stroke-width='0.5' opacity='0.05'/>
</svg>
"""
b64_bg = base64.b64encode(svg_bg.encode('utf-8')).decode('utf-8')

st.markdown(f"""
<style>
    /* Global Background */
    .stApp {{
        background-color: #0a0f1a;
        background-image: url("data:image/svg+xml;base64,{b64_bg}");
        background-repeat: repeat;
        background-size: 300px;
        color: #e0f2fe;
    }}
    
    /* Header Styling */
    h1 {{
        color: #00ffff !important;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        border-bottom: 2px solid #00ffff;
        padding-bottom: 15px;
        margin-bottom: 40px;
    }}
    h2, h3 {{ color: #38bdf8 !important; font-family: 'Courier New', monospace; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #111827 !important;
        border-right: 2px solid #00ffff;
        box-shadow: 5px 0 25px rgba(0, 255, 255, 0.1);
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{
        color: #38bdf8 !important;
        text-shadow: none;
        border: none;
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: #0f172a;
        color: #00ffff;
        border: 1px solid #00ffff;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #00ffff;
        color: #000;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
    }}
    
    /* Metric Cards */
    .metric-card {{
        background: rgba(10, 15, 26, 0.8);
        border: 1px solid #00ffff;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.15);
        margin-bottom: 30px;
        backdrop-filter: blur(5px);
    }}
    .metric-title {{
        font-size: 16px;
        color: #7dd3fc;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 15px;
        font-family: 'Courier New', monospace;
    }}
    .metric-value {{
        font-size: 34px;
        font-weight: bold;
        color: #00ffff;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
        font-family: 'Courier New', monospace;
    }}
    
    /* Alert Panels */
    .alert-panel {{
        padding: 30px;
        border-radius: 12px;
        margin-top: 25px;
        font-size: 20px;
        line-height: 1.7;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}
    .alert-healthy {{
        background: rgba(21, 128, 61, 0.15);
        border: 2px solid #22c55e;
        color: #4ade80;
        box-shadow: 0 0 25px rgba(34, 197, 94, 0.25);
    }}
    .alert-chronic {{
        background: rgba(180, 83, 9, 0.15);
        border: 2px solid #f59e0b;
        color: #fbbf24;
        box-shadow: 0 0 25px rgba(245, 158, 11, 0.25);
    }}
    .alert-critical {{
        background: rgba(153, 27, 27, 0.15);
        border: 2px solid #ef4444;
        color: #fca5a5;
        box-shadow: 0 0 30px rgba(239, 68, 68, 0.5);
        animation: pulse 1.5s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 15px rgba(239, 68, 68, 0.3); }}
        50% {{ box-shadow: 0 0 35px rgba(239, 68, 68, 0.8); border-color: #f87171; }}
        100% {{ box-shadow: 0 0 15px rgba(239, 68, 68, 0.3); }}
    }}
</style>
""", unsafe_allow_html=True)


# --- Database ---
PROFILES = {
    "Normal Blood (Reference)": {"f_res": 9.2, "depth": -40.0, "color": "#00FF00", "severity": "HEALTHY"},
    "Chronic Diabetes (High Glucose)": {"f_res": 9.4, "depth": -38.0, "color": "#FFA500", "severity": "CHRONIC"},
    "High Cholesterol": {"f_res": 9.6, "depth": -39.0, "color": "#FFD700", "severity": "CHRONIC"},
    "Breast Cancer (MCF-7)": {"f_res": 8.8, "depth": -35.0, "color": "#FF3333", "severity": "CRITICAL"},
    "Prostate Cancer (PC-3)": {"f_res": 8.9, "depth": -32.0, "color": "#FF00FF", "severity": "CRITICAL"},
    "Lung Cancer (A549)": {"f_res": 8.6, "depth": -30.0, "color": "#FF8C00", "severity": "CRITICAL"},
    "Blood Cancer (Leukemia)": {"f_res": 8.2, "depth": -28.0, "color": "#FF0000", "severity": "CRITICAL"}
}

# --- Drawing Helpers ---
def draw_rect_3d(ax, xc, yc, zc, w, d, h, color, edge_color, alpha=1.0):
    x0, x1 = xc - w/2, xc + w/2
    y0, y1 = yc - d/2, yc + d/2
    z0, z1 = zc, zc + h
    faces = [
        [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], 
        [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], 
        [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], 
        [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]], 
        [[x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1]], 
        [[x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1]]  
    ]
    poly3d = Poly3DCollection(faces, facecolors=color, linewidths=1.2, edgecolors=edge_color, alpha=alpha, shade=True)
    ax.add_collection3d(poly3d)

def draw_cylinder(ax, x_start, y_center, z_center, radius, length, color, orientation='x'):
    z = np.linspace(0, length, 15)
    theta = np.linspace(0, 2*np.pi, 20)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_c = radius * np.cos(theta_grid)
    y_c = radius * np.sin(theta_grid)
    if orientation == 'x':
        X = z_grid + x_start
        Y = x_c + y_center
        Z = y_c + z_center
    ax.plot_surface(X, Y, Z, color=color, alpha=1.0, shade=True)

def draw_hemisphere(ax, xc, yc, zc, radius, color):
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi / 2, 20) 
    X = xc + radius * np.outer(np.cos(u), np.sin(v))
    Y = yc + radius * np.outer(np.sin(u), np.sin(v))
    Z = zc + radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(X, Y, Z, color=color, alpha=0.9, shade=True, antialiased=True)

def draw_realistic_horn(ax, xc, yc, z_top, z_flare, z_bottom):
    w_guide = 1.2
    draw_rect_3d(ax, xc, yc, z_flare, w_guide, w_guide, z_top-z_flare, color='#b5a642', edge_color='#8B6508')
    w_top = w_guide / 2
    w_bot = 5.5 / 2
    t1, t2, t3, t4 = [xc-w_top, yc-w_top, z_flare], [xc+w_top, yc-w_top, z_flare], [xc+w_top, yc+w_top, z_flare], [xc-w_top, yc+w_top, z_flare]
    b1, b2, b3, b4 = [xc-w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc-w_bot, z_bottom], [xc+w_bot, yc+w_bot, z_bottom], [xc-w_bot, yc+w_bot, z_bottom]
    faces = [[t1, t2, b2, b1], [t2, t3, b3, b2], [t3, t4, b4, b3], [t4, t1, b1, b4]]
    poly3d = Poly3DCollection(faces, facecolors='#FFD700', edgecolors='#B8860B', linewidths=1.5, shade=True)
    ax.add_collection3d(poly3d)

def generate_noisy_s11(f, f_res, depth, q_factor=20):
    gamma = f_res / (2 * q_factor)
    dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
    noise = np.random.normal(0, 0.4, size=len(f)) + np.random.uniform(-0.2, 0.2, size=len(f))
    ripple = 0.5 * np.sin(2 * np.pi * 5 * f)
    return dip + noise + ripple

@st.cache_data(show_spinner=False)
def get_3d_fig(show_droplet=False):
    fig = plt.figure(figsize=(10, 8), facecolor='#0a0f1a')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#0a0f1a')
    ax.axis('off')
    
    ax.set_xlim(-11.5, 3.5)
    ax.set_ylim(-4.5, 4.5)
    ax.set_zlim(0, 14.5)
    ax.view_init(elev=15, azim=40)
    
    draw_rect_3d(ax, -9, 0, 0, 5, 8, 12, color='#888888', edge_color='#555555')
    draw_rect_3d(ax, -6.45, -1, 5, 0.15, 5, 5, color='#00FFFF', edge_color='#008B8B')
    draw_cylinder(ax, -6.5, 2.0, 8.0, 0.4, 0.8, color='silver', orientation='x')
    
    draw_realistic_horn(ax, 0, 0, 14, 11, 5)
    
    t = np.linspace(0, 1, 60)
    cx = -5.7 + 5.1*t
    cy = 2.0 * (1 - t)
    cz = 8.0 * (1 - t) + 12.5 * t - 4.5*np.sin(np.pi*t) 
    ax.plot(cx, cy, cz, color='#1A1A1A', linewidth=6, solid_capstyle='round')
    
    draw_rect_3d(ax, 0, 0, 0, 7, 7, 0.8, color='#2e8b57', edge_color='#006400')
    draw_rect_3d(ax, 0, 0, 0.8, 3, 3, 0.1, color='#FF8C00', edge_color='#CD6600')
    
    if show_droplet:
        draw_hemisphere(ax, 0, 0, 0.9, 0.6, color='#FF0000')
        
    return fig

def get_2d_fig(f_array, ref_y, target_y=None, prof=None, selected_sample=None):
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0a0f1a')
    ax.set_facecolor('#0a0f1a')
    ax.set_xlabel("Frequency (GHz)", color='#00ffff', fontsize=16)
    ax.set_ylabel("S₁₁ Return Loss (dB)", color='#00ffff', fontsize=16)
    ax.set_title("VNA TELEMETRY FEED", color='#00FFFF', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlim(8, 11)
    ax.set_ylim(-45, 0)
    ax.grid(True, linestyle='--', color='#1f2937')
    ax.tick_params(colors='#e0f2fe', labelsize=12)
    for spine in ax.spines.values():
        spine.set_color('#0ea5e9')
        
    ax.plot(f_array, ref_y, color='#64748b', linestyle='--', linewidth=3, label="Reference Baseline")
    
    if target_y is not None and prof is not None:
        ax.plot(f_array, target_y, color=prof["color"], linewidth=4, label=f"Active Scan ({selected_sample})")
        
    ax.legend(facecolor='#0a0f1a', edgecolor='#0ea5e9', loc='upper right', labelcolor='white', fontsize=14)
    return fig

# --- App Layout ---
st.markdown("<h1>🏥 ISIA BIOMEDICAL MICROWAVE SENSOR | RF TELEMETRY 📡</h1>", unsafe_allow_html=True)

st.sidebar.markdown("<h2>⚙️ HARDWARE CONTROL PANEL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
patient_name = st.sidebar.text_input("PATIENT ID", "PT-1039-X")
selected_sample = st.sidebar.selectbox("SELECT BIOMATERIAL SAMPLE", list(PROFILES.keys()))
st.sidebar.markdown("---")
scan_btn = st.sidebar.button("INITIATE RF SCAN", type="primary", use_container_width=True)

f_array = np.linspace(8, 11, 500)
ref_prof = PROFILES["Normal Blood (Reference)"]
ref_y = generate_noisy_s11(f_array, ref_prof["f_res"], ref_prof["depth"])

col1, col2 = st.columns([1, 1])

if not scan_btn:
    with col1:
        st.markdown("<h3 style='text-align: center;'>► 3D DIGITAL TWIN</h3>", unsafe_allow_html=True)
        st.pyplot(get_3d_fig(show_droplet=False))
        
    with col2:
        st.markdown("<h3 style='text-align: center;'>► S11 LIVE FEED</h3>", unsafe_allow_html=True)
        st.pyplot(get_2d_fig(f_array, ref_y))
        
    st.info("System Initialized. Awaiting sample load and RF telemetry scan...")

if scan_btn:
    with col1:
        st.markdown("<h3 style='text-align: center;'>► 3D DIGITAL TWIN</h3>", unsafe_allow_html=True)
        fig3d_container = st.empty()
        fig3d_container.pyplot(get_3d_fig(show_droplet=False))
        time.sleep(0.5) 
        fig3d_container.pyplot(get_3d_fig(show_droplet=True))
        
    with col2:
        st.markdown("<h3 style='text-align: center;'>► S11 LIVE FEED</h3>", unsafe_allow_html=True)
        prof = PROFILES[selected_sample]
        q_fac = 12 if "Leukemia" in selected_sample else 20
        target_y = generate_noisy_s11(f_array, prof["f_res"], prof["depth"], q_factor=q_fac)
        
        st.pyplot(get_2d_fig(f_array, ref_y, target_y, prof, selected_sample))
        
    delta_f = (prof['f_res'] - 9.2) * 1000
    severity = prof['severity']
    
    if severity == "HEALTHY":
        conf = random.uniform(97.5, 99.2)
    else:
        conf = random.uniform(92.1, 98.8)
        
    st.markdown("<br><hr style='border-color: #0ea5e9;'><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #00ffff; text-shadow: 0 0 10px #00ffff;'>✚ AI DOCTOR'S CLINICAL INTERPRETATION</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #7dd3fc;'><strong>Patient ID:</strong> {patient_name} | <strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p><br>", unsafe_allow_html=True)
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    col_res1.markdown(f"<div class='metric-card'><div class='metric-title'>〰️ Resonance Frequency</div><div class='metric-value'>{prof['f_res']:.3f} GHz</div></div>", unsafe_allow_html=True)
    col_res2.markdown(f"<div class='metric-card'><div class='metric-title'>〰️ Frequency Shift (Δf)</div><div class='metric-value'>{delta_f:+.0f} MHz</div></div>", unsafe_allow_html=True)
    col_res3.markdown(f"<div class='metric-card'><div class='metric-title'>〰️ Minimum Return Loss</div><div class='metric-value'>{prof['depth']:.1f} dB</div></div>", unsafe_allow_html=True)
    col_res4.markdown(f"<div class='metric-card'><div class='metric-title'>🧬 AI Confidence</div><div class='metric-value'>{conf:.2f}%</div></div>", unsafe_allow_html=True)
    
    if severity == "HEALTHY":
        st.markdown(f"<div class='alert-panel alert-healthy'>✔️ <strong>DIAGNOSIS: {selected_sample} (HEALTHY)</strong><br><br>The microwave dielectric profile of the blood sample aligns perfectly with healthy baseline metrics. No cellular abnormalities or metabolic imbalances detected. Continue standard healthy lifestyle routines.</div>", unsafe_allow_html=True)
    elif severity == "CHRONIC":
        st.markdown(f"<div class='alert-panel alert-chronic'>⚠️ <strong>DIAGNOSIS: {selected_sample} (CHRONIC - MANAGEABLE)</strong><br><br>The S11 parameter shift indicates a chronic metabolic condition (e.g., elevated glucose or lipids). While this is a manageable chronic disease, it requires lifestyle modifications, dietary control, and routine follow-ups. This is highly treatable and not immediately life-threatening if managed properly.</div>", unsafe_allow_html=True)
    else: # CRITICAL
        st.markdown(f"<div class='alert-panel alert-critical'>🚨 <strong>URGENT DIAGNOSIS: {selected_sample} (CRITICAL - ONCOLOGY)</strong><br><br>The significant frequency shift (Δf) indicates severe cellular abnormalities consistent with malignant tissue presence. Immediate referral to an oncology specialist for comprehensive biopsy and imaging is strictly required.</div>", unsafe_allow_html=True)
