# RGBtoNB

Eine Streamlit-App zur interaktiven Visualisierung astronomischer Spektrallinien.

## Start

```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run app.py
```

Danach ist die App unter `http://localhost:8501` erreichbar.

## Modell

Die App zeigt H-alpha (656.3 nm), O III (500.7 nm), S II (672.4 nm) und He II (468.6 nm) als Super-Gauss-Profile. Die Intensitaet jeder Linie sowie die gemeinsame Filterbandbreite zwischen 1 nm und 10 nm sind per Slider einstellbar. Optional koennen die geglaetteten RED-, GREEN- und BLUE-Empfindlichkeitskurven des Sony IMX571 aktiviert werden. Ohne Toggle gilt ein idealer Sensor mit 100 % Empfindlichkeit ueber alle Wellenlaengen.

## Tests

```bash
uv run pytest
```
