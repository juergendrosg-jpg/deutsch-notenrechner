# Design: Schuljahr-Feature

## Context

Das Notentool verwaltet Klassen mit Schülern und Noten pro Semester. Bisher gibt es keine Möglichkeit, zwischen Schuljahren zu trennen — wenn ein neues Schuljahr beginnt, müssten Klassen manuell neu angelegt und Schüler neu eingetragen werden. Dieses Feature fügt eine "Schuljahr"-Überkategorie hinzu, sodass Schüler in ihrer Klasse bleiben, aber pro Schuljahr neue Noten eingetragen werden.

## Anforderungen

- Schuljahre sind manuell benennbar (z.B. "2024/25")
- Beim Anlegen eines neuen Schuljahres werden alle Klassen mit Schülern übernommen, Noten/Struktur beginnen leer
- Schuljahre bleiben weiterhin bearbeitbar (kein Archiv-Modus)
- Die Sidebar zeigt die Schuljahr-Auswahl oberhalb von Unterstufe/Oberstufe

## Datenstruktur (Ansatz A: Schuljahr als Root-Ebene)

### Neu: `data.json`

```json
{
  "activeSchuljahrId": "sj_abc123",
  "schuljahre": [
    {
      "id": "sj_abc123",
      "name": "2024/25",
      "classes": [ ...unverändertes Klassen-Array... ]
    }
  ]
}
```

### Migration

`migrateData()` wickelt die Migration ab:
- Falls `data.schuljahre` nicht existiert: bestehendes `data.classes` wird in `schuljahre[0]` verpackt (name: "Importiert", id: generiert)
- `activeSchuljahrId` wird auf dieses erste Schuljahr gesetzt

## Globaler State

Neues Feld: `activeSchuljahrId` (analog zu `activeClassId`).

Neue Hilfsfunktion — ersetzt alle direkten `data.classes`-Zugriffe:

```js
function activeClasses() {
  const sj = data.schuljahre.find(s => s.id === data.activeSchuljahrId);
  return sj ? sj.classes : [];
}
```

## UI: Sidebar

Oben in der Sidebar: Schuljahr-Bereich mit Auswahl-Chips und `[+]`-Button.

```
┌─────────────────────────────┐
│  [ 2024/25 ] [ 2025/26 ] [+]│  ← Chips + "Neues Schuljahr"
├─────────────────────────────┤
│  Unterstufe                 │
│    3A                       │
│  Oberstufe                  │
│    7A                       │
└─────────────────────────────┘
```

- Aktives Schuljahr ist hervorgehoben (wie aktive Klasse)
- `[+]` öffnet Modal `modalAddSchuljahr`

## Modal: Neues Schuljahr

- Einziges Textfeld: Name (z.B. "2025/26")
- Beim Bestätigen:
  1. Alle Klassen des aktuell aktiven Schuljahres werden kopiert: `{id (neu), name, type, students}` — ohne `semester1`/`semester2`/`jahresnote`
  2. Neues Schuljahr wird angelegt und als aktiv gesetzt
  3. `activeClassId` wird auf die erste Klasse des neuen Schuljahres gesetzt (oder null wenn keine vorhanden)

## Was unverändert bleibt

- Alle Klassen-/Schüler-/Noten-Funktionen
- Tab-Struktur (Semester 1/2, SA/WDH/Präs/HA/Gesamt/Jahr/Schüler)
- `newClass()`, `addClass()`, `editClass()`, `deleteClass()` — arbeiten auf `activeClasses()`
- Alle Berechnungsfunktionen (`calcGesamtnote`, etc.)

## Kritische Dateien

- `index.html` — alle Änderungen hier (~2000 Zeilen, kein Build-Schritt)
- `data.json` — wird durch Migration automatisch aktualisiert

## Verification

1. `python server.py` starten
2. Bestehendes Schuljahr "2024/25" ist sichtbar, alle alten Klassen/Noten vorhanden
3. `[+]` → Name "2025/26" eingeben → alle Klassen erscheinen leer (Schüler vorhanden, keine Noten)
4. Zwischen Schuljahren wechseln → Noten sind jeweils korrekt getrennt
5. Im alten Schuljahr eine Note ändern → nicht im neuen sichtbar
