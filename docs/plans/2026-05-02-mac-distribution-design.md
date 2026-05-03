# Design: Mac-Distribution von Notenrechner v1.0

## Ziel

Die fertige App einer anderen Person auf deren MacBook zur Verfügung stellen — als leere, unausgefüllte Version, die dauerhaft Daten speichert und ohne tiefes technisches Wissen gestartet werden kann.

## Entscheidungen

- **Speicherung:** Server-seitig via Flask (wie bisher) — LocalStorage wurde verworfen, weil Daten dauerhaft ohne expliziten Export gespeichert bleiben müssen.
- **Start-Methode:** `start.command` Doppelklick-Skript — Macs haben Python 3 seit macOS 12.3 vorinstalliert, Flask wird beim ersten Start automatisch installiert.
- **Datenzustand:** Komplett leer (`{"classes": []}`) — keine bestehenden Klassen, Schüler oder Noten.

## Lieferpaket: `Notenrechner-v1.0/`

| Datei | Inhalt |
|---|---|
| `index.html` | v1.0, unverändert |
| `server.py` | unverändert |
| `data.json` | `{"classes": []}` (leer) |
| `start.command` | macOS-Startskript (ausführbar) |
| `ANLEITUNG.txt` | Kurze Anleitung auf Deutsch |

## start.command — Logik

1. Prüft ob `python3` verfügbar ist — wenn nicht: freundliche Fehlermeldung mit Hinweis auf python.org
2. Führt `pip3 install flask` aus (idempotent — schadet nicht bei Wiederholung)
3. Startet `python3 server.py` im Hintergrund
4. Öffnet `http://localhost:5000` im Standardbrowser mit `open`
5. Wartet auf Server-Start (kurze Pause), dann beendet sich das Terminal-Fenster

## Voraussetzungen

- macOS Monterey 12.3 oder neuer (Python 3 vorinstalliert)
- Internetverbindung beim ersten Start (für `pip install flask`, ~2MB)
- Danach vollständig offline nutzbar

## Was NICHT geändert wird

`index.html` und `server.py` bleiben 1:1 identisch mit v1.0 — keine Regressionen möglich.
