import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import random
import time
import base64
import requests
import json
import pandas as pd

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
    .stApp {{
        background-color: #0a0f1a;
        background-image: url("data:image/svg+xml;base64,{b64_bg}");
        background-repeat: repeat;
        background-size: 300px;
        color: #e0f2fe;
    }}
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
        font-size: 16px; color: #7dd3fc; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; font-family: 'Courier New', monospace;
    }}
    .metric-value {{
        font-size: 34px; font-weight: bold; color: #00ffff; text-shadow: 0 0 15px rgba(0, 255, 255, 0.6); font-family: 'Courier New', monospace;
    }}
    
    .alert-panel {{
        padding: 30px; border-radius: 12px; margin-top: 25px; font-size: 20px; line-height: 1.7; font-family: 'Courier New', monospace; font-weight: bold; letter-spacing: 0.5px;
    }}
    .alert-healthy {{ background: rgba(21, 128, 61, 0.15); border: 2px solid #22c55e; color: #4ade80; box-shadow: 0 0 25px rgba(34, 197, 94, 0.25); }}
    .alert-chronic {{ background: rgba(180, 83, 9, 0.15); border: 2px solid #f59e0b; color: #fbbf24; box-shadow: 0 0 25px rgba(245, 158, 11, 0.25); }}
    .alert-critical {{ background: rgba(153, 27, 27, 0.15); border: 2px solid #ef4444; color: #fca5a5; box-shadow: 0 0 30px rgba(239, 68, 68, 0.5); animation: pulse 1.5s infinite; }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 15px rgba(239, 68, 68, 0.3); }}
        50% {{ box-shadow: 0 0 35px rgba(239, 68, 68, 0.8); border-color: #f87171; }}
        100% {{ box-shadow: 0 0 15px rgba(239, 68, 68, 0.3); }}
    }}
</style>
""", unsafe_allow_html=True)


# --- Database ---
PROFILES = {
    "Healthy (Reference)": {"f_res": 9.2, "depth": -40.0, "color": "#00FF00", "severity": "HEALTHY"},
    "Leukemia": {"f_res": 8.0, "depth": -28.0, "color": "#FF0000", "severity": "CRITICAL"},
    "Diabetes (Hyperglycemia)": {"f_res": 8.6, "depth": -38.0, "color": "#FFA500", "severity": "CHRONIC"},
    "Hypercholesterolemia": {"f_res": 9.6, "depth": -39.0, "color": "#FFD700", "severity": "CHRONIC"},
    "Malaria": {"f_res": 8.4, "depth": -33.0, "color": "#FF3333", "severity": "CRITICAL"},
    "Anemia": {"f_res": 9.7, "depth": -37.0, "color": "#00FFFF", "severity": "CHRONIC"},
    "Dehydration": {"f_res": 7.7, "depth": -25.0, "color": "#A52A2A", "severity": "CRITICAL"},
    "Sepsis (Blood Infection)": {"f_res": 8.5, "depth": -30.0, "color": "#800080", "severity": "CRITICAL"},
    "Breast Cancer (Metastatic)": {"f_res": 8.3, "depth": -31.0, "color": "#FF69B4", "severity": "CRITICAL"},
    "Lung Cancer (Advanced)": {"f_res": 8.1, "depth": -29.0, "color": "#8B4513", "severity": "CRITICAL"},
    "Colorectal Cancer": {"f_res": 8.4, "depth": -32.0, "color": "#B8860B", "severity": "CRITICAL"},
    "Prostate Cancer": {"f_res": 8.6, "depth": -34.0, "color": "#4682B4", "severity": "CRITICAL"},
    "Brain Tumor (Biomarkers)": {"f_res": 7.9, "depth": -27.0, "color": "#483D8B", "severity": "CRITICAL"}
}

# --- Plotly 3D Drawing Helpers ---
def get_box_mesh(xc, yc, zc, w, d, h, color, lighting=None):
    x0, x1 = xc - w/2, xc + w/2
    y0, y1 = yc - d/2, yc + d/2
    z0, z1 = zc, zc + h
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    i = [0, 0, 4, 4, 0, 0, 2, 2, 1, 1, 0, 0]
    j = [1, 2, 5, 6, 1, 5, 3, 7, 2, 6, 3, 7]
    k = [2, 3, 6, 7, 5, 4, 7, 6, 6, 5, 7, 4]
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        flatshading=True,
        lighting=lighting if lighting else dict(ambient=0.4, diffuse=0.8, specular=0.2, roughness=0.5)
    )

def get_cylinder_mesh(x_start, y_center, z_center, radius, length, color, lighting=None):
    n = 20
    theta = np.linspace(0, 2*np.pi, n)
    y_circ = radius * np.cos(theta)
    z_circ = radius * np.sin(theta)
    
    x = [x_start]*n + [x_start + length]*n
    y = list(y_center + y_circ) + list(y_center + y_circ)
    z = list(z_center + z_circ) + list(z_center + z_circ)
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        alphahull=0,
        color=color,
        flatshading=False,
        lighting=lighting
    )

def get_horn_mesh(xc, yc, z_top, z_flare, z_bot, color, lighting=None):
    w_guide = 1.2
    guide_mesh = get_box_mesh(xc, yc, z_flare, w_guide, w_guide, z_top-z_flare, color, lighting)
    
    w_top = w_guide / 2
    w_b = 5.5 / 2
    x = [xc-w_top, xc+w_top, xc+w_top, xc-w_top,  
         xc-w_b, xc+w_b, xc+w_b, xc-w_b]          
    y = [yc-w_top, yc-w_top, yc+w_top, yc+w_top,  
         yc-w_b, yc-w_b, yc+w_b, yc+w_b]
    z = [z_flare, z_flare, z_flare, z_flare,
         z_bot, z_bot, z_bot, z_bot]
         
    i = [0, 0, 2, 2, 1, 1, 0, 0]
    j = [1, 5, 3, 7, 2, 6, 3, 7]
    k = [5, 4, 7, 6, 6, 5, 7, 4]
    
    flare_mesh = go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        flatshading=True,
        lighting=lighting
    )
    return [guide_mesh, flare_mesh]

@st.cache_data(show_spinner=False)
def get_3d_plotly_fig(show_droplet=False):
    traces = []
    
    # 1. VNA Machine (Main Body & Screen)
    vna_body = get_box_mesh(-9, 0, 0, 5, 8, 12, '#2b2b2b', lighting=dict(ambient=0.5, diffuse=0.7, specular=0.3, roughness=0.4))
    traces.append(vna_body)
    
    vna_screen = get_box_mesh(-6.45, -1, 5, 0.15, 5, 5, '#00FFFF', lighting=dict(ambient=0.9, diffuse=0.8, specular=0.1, roughness=0.9))
    traces.append(vna_screen)
    
    # VNA Port Cylinder
    port = get_cylinder_mesh(-6.5, 2.0, 8.0, 0.4, 0.8, 'silver', lighting=dict(ambient=0.6, diffuse=0.8, specular=0.8, roughness=0.2))
    traces.append(port)
    
    # 2. Pyramidal Horn Antenna
    horn_meshes = get_horn_mesh(0, 0, 14, 11, 5, '#b5a642', lighting=dict(ambient=0.3, diffuse=0.6, specular=2.0, roughness=0.2))
    traces.extend(horn_meshes)
    
    # 3. Coaxial Cable
    t = np.linspace(0, 1, 60)
    cx = -5.7 + 5.1*t
    cy = 2.0 * (1 - t)
    cz = 8.0 * (1 - t) + 12.5 * t - 4.5*np.sin(np.pi*t) 
    
    cable = go.Scatter3d(
        x=cx, y=cy, z=cz,
        mode='lines',
        line=dict(color='#111111', width=8),
        hoverinfo='skip'
    )
    traces.append(cable)
    
    # 4. Metamaterial Absorber Sensor 
    fr4 = get_box_mesh(0, 0, 0, 7, 7, 0.8, '#228B22', lighting=dict(ambient=0.5, diffuse=0.7, specular=0.1, roughness=0.8))
    traces.append(fr4)
    
    copper = get_box_mesh(0, 0, 0.8, 3, 3, 0.1, '#b87333', lighting=dict(ambient=0.4, diffuse=0.8, specular=1.5, roughness=0.2))
    traces.append(copper)
    
    # 5. Blood Droplet Marker
    if show_droplet:
        droplet = go.Scatter3d(
            x=[0], y=[0], z=[1.15],
            mode='markers',
            marker=dict(size=15, color='#8a0303', symbol='circle', opacity=0.9),
            hoverinfo='skip'
        )
        traces.append(droplet)
        
    fig = go.Figure(data=traces)
    
    camera = dict(
        up=dict(x=0, y=0, z=1),
        center=dict(x=-0.5, y=0, z=0),
        eye=dict(x=1.3, y=-1.5, z=0.8)
    )
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, range=[-11.5, 3.5]),
            yaxis=dict(visible=False, range=[-4.5, 4.5]),
            zaxis=dict(visible=False, range=[0, 14.5]),
            aspectmode='data'
        ),
        scene_camera=camera,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig


def generate_noisy_s11(f, f_res, depth, q_factor=20):
    gamma = f_res / (2 * q_factor)
    dip = depth * (gamma**2) / ((f - f_res)**2 + gamma**2)
    noise = np.random.normal(0, 0.4, size=len(f)) + np.random.uniform(-0.2, 0.2, size=len(f))
    ripple = 0.5 * np.sin(2 * np.pi * 5 * f)
    return dip + noise + ripple

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
st.markdown("<h1>BIOMEDICAL MICROWAVE SENSOR</h1>", unsafe_allow_html=True)

st.sidebar.markdown("<h2>⚙️ HARDWARE CONTROL PANEL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# --- QR Code for Live App ---
st.sidebar.markdown("<p style='text-align: center; color: #7dd3fc; font-family: Courier New, monospace; font-size: 13px; letter-spacing: 1px;'>📱 Scan to Try Live!</p>", unsafe_allow_html=True)
st.sidebar.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://meta-biosensor.streamlit.app/", width=150)
st.sidebar.markdown("---")

# --- Language Selector ---
report_language = st.sidebar.radio(
    "🌐 Report Language / زمانی ڕاپۆرت",
    options=["English", "Kurdish (Sorani)"],
    horizontal=True
)
st.sidebar.markdown("---")

patient_name = st.sidebar.text_input("PATIENT ID", "PT-1039-X")
selected_sample = st.sidebar.selectbox("SELECT BIOMATERIAL SAMPLE", list(PROFILES.keys()))
st.sidebar.markdown("---")
scan_btn = st.sidebar.button("INITIATE RF SCAN", type="primary", use_container_width=True)

if "scan_active" not in st.session_state:
    st.session_state.scan_active = False

if "patient_history" not in st.session_state:
    st.session_state.patient_history = []

if scan_btn:
    st.session_state.scan_active = True
    st.session_state.report_generated = False
    st.session_state.ai_report = ""
    
    prof_tmp = PROFILES[selected_sample]
    delta_f_tmp = (prof_tmp['f_res'] - 9.2) * 1000
    st.session_state.patient_history.append({
        "Patient ID": patient_name,
        "Condition": selected_sample,
        "RF Shift (MHz)": f"{delta_f_tmp:+.0f}",
        "Timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })

f_array = np.linspace(8, 11, 500)
ref_prof = PROFILES["Healthy (Reference)"]
ref_y = generate_noisy_s11(f_array, ref_prof["f_res"], ref_prof["depth"])

col1, col2 = st.columns([1, 1])

if not st.session_state.scan_active:
    with col1:
        st.markdown("<h3 style='text-align: center;'>► 3D DIGITAL TWIN</h3>", unsafe_allow_html=True)
        st.plotly_chart(get_3d_plotly_fig(show_droplet=False), use_container_width=True)
        
    with col2:
        st.markdown("<h3 style='text-align: center;'>► S11 LIVE FEED</h3>", unsafe_allow_html=True)
        st.pyplot(get_2d_fig(f_array, ref_y))
        
    st.info("System Initialized. Awaiting sample load and RF telemetry scan...")

else:
    with col1:
        st.markdown("<h3 style='text-align: center;'>► 3D DIGITAL TWIN</h3>", unsafe_allow_html=True)
        if scan_btn:
            fig3d_container = st.empty()
            fig3d_container.plotly_chart(get_3d_plotly_fig(show_droplet=False), use_container_width=True)
            time.sleep(0.5) 
            fig3d_container.plotly_chart(get_3d_plotly_fig(show_droplet=True), use_container_width=True)
        else:
            st.plotly_chart(get_3d_plotly_fig(show_droplet=True), use_container_width=True)
        
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
    st.markdown("<h2 style='text-align: center; color: #00ffff; text-shadow: 0 0 10px #00ffff;'>🧠 AI Pathologist & Clinical Report</h2>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='alert-panel alert-critical'>🚨 <strong>URGENT DIAGNOSIS: {selected_sample} (CRITICAL - ABNORMALITY)</strong><br><br>The significant frequency shift (Δf) indicates severe cellular abnormalities. Immediate referral to a specialist for comprehensive biopsy and imaging is strictly required.</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    if "report_generated" not in st.session_state:
        st.session_state.report_generated = False
        st.session_state.ai_report = ""

    report_btn = st.button("✨ Generate Comprehensive AI Report", type="primary", use_container_width=True)
    
    if report_btn:
        if "GROQ_API_KEY" not in st.secrets:
            st.error("🚨 GROQ_API_KEY not found in Streamlit Secrets. Please add it to your `.streamlit/secrets.toml` or Streamlit Cloud settings to generate reports.")
            st.stop()
            
        st.session_state.report_generated = True
        with st.spinner("Loading/Analyzing RF Data..."):
            api_key = st.secrets["GROQ_API_KEY"]
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            system_prompt = """You are a highly advanced Senior Clinical Pathologist working in a state-of-the-art hospital system.
Your goal is to generate a strictly professional, hospital-grade Electronic Health Record (EHR) report based on the provided simulated disease.

STRICT RULE: The "Doctor's Clinical Notes" and "Diagnosis" sections MUST NOT mention RF shifts, VNA, microwaves, or antennas. It must read entirely like a real medical doctor explaining the biological and physiological nature of the disease, and why it happens in the body.

You MUST structure your response with beautiful Markdown, bold text, and emojis, adhering strictly to the following format:

### 🩸 Clinical Lab Results
(Output a beautiful Markdown table. Based on the selected disease, hallucinate/estimate realistic medical parameters. e.g., if Leukemia, show WBC counts; if Diabetes, show Blood Glucose levels. Columns: Test Name | Result | Normal Range | Flag (High/Low/Normal))

### 🩺 Doctor's Clinical Notes
(A professional paragraph explaining the biological state of the patient based on the disease. Focus purely on medical biology, cellular mechanics, or metabolics. Do NOT mention engineering terms.)

### 💊 Rx Prescription & Action Plan
(A beautiful Markdown table or list of specific medications, e.g., Chemotherapy drugs for cancer, Metformin for Diabetes, dosages, and frequency of use, plus immediate clinical actions.)"""

            # Inject Kurdish language instruction if selected
            if report_language == "Kurdish (Sorani)":
                system_prompt += """\n\nYou are a professional Medical AI. You must respond in pure, natural Sorani Kurdish (Arabic script). DO NOT use English letters inside Kurdish sentences. Follow this EXACT markdown structure, keeping scientific test names in English:

### 🩸 ئەنجامی پشکنینە کلینیکییەکان
| ناوی پشکنین | ئەنجام | ڕێژەی ئاسایی | دۆخ |
|---|---|---|---|
(Insert tests here. e.g., | WBC | ... )

### 🩺 تێبینییە کلینیکییەکانی پزیشک
(Write 2-3 sentences in pure Sorani Kurdish explaining the condition. No English words here).

### 💊 ڕەچەتەی دەرمان و پلانی چارەسەر
(List 2-3 actionable medical recommendations in pure Sorani Kurdish using bullet points)."""
            
            user_prompt = f"Patient Name: {patient_name}\nSelected Condition: {selected_sample}\n\nPlease generate the medical report as instructed."
            
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            try:
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.ai_report = result["choices"][0]["message"]["content"]
                else:
                    st.session_state.ai_report = f"Error: API returned status code {response.status_code}\n{response.text}"
            except Exception as e:
                st.session_state.ai_report = f"Error calling API: {str(e)}"

    if st.session_state.report_generated and st.session_state.ai_report:
        st.markdown(f"""
        <div style='background: rgba(10, 15, 26, 0.9); border: 2px solid #ff00ff; border-radius: 12px; padding: 20px 30px; box-shadow: 0 0 25px rgba(255, 0, 255, 0.3); margin-top: 30px; font-family: "Courier New", Courier, monospace;'>
            <h3 style='color: #ff00ff; margin: 0; display: flex; align-items: center;'>
                <span style='margin-right: 10px; font-size: 24px;'>🔬</span> OFFICIAL AI CLINICAL REPORT
            </h3>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        # Inject RTL CSS only when Kurdish (Sorani) is selected
        # Scoped to stMainBlockContainer to guarantee sidebar is never affected
        if report_language == "Kurdish (Sorani)":
            st.markdown("""
                <style>
                @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

                /* Target ONLY markdown inside the main app body, leaving sidebar alone */
                [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] {
                    direction: rtl !important;
                    text-align: right !important;
                    font-family: 'Cairo', sans-serif !important;
                    font-size: 18px !important;
                    line-height: 2.0 !important;
                }
                [data-testid="stMainBlockContainer"] table {
                    direction: rtl !important;
                    text-align: right !important;
                    width: 100%;
                }
                [data-testid="stMainBlockContainer"] th,
                [data-testid="stMainBlockContainer"] td {
                    text-align: right !important;
                    padding: 12px !important;
                }
                [data-testid="stMainBlockContainer"] h1,
                [data-testid="stMainBlockContainer"] h2,
                [data-testid="stMainBlockContainer"] h3 {
                    direction: rtl !important;
                    text-align: right !important;
                    font-family: 'Cairo', sans-serif !important;
                }
                </style>
                """, unsafe_allow_html=True)

        st.markdown(st.session_state.ai_report)
        
    st.markdown("<br><hr style='border-color: #0ea5e9;'><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #00ffff; text-shadow: 0 0 10px #00ffff;'>🗄️ Hospital Patient Database</h2>", unsafe_allow_html=True)
    
    if len(st.session_state.patient_history) > 0:
        df = pd.DataFrame(st.session_state.patient_history)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No patient records found in the current session. Run an RF scan to populate the database.")

