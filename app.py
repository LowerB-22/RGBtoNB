import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="RGBtoNB", page_icon="✦", layout="wide")

from src.rgbtonb.physics import (
    CHANNELS,
    ideal_sensor_color,
    sensor_channel_signals,
    sensor_response_curve,
    super_gaussian_profile,
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink:#e8f0eb; --muted:#92a59c; --line:#263a36; --cyan:#56c6c8; --coral:#ef665b; --gold:#f3bd52; }
    .stApp { background: radial-gradient(circle at 75% 2%, #183b3b 0, #0b1517 40%, #081012 100%); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; }
    h1,h2,h3,p,div { font-family:'Space Grotesk',sans-serif; }
    .mono, [data-testid="stMetricValue"] { font-family:'DM Mono',monospace !important; }
    .kicker { color:var(--cyan); font:500 0.75rem 'DM Mono',monospace; letter-spacing:.16em; text-transform:uppercase; }
    .hero { border-bottom:1px solid var(--line); padding:1.4rem 0 1.5rem; margin-bottom:1.3rem; }
    .hero h1 { font-size:clamp(2.4rem,5vw,4.6rem); line-height:.95; letter-spacing:-.05em; margin:.25rem 0 .7rem; }
    .hero p { color:var(--muted); max-width:680px; font-size:1.05rem; }
    .panel { border:1px solid var(--line); background:rgba(12,28,29,.72); padding:1rem 1.1rem; border-radius:8px; height:100%; }
    .panel-title { color:var(--muted); font:500 .72rem 'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.65rem; }
    .channel { border-left:3px solid; padding:.45rem .75rem; margin:.45rem 0; background:rgba(255,255,255,.025); }
    .channel strong { font:500 1rem 'DM Mono',monospace; }
    .channel small { color:var(--muted); float:right; }
    section[data-testid="stSidebar"] { background:#0c191b; border-right:1px solid var(--line); }
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#b7c8c2 !important; }
    section[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stMarkdownContainer"] p { color:#dce9e4 !important; }
    section[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stSliderValue"] { color:#f4faf7 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div class="kicker">IMX571 / NARROWBAND LABORATORY</div>'
    '<h1>RGB<span style="color:#56c6c8">to</span>NB</h1>'
    '<p>Interaktive Darstellung von vier astronomischen Emissionslinien mit idealisiertem Super-Gauß-Profil.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="kicker">SPECTRUM SETUP</div>', unsafe_allow_html=True)
    bandwidth = st.slider("Filterbandbreite (nm)", 1.0, 10.0, 6.0, 0.5)
    use_sensor_response = st.toggle("Sensor-Empfindlichkeit anzeigen", value=False)
    st.divider()
    intensities = {
        name: st.slider(f"{name} Intensität", 0, 100, default)
        for name, default in {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}.items()
    }

mixed_color = ideal_sensor_color(intensities, use_sensor_response, bandwidth)
sensor_rgb = sensor_channel_signals(intensities, use_sensor_response, bandwidth)
sensor_total = sensor_rgb.sum()
sensor_ratios = sensor_rgb / sensor_total if sensor_total > 0 else np.zeros(3)
ratio_text = " · ".join(
    f"{channel}/I = {ratio:.3f}"
    for channel, ratio in zip(("R", "G", "B"), sensor_ratios)
)
color_title = "IMX571 SENSOR / RESULTING COLOR" if use_sensor_response else "IDEAL SENSOR / RESULTING COLOR"
color_description = (
    "Sensorantwort aus interpolierten IMX571-Kurven"
    if use_sensor_response
    else "100 % Empfindlichkeit über alle Wellenlängen"
)

wavelengths = np.linspace(430, 710, 1400)
figure = go.Figure()
for name, channel in CHANNELS.items():
    profile = super_gaussian_profile(wavelengths, channel["wavelength_nm"], bandwidth) * intensities[name]
    figure.add_trace(go.Scatter(
        x=wavelengths,
        y=profile,
        name=name,
        line={"color": channel["color"], "width": 2.5},
    ))

if use_sensor_response:
    for sensor_channel, color in (("RED", "#ff4b4b"), ("GREEN", "#56d68a"), ("BLUE", "#6194ff")):
        figure.add_trace(go.Scatter(
            x=wavelengths,
            y=sensor_response_curve(sensor_channel, wavelengths) * 100,
            name=f"Sensor {sensor_channel}",
            line={"color": color, "width": 1.5, "dash": "dot"},
            opacity=0.8,
        ))

figure.update_layout(
    height=540,
    margin={"l": 0, "r": 10, "t": 10, "b": 0},
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend={
        "orientation": "h",
        "y": 1.08,
        "font": {"color": "#dce9e4", "size": 14},
    },
    xaxis={"title": "Wellenlänge (nm)", "gridcolor": "#1b302e"},
    yaxis={"title": "relative Intensität / QE (%)", "gridcolor": "#1b302e", "range": [0, 105]},
)

st.markdown('<div class="panel"><div class="panel-title">EMISSION LINES / SUPER-GAUSSIAN PROFILE</div>', unsafe_allow_html=True)
st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
st.markdown(
    f'<p class="mono" style="color:#b7c8c2;font-size:.8rem">Gemeinsame Bandbreite: {bandwidth:.1f} nm · Profilordnung: 4</p></div>',
    unsafe_allow_html=True,
)

st.markdown(f'<div class="panel"><div class="panel-title">{color_title}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="height:110px;background:{mixed_color};border:1px solid #ffffff55;border-radius:6px"></div>'
    f'<p class="mono" style="color:#b7c8c2;font-size:.8rem">{color_description} · {mixed_color}<br>{ratio_text} · I = R + G + B</p></div>',
    unsafe_allow_html=True,
)
