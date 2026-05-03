# Undo/Redo Design — 2026-04-26

## Anforderungen

- 1 Schritt Undo + 1 Schritt Redo
- Nur Noteneingaben (SA, Wdh, Präs, HA, Gewichtung) — keine strukturellen Änderungen
- Buttons in der Navbar unter dem Darkmodus-Button

## Ansatz: Snapshot vor Mutation (Option A)

### Zustand

```js
let undoSnapshot = null;  // Deep-Clone von data vor letzter Noteneingabe
let redoSnapshot = null;  // Deep-Clone von data vor letztem Undo
```

### Neue Funktionen

**`saveDataWithUndo()`** — ersetzt `saveData()` bei allen Noteneingabe-Mutationen:
1. `undoSnapshot = JSON.parse(JSON.stringify(data))` (Deep-Clone)
2. `redoSnapshot = null` (neue Aktion löscht Redo-Pfad)
3. `saveData()` + `render()` wie bisher
4. `updateUndoButtons()` aufrufen

**`undoData()`**:
1. Guard: falls `undoSnapshot === null`, abbrechen
2. `redoSnapshot = JSON.parse(JSON.stringify(data))`
3. `data = undoSnapshot; undoSnapshot = null`
4. `saveData()` + `render()` + `updateUndoButtons()`

**`redoData()`**:
1. Guard: falls `redoSnapshot === null`, abbrechen
2. `undoSnapshot = JSON.parse(JSON.stringify(data))`
3. `data = redoSnapshot; redoSnapshot = null`
4. `saveData()` + `render()` + `updateUndoButtons()`

**`updateUndoButtons()`** — setzt `disabled`-Attribut der Navbar-Buttons.

### Mutationen die `saveDataWithUndo()` verwenden

- SA-Felder: `aufgabenstellung`, `fehler`, `wortschatz`, `textorganisation`, `kommentar`, `fehlerProPunkt`
- Wiederholung-Punkte
- Präsentation-Note
- Hausaufgabe-Status
- Gewichtung (alle Felder)

### Mutationen die weiter `saveData()` verwenden (keine Undo-Unterstützung)

- Klasse hinzufügen/umbenennen/löschen
- Schüler hinzufügen/umbenennen/löschen
- Schularbeit/Wdh/Präs/HA hinzufügen/umbenennen/löschen

### UI

Navbar-Erweiterung unter `#theme-toggle`:

```html
<button id="btn-undo" onclick="undoData()" title="Rückgängig" disabled>
    <i class="bi bi-arrow-counterclockwise"></i>
</button>
<button id="btn-redo" onclick="redoData()" title="Wiederholen" disabled>
    <i class="bi bi-arrow-clockwise"></i>
</button>
```

Styling analog zum bestehenden `#theme-toggle`.
