# System Monitor

Ein Desktop-Systemmonitor mit grafischer Oberfläche auf Basis von Python, PySide6 und psutil. Die Oberfläche zeigt CPU- und RAM-Auslastung, CPU-Kerne, verfügbare Temperatur- und Taktinformationen, Laufzeit, Load, Swap, Speicherplatz und Netzwerkdurchsatz an.

## Voraussetzungen

- Python 3.10 oder neuer
- Linux, Windows oder macOS
- Für Temperaturwerte müssen Betriebssystem und Hardware entsprechende Sensorwerte bereitstellen.

## Installation und Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python system_monitor.py
```

## Hinweise

- Die Anzeige wird einmal pro Sekunde aktualisiert.
- Temperatur- und Load-Angaben können je nach Betriebssystem und Hardware nicht verfügbar sein.
- Der angezeigte Speicherplatz bezieht sich auf `/` und ist damit vor allem für Linux-Systeme gedacht.
