# Export/Import-Funktion — Implementierungsplan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Export- und Import-Buttons im Sidebar-Footer, die `data.json` als Datei herunterladen bzw. eine Backup-Datei wieder einlesen.

**Architecture:** Reine Frontend-Änderung in `index.html`. Export nutzt einen temporären `<a>`-Download-Link. Import nutzt ein verstecktes `<input type="file">`. Beide Operationen verwenden den bestehenden `/api/data`-Endpunkt (GET für Export, POST für Import). Kein Umbau von `server.py` oder der Berechnungslogik.

**Tech Stack:** Vanilla JS, Fetch API, Bootstrap Icons (bereits vorhanden), Tailwind CSS

---

### Task 1: Sidebar-Footer HTML einfügen

**Files:**
- Modify: `index.html` — nach Zeile 608 (nach dem Oberstufe-Block, vor dem `</div>` das die Sidebar schließt)

**Step 1: HTML-Snippet einfügen**

Nach Zeile 608 (`<div id="class-list-o"></div>`) und vor Zeile 609 (`</div>` — Sidebar-Ende) diesen Block einfügen:

```html
        <div id="sidebar-footer">
            <button class="btn btn-xs btn-outline-secondary w-50" onclick="exportData()" title="Daten als JSON-Datei herunterladen">
                <i class="bi bi-download"></i> Exportieren
            </button>
            <input type="file" id="import-file-input" accept=".json" style="display:none" onchange="importData(event)">
            <button class="btn btn-xs btn-outline-secondary w-50" onclick="document.getElementById('import-file-input').click()" title="Daten aus JSON-Datei laden">
                <i class="bi bi-upload"></i> Importieren
            </button>
        </div>
```

**Step 2: Visuell prüfen**

Datei speichern, Browser neu laden → Zwei Buttons müssen am unteren Ende der Sidebar sichtbar sein.

---

### Task 2: Sidebar-Footer CSS einfügen

**Files:**
- Modify: `index.html` — im `<style type="text/tailwindcss">` Block (unter den bestehenden `@layer components`-Definitionen)

**Step 1: CSS einfügen**

Im `<style>`-Block nach den bestehenden `.sidebar-group-head`, `.class-item` etc. Definitionen hinzufügen:

```css
#sidebar-footer {
    display: flex;
    gap: 4px;
    padding: 8px 8px 10px 8px;
    border-top: 1px solid #e5e7eb;
    margin-top: auto;
}
```

Damit `margin-top: auto` funktioniert, muss `#sidebar` als Flexbox-Spalte konfiguriert sein. Prüfe ob `#sidebar` bereits `display: flex; flex-direction: column;` hat — falls nicht, ergänzen.

**Step 2: Sidebar als Flex-Spalte sicherstellen**

Suche im CSS nach `#sidebar {` und prüfe ob `display: flex` und `flex-direction: column` vorhanden sind. Falls nicht, ergänzen:

```css
#sidebar {
    display: flex;
    flex-direction: column;
    /* ... bestehende Properties behalten ... */
}
```

**Step 3: Visuell prüfen**

Browser neu laden → Footer-Buttons sollen am unteren Ende der Sidebar kleben, mit einer dezenten Trennlinie darüber.

---

### Task 3: `exportData()` Funktion implementieren

**Files:**
- Modify: `index.html` — im JavaScript-Bereich, nach der `saveData()`-Funktion (nach Zeile 809)

**Step 1: Funktion einfügen**

```javascript
function exportData() {
    const date = new Date().toISOString().slice(0, 10);
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notenrechner-backup-${date}.json`;
    a.click();
    URL.revokeObjectURL(url);
}
```

**Step 2: Manuell testen**

Browser neu laden → "Exportieren" klicken → Datei `notenrechner-backup-HEUTE.json` wird heruntergeladen → Datei öffnen und prüfen ob der Inhalt `{"classes": [...]}` korrekt ist.

---

### Task 4: `importData()` Funktion implementieren

**Files:**
- Modify: `index.html` — direkt nach `exportData()` (nach Task 3)

**Step 1: Funktion einfügen**

```javascript
function importData(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        let parsed;
        try {
            parsed = JSON.parse(e.target.result);
        } catch {
            alert('Fehler: Die Datei ist kein gültiges JSON.');
            return;
        }
        if (!parsed.classes || !Array.isArray(parsed.classes)) {
            alert('Fehler: Die Datei enthält keine gültigen Notendaten.');
            return;
        }
        data = parsed;
        saveData();
        render();
        alert('Daten wurden erfolgreich geladen.');
    };
    reader.readAsText(file);
    // Input zurücksetzen damit dieselbe Datei nochmals importiert werden kann
    event.target.value = '';
}
```

**Step 2: Manuell testen — Erfolgsfall**

Browser neu laden → "Importieren" klicken → die zuvor exportierte Backup-Datei auswählen → Alert "Daten wurden erfolgreich geladen" erscheint → App zeigt die importierten Daten korrekt an.

**Step 3: Manuell testen — Fehlerfall**

Eine Textdatei mit ungültigem Inhalt (z.B. `{"foo": "bar"}`) importieren → Alert "Die Datei enthält keine gültigen Notendaten" erscheint → App-Daten unverändert.

---

## Verifikation Ende-zu-Ende

1. App starten (`python server.py`)
2. Eine Klasse anlegen, Schüler hinzufügen, eine Note eingeben
3. "Exportieren" → Datei herunterladen, Inhalt prüfen
4. Daten in der App löschen (Klasse löschen)
5. "Importieren" → Backup-Datei auswählen
6. App zeigt die Klasse mit Schüler und Note wieder korrekt an
7. `data.json` auf dem Server prüfen — muss den importierten Zustand enthalten
