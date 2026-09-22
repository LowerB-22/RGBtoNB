from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="RGBtoNB", page_icon="✦", layout="wide")

from src.rgbtonb.physics import CHANNELS, SensorConfig, sensor_qe, simulate_channels


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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div class="kicker">IMX571 / NARROWBAND LABORATORY</div>'
    '<h1>RGB<span style="color:#56c6c8">to</span>NB</h1>'
    '<p>Eine physikalisch nachvollziehbare Vorschau darauf, wie H-alpha, O III und S II auf einem gekühlten Sony IMX571 zu einem RGB-Komposit werden.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="kicker">OBSERVING SETUP</div>', unsafe_allow_html=True)
    exposure = st.slider("Belichtungszeit / Kanal (s)", 30, 900, 300, 30)
    aperture = st.slider("Öffnung (mm)", 40, 400, 80, 5)
    airmass = st.slider("Airmass", 1.0, 3.0, 1.3, 0.1)
    temperature = st.slider("Sensortemperatur (°C)", -15, 20, 0)
    st.divider()
    st.caption("Nominalmodell • IMX571 mono response • 3.76 μm Pixel")

fluxes = {
    "H-alpha": st.sidebar.slider("H-alpha Flux", 20, 400, 180),
    "O III": st.sidebar.slider("O III Flux", 20, 400, 125),
    "S II": st.sidebar.slider("S II Flux", 20, 400, 90),
}
results = simulate_channels(exposure, aperture, airmass, fluxes, temperature)

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.markdown('<div class="panel"><div class="panel-title">01 / Filter passbands & sensor response</div>', unsafe_allow_html=True)
    wavelengths = np.linspace(380, 750, 600)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=wavelengths, y=sensor_qe(wavelengths) * 100, name="IMX571 QE", line={"color": "#e8f0eb", "width": 2}, fill="tozeroy", fillcolor="rgba(86,198,200,.08)"))
    for name, channel in CHANNELS.items():
        center, width = channel["wavelength_nm"], channel["bandwidth_nm"]
        profile = np.exp(-0.5 * ((wavelengths - center) / (width / 2.355)) ** 2) * 92
        fig.add_trace(go.Scatter(x=wavelengths, y=profile, name=name, line={"color": channel["color"], "width": 2}, opacity=.9))
    fig.update_layout(height=380, margin={"l": 0, "r": 10, "t": 10, "b": 0}, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend={"orientation":"h", "y":1.08}, xaxis={"title":"Wellenlänge (nm)", "gridcolor":"#1b302e"}, yaxis={"title":"relative QE / transmission (%)", "gridcolor":"#1b302e", "range":[0,105]})
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">02 / Detected signal</div>', unsafe_allow_html=True)
    for name, channel in CHANNELS.items():
        result = results[name]
        st.markdown(f'<div class="channel" style="border-color:{channel["color"]}"><strong>{name}</strong><small>{channel["wavelength_nm"]:.1f} nm</small><br><span class="mono">{result["electrons"]:,.0f} e−</span> · SNR {result["snr"]:.1f} · QE {result["qe"]:.0%}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="margin-top:1.2rem">RGB mapping / synthetic palette</div>', unsafe_allow_html=True)
    rgb = np.array([results["S II"]["electrons"], results["H-alpha"]["electrons"], results["O III"]["electrons"]])
    rgb /= max(rgb.max(), 1)
    rgb = np.clip(rgb ** 0.42, 0, 1)
    st.markdown(f'<div style="height:74px;border-radius:6px;background:rgb({rgb[0]*255:.0f},{rgb[1]*255:.0f},{rgb[2]*255:.0f});border:1px solid #ffffff33"></div><p class="mono" style="color:#92a59c;font-size:.8rem">S II → R &nbsp; Hα → G &nbsp; O III → B</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Signal budget")
table = pd.DataFrame([
    {"Kanal": name, "Photonenfluss": fluxes[name], "Signal (e−)": round(values["electrons"]), "Dark (e−)": round(values["dark_electrons"], 2), "Shot + Read Noise (e−)": round(values["noise"], 1), "SNR": round(values["snr"], 1)}
    for name, values in results.items()
])
st.dataframe(table, hide_index=True, use_container_width=True)
st.caption("Das Modell ist eine transparente Näherung: reale Filterkurven, Bayer-Matrix, Seeing und Objekt-Helligkeitsverteilung können abweichen.")
