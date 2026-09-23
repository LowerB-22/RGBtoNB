import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="RGBtoNB", page_icon="✦", layout="wide")

from src.rgbtonb.physics import (
    CHANNELS,
    continuum_channel_signals,
    ideal_sensor_color,
    line_channel_signals,
    sensor_display_values,
    sensor_channel_signals,
    sensor_response_curve,
    super_gaussian_profile,
    wavelength_to_rgb_channels,
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
    bandwidth = st.slider("Linienbreite FWHM (nm)", 1.0, 10.0, 6.0, 0.5)
    use_sensor_response = st.toggle("Sensor-Empfindlichkeit anzeigen", value=False)
    normalize_to_max = st.toggle("Sensor-Signal auf Maximum normieren", value=False)
    show_spectral_rgb = st.toggle("Spektrale RGB-Referenzkurven anzeigen", value=False)
    bit_depth = st.selectbox("Anzeige-Bittiefe", (8, 10, 12, 16), index=3)
    white_continuum = st.slider("Weißes Kontinuum", 0, 100, 0)
    st.divider()
    intensities = {
        name: st.slider(f"{name} Intensität", 0, 100, default)
        for name, default in {"H-alpha": 80, "O III": 65, "S II": 55, "He II": 40}.items()
    }

mixed_color = ideal_sensor_color(
    intensities,
    use_sensor_response,
    bandwidth,
    normalize_to_max,
    bit_depth,
    white_continuum,
)
sensor_rgb = sensor_channel_signals(intensities, use_sensor_response, bandwidth, white_continuum)
display_values = (
    sensor_display_values(intensities, bandwidth, bit_depth, normalize_to_max, white_continuum)
    if use_sensor_response
    else sensor_rgb / 255 * ((1 << bit_depth) - 1)
)
sensor_total = sensor_rgb.sum()
sensor_ratios = sensor_rgb / sensor_total if sensor_total > 0 else np.zeros(3)
ratio_text = " · ".join(
    f"{channel}/I = {ratio:.3f}"
    for channel, ratio in zip(("R", "G", "B"), sensor_ratios)
)
display_rgb_text = "RGB({:.0f}, {:.0f}, {:.0f})".format(*display_values)
color_title = "IMX571 SENSOR / RESULTING COLOR" if use_sensor_response else "IDEAL SENSOR / RESULTING COLOR"
color_description = (
    "Sensorantwort aus interpolierten IMX571-Kurven"
    if use_sensor_response
    else "100 % Empfindlichkeit über alle Wellenlängen"
)

wavelengths = np.linspace(430, 710, 1400)
figure = make_subplots(specs=[[{"secondary_y": True}]])
if white_continuum > 0:
    continuum_profile = np.full_like(
        wavelengths,
        white_continuum / (wavelengths[-1] - wavelengths[0]),
        dtype=float,
    )
    figure.add_trace(go.Scatter(
        x=wavelengths,
        y=continuum_profile,
        name="Weißes Kontinuum",
        line={"color": "#f4f7f2", "width": 1.5},
        opacity=0.7,
    ), secondary_y=False)
for name, channel in CHANNELS.items():
    profile_shape = super_gaussian_profile(wavelengths, channel["wavelength_nm"], bandwidth)
    profile = profile_shape / np.trapezoid(profile_shape, wavelengths) * intensities[name]
    figure.add_trace(go.Scatter(
        x=wavelengths,
        y=profile,
        name=name,
        line={"color": channel["color"], "width": 2.5},
    ), secondary_y=False)

if use_sensor_response:
    for sensor_channel, color in (("RED", "#ff4b4b"), ("GREEN", "#56d68a"), ("BLUE", "#6194ff")):
        figure.add_trace(go.Scatter(
            x=wavelengths,
            y=sensor_response_curve(sensor_channel, wavelengths) * 100,
            name=f"Sensor {sensor_channel}",
            line={"color": color, "width": 1.5, "dash": "dot"},
            opacity=0.8,
        ), secondary_y=True)

if show_spectral_rgb:
    spectral_rgb = np.array([wavelength_to_rgb_channels(wavelength) for wavelength in wavelengths])
    for channel_index, channel_name in enumerate(("RGB Rot", "RGB Grün", "RGB Blau")):
        figure.add_trace(go.Scatter(
            x=wavelengths,
            y=spectral_rgb[:, channel_index] * 100,
            name=channel_name,
            line={
                "color": ("#ff6b6b", "#63e6a1", "#72a7ff")[channel_index],
                "width": 1.4,
                "dash": "dashdot",
            },
            opacity=0.75,
        ), secondary_y=True)

strip_wavelengths = np.linspace(430, 710, 1400)
spectral_rgb = np.array([
    wavelength_to_rgb_channels(wavelength)
    for wavelength in strip_wavelengths
])
line_signal = np.zeros(strip_wavelengths.size)
continuum_signal = np.zeros(strip_wavelengths.size)
if white_continuum > 0:
    continuum_signal += white_continuum / (strip_wavelengths[-1] - strip_wavelengths[0])
for name, channel in CHANNELS.items():
    profile_shape = super_gaussian_profile(
        strip_wavelengths,
        channel["wavelength_nm"],
        bandwidth,
    )
    line_profile = profile_shape / np.trapezoid(profile_shape, strip_wavelengths) * intensities[name]
    line_signal += line_profile
if use_sensor_response:
    sensor_rgb = np.column_stack([
        sensor_response_curve(sensor_channel, strip_wavelengths)
        for sensor_channel in ("RED", "GREEN", "BLUE")
    ])
    spectral_rgb *= sensor_rgb
    continuum_rgb = sensor_rgb
else:
    continuum_rgb = np.ones((strip_wavelengths.size, 3))
spectro_image = np.maximum(
    line_signal[:, None] * spectral_rgb
    + continuum_signal[:, None] * continuum_rgb,
    0,
)
profile_reference = super_gaussian_profile(
    np.linspace(-4 * bandwidth, 4 * bandwidth, 401),
    0.0,
    bandwidth,
)
reference_peak = 100 / np.trapezoid(profile_reference, np.linspace(-4 * bandwidth, 4 * bandwidth, 401))
continuum_reference = 100 / (strip_wavelengths[-1] - strip_wavelengths[0])
display_reference = max(reference_peak, continuum_reference)
spectro_image = np.rint(np.clip(spectro_image / display_reference * 255, 0, 255)).astype(np.uint8)
spectro_image = np.repeat(spectro_image[None, :, :], 36, axis=0)
strip_figure = go.Figure(go.Image(z=spectro_image))
strip_figure.update_layout(
    height=150,
    margin={"l": 0, "r": 0, "t": 0, "b": 28},
    showlegend=False,
    paper_bgcolor="#050708",
    plot_bgcolor="#050708",
    xaxis={
        "range": [0, len(strip_wavelengths)],
        "tickvals": [(value - 430) / (710 - 430) * len(strip_wavelengths) for value in (450, 500, 550, 600, 650, 700)],
        "ticktext": ["450", "500", "550", "600", "650", "700"],
        "tickfont": {"color": "#dce9e4", "size": 11},
        "showgrid": False,
        "showticklabels": True,
        "zeroline": False,
        "linecolor": "#46615e",
    },
    yaxis={"range": [0, 36], "showgrid": False, "showticklabels": False, "showline": False, "zeroline": False},
    shapes=[{"type": "rect", "xref": "paper", "yref": "paper", "x0": 0, "y0": 0, "x1": 1, "y1": 1, "line": {"color": "#46615e", "width": 1}, "fillcolor": "rgba(0,0,0,0)"}],
)

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
    yaxis={"title": "Spektrale Dichte (Intensität / nm)", "gridcolor": "#1b302e"},
    yaxis2={"title": "Relative Antwort (%)", "range": [0, 105], "overlaying": "y", "side": "right"},
)

st.markdown('<div class="panel"><div class="panel-title">EMISSION LINES / SUPER-GAUSSIAN PROFILE</div>', unsafe_allow_html=True)
st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
st.markdown(
    f'<p class="mono" style="color:#b7c8c2;font-size:.8rem">Linienbreite (FWHM): {bandwidth:.1f} nm · Profilordnung: 4</p></div>',
    unsafe_allow_html=True,
)

st.markdown(f'<div class="panel-title">{color_title}</div>', unsafe_allow_html=True)
st.plotly_chart(strip_figure, width="stretch", config={"displayModeBar": False})
st.markdown(
    f'<p class="mono" style="color:#b7c8c2;font-size:.8rem">{color_description}<br>{display_rgb_text} · {bit_depth}-Bit<br>{ratio_text} · I = R + G + B</p>',
    unsafe_allow_html=True,
)

scatter_figure = go.Figure()
line_only_rgb = sensor_channel_signals(intensities, use_sensor_response, bandwidth)
line_only_total = line_only_rgb.sum()
if line_only_total > 0:
    line_only_point = np.array([
        line_only_rgb[0] / line_only_total,
        line_only_rgb[1] / line_only_total,
    ])
    scatter_figure.add_trace(go.Scatter(
        x=[line_only_point[0]],
        y=[line_only_point[1]],
        mode="markers+text",
        text=["Linien gesamt"],
        textposition="top right",
        textfont={"color": "#f4f7f2", "size": 12},
        marker={"size": 16, "color": "#f4f7f2", "symbol": "circle-open", "line": {"color": "#f4f7f2", "width": 2}},
        name="Linien gesamt",
        hovertemplate="Linien gesamt<br>R/I = %{x:.3f}<br>G/I = %{y:.3f}<extra></extra>",
    ))

total_rgb = sensor_channel_signals(intensities, use_sensor_response, bandwidth, white_continuum)
total_signal = total_rgb.sum()
if total_signal > 0:
    total_point = np.array([total_rgb[0] / total_signal, total_rgb[1] / total_signal])
    if line_only_total > 0 and white_continuum > 0:
        scatter_figure.add_trace(go.Scatter(
            x=[line_only_point[0], total_point[0]],
            y=[line_only_point[1], total_point[1]],
            mode="lines",
            line={"color": "#f4f7f2", "width": 1.5, "dash": "dot"},
            name="Kontinuum-Verschiebung",
            hoverinfo="skip",
            showlegend=False,
        ))
    scatter_figure.add_trace(go.Scatter(
        x=[total_point[0]],
        y=[total_point[1]],
        mode="markers+text",
        text=["Linien + Kontinuum"],
        textposition="bottom right",
        textfont={"color": "#ffffff", "size": 12},
        marker={"size": 17, "color": "#ffffff", "symbol": "star", "line": {"color": "#56c6c8", "width": 2}},
        name="Linien + Kontinuum",
        hovertemplate="Linien + Kontinuum<br>R/I = %{x:.3f}<br>G/I = %{y:.3f}<extra></extra>",
    ))

for name, channel in CHANNELS.items():
    line_rgb = line_channel_signals(name, intensities[name], use_sensor_response, bandwidth)
    line_total = line_rgb.sum()
    if line_total <= 0:
        continue
    scatter_figure.add_trace(go.Scatter(
        x=[line_rgb[0] / line_total],
        y=[line_rgb[1] / line_total],
        mode="markers+text",
        text=[name],
        textposition="top center",
        textfont={"color": "#dce9e4", "size": 12},
        marker={"size": 13, "color": channel["color"], "line": {"color": "#e8f0eb", "width": 1}},
        name=name,
        hovertemplate=f"{name}<br>R/I = %{{x:.3f}}<br>G/I = %{{y:.3f}}<extra></extra>",
    ))
if white_continuum > 0:
    continuum_rgb = continuum_channel_signals(white_continuum, use_sensor_response)
    continuum_total = continuum_rgb.sum()
    if continuum_total > 0:
        scatter_figure.add_trace(go.Scatter(
            x=[continuum_rgb[0] / continuum_total],
            y=[continuum_rgb[1] / continuum_total],
            mode="markers+text",
            text=["Weißes Kontinuum"],
            textposition="bottom center",
            textfont={"color": "#f4f7f2", "size": 12},
            marker={"size": 13, "color": "#f4f7f2", "symbol": "diamond", "line": {"color": "#e8f0eb", "width": 1}},
            name="Weißes Kontinuum",
            hovertemplate="Weißes Kontinuum<br>R/I = %{x:.3f}<br>G/I = %{y:.3f}<extra></extra>",
        ))
scatter_figure.update_layout(
    height=360,
    margin={"l": 55, "r": 20, "t": 20, "b": 45},
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    xaxis={"title": "R / I", "range": [0, 1], "gridcolor": "#1b302e"},
    yaxis={"title": "G / I", "range": [0, 1], "gridcolor": "#1b302e", "scaleanchor": "x", "scaleratio": 1},
)
st.markdown('<div class="panel-title">LINE COLOR CONTRIBUTIONS</div>', unsafe_allow_html=True)
st.plotly_chart(scatter_figure, width="stretch", config={"displayModeBar": False})

st.markdown('<div class="panel-title">TOTAL COLOR MIXTURE</div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="height:110px;background:{mixed_color};border:1px solid #ffffff55;border-radius:6px"></div>'
    f'<p class="mono" style="color:#b7c8c2;font-size:.8rem">Linien + Kontinuum · {display_rgb_text} · {bit_depth}-Bit</p>',
    unsafe_allow_html=True,
)
