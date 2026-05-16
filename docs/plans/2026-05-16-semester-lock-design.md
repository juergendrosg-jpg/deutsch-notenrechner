# Design: Semester-Sperre

**Datum:** 2026-05-16  
**Status:** Genehmigt

## Ziel

Ein abgeschlossenes Semester pro Klasse sperren können, um versehentliche Änderungen zu verhindern. Jede Klasse verwaltet ihre Semester-Sperren unabhängig. Sperren und Entsperren je mit Bestätigung.

## Datenmodell

`locked` ist ein optionales Boolean direkt im Semester-Objekt:

```json
"semester1": { "locked": true, "schularbeiten": [...], ... }
```

Fehlendes Flag = `false` — keine Migration nötig, überall `sem.locked ?? false` prüfen.

## UI — Schloss-Icon im Semester-Tab

Das Schloss-Icon (`bi-lock-fill` / `bi-unlock`) erscheint direkt neben dem Label im Semester-Tab. Das Icon hat einen eigenen `onclick`-Handler, damit Tab-Wechsel und Sperren getrennte Aktionen bleiben.

```
[ 🔒 1. Semester ]  [ 2. Semester ]  [ Jahresnote ]  [ Schüler:innen ]
```

- Gesperrtes Semester: `bi-lock-fill`, gedämpfte Farbe im Tab
- Entsperrtes Semester: `bi-unlock` (nur sichtbar wenn Tab aktiv, um Unordnung zu vermeiden)

## Gesperrter Zustand

Wenn `sem.locked === true` für das aktive Semester:

- Alle `<input>`, `<select>`, `<textarea>` werden mit `disabled` gerendert
- Alle „Hinzufügen"-Buttons (neue SA, WDH, Präs, HA) werden ausgeblendet
- Gewichtungs-Inputs im Gesamt-Tab werden disabled
- Ein Hinweis-Banner erscheint oben im Tab-Content: *„Dieses Semester ist gesperrt."*
- Der Schüler:innen-Tab bleibt vollständig editierbar

## Bestätigung

**Sperren:** `confirm("1. Semester sperren? Alle Eingaben werden schreibgeschützt.")`  
**Entsperren:** `confirm("Sperre für 1. Semester aufheben?")`

Bei OK: Flag setzen → `saveData()` → `render()`

## Hilfsfunktion

```js
function isSemesterLocked(cls, sem) {
  return cls?.[sem]?.locked === true;
}
```

Wird überall aufgerufen wo Inputs/Buttons gerendert werden.

## Abgrenzung

- Schüler:innen-Liste bleibt immer editierbar (auch bei gesperrtem Semester)
- Jahresnote-Tab ist read-only (wird durch Sperre nicht beeinflusst)
- Keine serverseitige Validierung — Schutz ist rein UI-seitig (ausreichend für Single-User-App)
