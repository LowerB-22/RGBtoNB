# RGBtoNB

Eine Streamlit-App zur interaktiven Visualisierung astronomischer Spektrallinien.

## Start

```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run app.py
```

Danach ist die App unter `http://localhost:8513` erreichbar, sofern sie mit dem aktuellen Projekt-Setup gestartet wird.

## Modell

Die App zeigt H-alpha (656.3 nm), O III (500.7 nm), S II (672.4 nm) und He II (468.6 nm) als Super-Gauss-Profile. Die Intensitaet jeder Linie sowie die gemeinsame Filterbandbreite zwischen 1 nm und 10 nm sind per Slider einstellbar.

Die Intensitaetsregler verwenden eine gemeinsame integrierte Skala: Das Linienprofil wird auf Flaeche 1 normiert, und das weisse Kontinuum wird ueber den Bereich 430-710 nm integriert. Ein Linienwert und ein Kontinuumswert mit gleicher Hoehe entsprechen damit derselben Gesamtintensitaet vor der Sensorantwort.

Optional koennen die geglaetteten RED-, GREEN- und BLUE-Empfindlichkeitskurven des Sony IMX571 aktiviert werden. Ohne Toggle gilt ein idealer Sensor. Mit aktivierter Sensorantwort werden Linien- und Kontinuumssignale getrennt mit den interpolierten Kurven gefaltet und anschliessend pro RGB-Kanal addiert.

Die Darstellung umfasst ein Linienprofil, ein spalt-spektrografisches RGB-Spektralbild, einen R/I-gegen-G/I-Scatterplot fuer die einzelnen Linien sowie die Gesamtfarbmischung. Eine logarithmische oder nichtlineare Darstellung kann schwache Kontinuumsanteile sichtbar machen, ohne die zugrunde liegenden integrierten Signale zu veraendern.

Die Anzeige-Codes koennen mit 8, 10, 12 oder 16 Bit ausgegeben werden. Die Maximalnormierung ist optional und betrifft nur die Anzeige, nicht die Rohsignale.

## Tests

```bash
uv run pytest
```
