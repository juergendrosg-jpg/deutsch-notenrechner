# Design: Export/Import-Funktion für Notenrechner

## Ziel

Die Nutzerin kann ihre Daten als JSON-Datei exportieren (Backup) und importieren (Wiederherstellen oder Update einspielen). Kein Datenverlust bei App-Updates oder versehentlichem Löschen.

## Entscheidungen

- **Methode:** JSON-Download/Upload über Browser-Standard-APIs — kein Server-Umbau nötig
- **Platzierung:** Sidebar-Footer, unter den Klassen-Links — dezent, nicht im Weg
- **Format:** Voller `data.json`-Inhalt (komplettes `{"classes": [...]}`)

## UI

Zwei kleine Buttons nebeneinander am unteren Ende der Sidebar:

```
[ Exportieren ]  [ Importieren ]
```

- **Exportieren:** Lädt aktuelle Daten vom Server, triggert Browser-Download als `notenrechner-backup-YYYY-MM-DD.json`
- **Importieren:** Öffnet nativen Datei-Dialog (`.json`), liest Datei ein, validiert `classes`-Array, sendet per POST an `/api/data`, rendert App neu

## Fehlerbehandlung

- Import: Wenn Datei kein gültiges JSON oder kein `classes`-Array → `alert()` mit Fehlermeldung
- Import: Kurze Erfolgsmeldung "Daten wurden geladen" nach erfolgreichem Import

## Was NICHT geändert wird

`server.py`, die Tab-Logik, Berechnungsfunktionen, bestehende Render-Pipeline.
