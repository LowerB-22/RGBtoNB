# RGBtoNB

Eine Streamlit-App zur physik-basierten Visualisierung von astronomischen Narrowband-Aufnahmen auf einem Sony IMX571 Sensor.

## Start

```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run app.py
```

Danach ist die App unter `http://localhost:8501` erreichbar.

## Modell

Die Simulation kombiniert eine geglaettete QE-Naeherung fuer den IMX571, Bandpass-Profile fuer H-alpha (656.3 nm), O III (500.7 nm) und S II (672.4 nm), atmosphaerische Transmission, Sammelflaeche, Belichtungszeit sowie Shot-, Dark- und Read-Noise. Die Werte dienen der anschaulichen Planung und sind kein Ersatz fuer eine kalibrierte Instrumentenantwort.

## Tests

```bash
uv run pytest
```
