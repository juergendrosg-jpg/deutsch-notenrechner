# Spanisch-Klasse Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Neuer Klassen-Typ „spanisch" in `index.html` mit nur Wiederholungen, Präsentationen und Mündlicher Mitarbeit — Gesamtnote als exaktes Drittel je Kategorie, keine Schularbeiten, keine Hausübungen.

**Architecture:** Einzige geänderte Datei ist `index.html`. Der Typ `"spanisch"` wird neben `"unterstufe"` und `"oberstufe"` als dritter `cls.type`-Wert eingeführt. Überall wo der Code auf `cls.type` prüft, wird Spanisch berücksichtigt. Die Berechnung der Gesamtnote ignoriert bei `type === 'spanisch'` die `gewichtung`-Felder und teilt gleichmäßig durch die Anzahl vorhandener Teilnoten.

**Tech Stack:** Vanilla JS, HTML, Tailwind CDN v4 — kein Build-Schritt, Änderungen sofort per Browser-Reload sichtbar.

---

### Task 1: `newClass` — Spanisch-Klasse anlegen

**Files:**
- Modify: `index.html` — Funktion `newClass` (ca. Zeile 1374)

Ziel: `newClass('5A', 'spanisch')` erzeugt eine Klasse ohne `schularbeiten` und ohne `hausaufgaben`, mit leerem `gewichtung`-Objekt.

**Step 1: Implementierung**

Ersetze in `newClass` den Block:

```js
// vorher (vereinfacht):
type = type || 'unterstufe';
const isOberstufe = type === 'oberstufe';
const semBase = () => ({
    schularbeiten: isOberstufe
        ? [{id: genId(), name: '1. Schularbeit'}]
        : [{id: genId(), name: '1. Schularbeit'}, {id: genId(), name: '2. Schularbeit'}],
    wiederholungen: [], praesentationen: [], hausaufgaben: [],
    gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20, muendlich:0},
    studentData: {}
});
```

durch:

```js
type = type || 'unterstufe';
const isOberstufe = type === 'oberstufe';
const isSpanisch  = type === 'spanisch';
const semBase = () => {
    if (isSpanisch) return {
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {},
        studentData: {}
    };
    return {
        schularbeiten: isOberstufe
            ? [{id: genId(), name: '1. Schularbeit'}]
            : [{id: genId(), name: '1. Schularbeit'}, {id: genId(), name: '2. Schularbeit'}],
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20, muendlich:0},
        studentData: {}
    };
};
```

Und den Return-Block anpassen — `activeSaId` darf für Spanisch nicht auf `schularbeiten[0]` zeigen:

```js
// In addClass(), nach newClass():
activeSaId = c.semester1.schularbeiten?.[0]?.id ?? null;
```
Das ist schon optional-chained und klappt auch wenn `schularbeiten` fehlt — kein Change nötig.

**Step 2: Manuell testen**
Starte `python server.py`, öffne http://localhost:5000, lege eine Spanisch-Klasse an (sobald der Button existiert — kommt in Task 2). Prüfe in den DevTools → Network → `/api/data` POST, dass die neue Klasse kein `schularbeiten`-Feld hat.

**Step 3: Commit**
```bash
git add index.html
git commit -m "feat: newClass supports type=spanisch (no schularbeiten/hausaufgaben)"
```

---

### Task 2: Sidebar — Spanisch-Abschnitt

**Files:**
- Modify: `index.html` — HTML-Sidebar (ca. Zeile 655–680) und `renderSidebar()` (ca. Zeile 1781)

**Step 1: HTML-Struktur hinzufügen**

Füge nach dem Oberstufe-Block (ca. Zeile 669) ein:

```html
<div>
    <div class="sidebar-group-head">
        <span class="sidebar-group-label">Spanisch</span>
        <button class="btn btn-xs btn-outline-secondary" id="btn-add-class-s" title="Neue Spanisch-Klasse"><i class="bi bi-plus-lg"></i></button>
    </div>
    <div id="class-list-s"></div>
</div>
```

**Step 2: `renderSidebar()` erweitern**

Ersetze:
```js
const uClasses = activeClasses().filter(c => c.type !== 'oberstufe');
const oClasses = activeClasses().filter(c => c.type === 'oberstufe');
listU.innerHTML = uClasses.length ? uClasses.map(classItem).join('') : empty;
listO.innerHTML = oClasses.length ? oClasses.map(classItem).join('') : empty;
```

durch:
```js
const listS = document.getElementById('class-list-s');
const uClasses = activeClasses().filter(c => c.type === 'unterstufe');
const oClasses = activeClasses().filter(c => c.type === 'oberstufe');
const sClasses = activeClasses().filter(c => c.type === 'spanisch');
listU.innerHTML = uClasses.length ? uClasses.map(classItem).join('') : empty;
listO.innerHTML = oClasses.length ? oClasses.map(classItem).join('') : empty;
if (listS) listS.innerHTML = sClasses.length ? sClasses.map(classItem).join('') : empty;
```

**Step 3: Button-Event registrieren**

Im `DOMContentLoaded`-Block (oder wo `btn-add-class-u` und `btn-add-class-o` gebunden werden — suche nach `btn-add-class-o`), füge analog hinzu:

```js
document.getElementById('btn-add-class-s').addEventListener('click', () => {
    document.getElementById('inp-class-type').value = 'spanisch';
    document.getElementById('inp-class-name').value = '';
    showModal('modalAddClass');
});
```

**Step 4: Manuell testen**
Sidebar zeigt drei Abschnitte. Spanisch-Klasse anlegen funktioniert.

**Step 5: Commit**
```bash
git add index.html
git commit -m "feat: sidebar Spanisch section with add button"
```

---

### Task 3: Migration — Spanisch-Klassen korrekt behandeln

**Files:**
- Modify: `index.html` — `migrateData()` (ca. Zeile 986)

**Step 1: Schularbeiten-Auffüllung nur für Unterstufe**

Der Block „Ensure exactly 2 Schularbeiten" (ca. Zeile 1083) prüft bereits `cls.type === 'unterstufe'` — **kein Change nötig**.

**Step 2: `semester2` Default ohne Schularbeiten für Spanisch**

Der Block „Ensure semester2 exists" (ca. Zeile 1071) legt immer `schularbeiten` an. Ersetze:

```js
if (!cls.semester2) {
    cls.semester2 = {
        schularbeiten: [{id: genId(), name: '1. Schularbeit'}, {id: genId(), name: '2. Schularbeit'}],
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20},
        studentData: {}
    };
}
```

durch:

```js
if (!cls.semester2) {
    if (cls.type === 'spanisch') {
        cls.semester2 = {
            wiederholungen: [], praesentationen: [], hausaufgaben: [],
            gewichtung: {},
            studentData: {}
        };
    } else {
        cls.semester2 = {
            schularbeiten: [{id: genId(), name: '1. Schularbeit'}, {id: genId(), name: '2. Schularbeit'}],
            wiederholungen: [], praesentationen: [], hausaufgaben: [],
            gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20},
            studentData: {}
        };
    }
}
```

**Step 3: `muendlich`-Default auch für Spanisch**

Der Block für `muendlich === undefined` (ca. Zeile 1106) läuft über alle Semester aller Klassen — funktioniert auch für Spanisch, kein Change nötig.

**Step 4: Commit**
```bash
git add index.html
git commit -m "fix: migration skips schularbeiten for spanisch classes"
```

---

### Task 4: Gesamtnote — exakte Drittel für Spanisch

**Files:**
- Modify: `index.html` — `calcGesamtnote()` (ca. Zeile 1261)

**Step 1: Spanisch-Branch einfügen**

Am Anfang von `calcGesamtnote`, vor dem bestehenden Code:

```js
function calcGesamtnote(cls, sem, s) {
    if (cls.type === 'spanisch') {
        const wdhNote   = calcWdhTeilnote(sem, s.id);
        const praesNote = calcPraesTeilnote(sem, s.id);
        const mmNote    = calcMMTeilnote(sem, s.id);
        const parts = [wdhNote, praesNote, mmNote].filter(v => v !== null);
        if (parts.length === 0) return null;
        return parts.reduce((a, b) => a + b, 0) / parts.length;
    }
    // ... bestehender Code bleibt unverändert
```

**Step 2: `effectiveSemesterNote` — keine SA-Zwangs-5 für Spanisch**

Die Funktion prüft bereits `cls.type !== 'oberstufe'` vor `hasPositiveSA`. Da Spanisch auch nicht Oberstufe ist, würde sie die Prüfung machen — aber Spanisch hat keine Schularbeiten. Ergänze:

```js
function effectiveSemesterNote(cls, sem, s) {
    const sas = sem.schularbeiten || [];
    const sd  = sem.studentData?.[s.id] || {};
    const hasSAData = sas.some(sa => sd.schularbeiten?.[sa.id]);
    if (cls.type !== 'oberstufe' && cls.type !== 'spanisch' && hasSAData && !hasPositiveSA(sem, s)) return 5;
    return calcGesamtnoteAdjusted(cls, sem, s);
}
```

**Step 3: Manuell testen**
Spanisch-Klasse anlegen, Schüler:innen anlegen, Wdh./Präs./MM eintragen → Gesamtnote-Tab zeigt korrekte Drittel-Note.

**Step 4: Commit**
```bash
git add index.html
git commit -m "feat: calcGesamtnote uses equal thirds for spanisch classes"
```

---

### Task 5: Tabs — SA und HÜ für Spanisch ausblenden

**Files:**
- Modify: `index.html` — `renderContent()` (ca. Zeile 1800)

**Step 1: Tab-Bar konditionell rendern**

Ersetze die Tab-Bar-Generierung (die `<ul class="nav class-tabs">` Zeile):

```js
${activeTab!=='jahr'&&activeTab!=='schueler' ? `<ul class="nav class-tabs" id="class-tabs">
    <li class="nav-item"><a class="nav-link ${activeTab==='sa'?'active':''}" href="#" onclick="selectTab('sa');return false;"><i class="bi bi-pencil-square me-1"></i>Schularbeiten</a></li>
    <li class="nav-item"><a class="nav-link ${activeTab==='wdh'?'active':''}" ...
    ...
    <li class="nav-item"><a class="nav-link ${activeTab==='ha'?'active':''}" href="#" onclick="selectTab('ha');return false;"><i class="bi bi-house me-1"></i>Hausübungen</a></li>
    ...
</ul>` : ''}
```

durch (den Spanisch-Zweig einbauen):

```js
${activeTab!=='jahr'&&activeTab!=='schueler' ? `<ul class="nav class-tabs" id="class-tabs">
    ${cls.type !== 'spanisch' ? `<li class="nav-item"><a class="nav-link ${activeTab==='sa'?'active':''}" href="#" onclick="selectTab('sa');return false;"><i class="bi bi-pencil-square me-1"></i>Schularbeiten</a></li>` : ''}
    <li class="nav-item"><a class="nav-link ${activeTab==='wdh'?'active':''}" href="#" onclick="selectTab('wdh');return false;"><i class="bi bi-journal-check me-1"></i>Wiederholungen</a></li>
    <li class="nav-item"><a class="nav-link ${activeTab==='praes'?'active':''}" href="#" onclick="selectTab('praes');return false;"><i class="bi bi-mic me-1"></i>Präsentationen</a></li>
    ${cls.type !== 'spanisch' ? `<li class="nav-item"><a class="nav-link ${activeTab==='ha'?'active':''}" href="#" onclick="selectTab('ha');return false;"><i class="bi bi-house me-1"></i>Hausübungen</a></li>` : ''}
    <li class="nav-item"><a class="nav-link ${activeTab==='mm'?'active':''}" href="#" onclick="selectTab('mm');return false;"><i class="bi bi-chat-dots me-1"></i>Mündl. Mitarbeit</a></li>
    <li class="nav-item"><a class="nav-link ${activeTab==='gesamt'?'active':''}" href="#" onclick="selectTab('gesamt');return false;"><i class="bi bi-calculator me-1"></i>Gesamtnote</a></li>
</ul>` : ''}
```

**Step 2: `selectClass` — Default-Tab für Spanisch**

In `selectClass()`:
```js
function selectClass(id) {
    activeClassId = id;
    const _selCls = activeClasses().find(c => c.id === id);
    activeSaId = _selCls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
    activeTab = _selCls?.type === 'spanisch' ? 'wdh' : 'sa';
    renderSidebar(); renderContent();
}
```

**Step 3: `selectSemester` — Default-Tab für Spanisch**
```js
function selectSemester(sem) {
    activeSemester = sem;
    const cls = activeClasses().find(c => c.id === activeClassId);
    activeSaId = cls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
    if (activeTab === 'jahr' || activeTab === 'schueler') activeTab = cls?.type === 'spanisch' ? 'wdh' : 'sa';
    else if (cls?.type === 'spanisch' && (activeTab === 'sa' || activeTab === 'ha')) activeTab = 'wdh';
    renderContent();
}
```

**Step 4: Manuell testen**
- Spanisch-Klasse wählen → kein SA-Tab, kein HÜ-Tab, erster Tab ist Wiederholungen
- Semester wechseln → bleibt auf Wdh. (nicht auf SA springen)
- Deutsch-Klasse wählen → alle Tabs wie gewohnt

**Step 5: Commit**
```bash
git add index.html
git commit -m "feat: hide SA and HA tabs for spanisch classes, default tab=wdh"
```

---

### Task 6: Gesamtnote-Tab — Spalten für Spanisch anpassen

**Files:**
- Modify: `index.html` — `renderTabGesamt()` (ca. Zeile 2395)

Für Spanisch soll der Gesamtnote-Tab keine SA-Spalten und keine HÜ-Spalte zeigen, und das Gewichtungs-Widget zeigt „je ⅓" statt editierbarer Inputs.

**Step 1: Gewichtungs-Widget**

Am Anfang von `renderTabGesamt`, ersetze den `weight-card`-Block durch:

```js
const isSpanisch = cls.type === 'spanisch';
```

Dann den `weight-card` div:

```js
<div class="weight-card">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <strong>Gewichtung der Teilnoten</strong>
        ${isSpanisch
            ? '<span class="weight-sum-ok">je ⅓ (fix)</span>'
            : `<span class="${warnClass}" id="weight-sum-display">${warnTxt}</span>`}
    </div>
    ${isSpanisch
        ? `<div class="d-flex flex-wrap gap-3">
               <div class="weight-item"><label>Wiederholung</label><span class="form-control form-control-sm" style="width:70px;text-align:center">⅓</span></div>
               <div class="weight-item"><label>Präsentation</label><span class="form-control form-control-sm" style="width:70px;text-align:center">⅓</span></div>
               <div class="weight-item"><label>Mündl. Mitarbeit</label><span class="form-control form-control-sm" style="width:70px;text-align:center">⅓</span></div>
           </div>`
        : `<div class="d-flex flex-wrap gap-3 align-items-end">
               ${weightInput('schularbeiten', 'Schularbeiten', g.schularbeiten)}
               ${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
               ${weightInput('praesentation','Präsentation',  g.praesentation)}
               ${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
               ${weightInput('muendlich','Mündl. Mitarbeit', g.muendlich)}
               ${activeSemester === 'semester2' ? `<button ...>↩ Gewichtungen aus 1. Sem. übernehmen</button>` : ''}
           </div>`}
</div>
```

**Step 2: Tabellenkopf und -zeilen konditionell**

Im Tabellenkopf (`<thead>`):
```js
${!isSpanisch ? `<th ...>SA gesamt...</th>` : ''}
${!isSpanisch ? sas.map(sa => ...).join('') : ''}
<th ...>Wdh.</th>
<th ...>Präs.</th>
${!isSpanisch ? `<th ...>HÜ</th>` : ''}
<th ...>Mündl.</th>
```

In den Tabellenzeilen analog dieselben Spalten weglassen.

**Step 3: Manuell testen**
Gesamtnote-Tab Spanisch: zeigt nur Wdh./Präs./Mündl.-Spalten, Gewichtung „je ⅓", korrekte Gesamtnote.

**Step 4: Commit**
```bash
git add index.html
git commit -m "feat: gesamt tab shows thirds layout for spanisch classes"
```

---

### Task 7: Schuljahr-Kopie — Spanisch-Klassen korrekt duplizieren

**Files:**
- Modify: `index.html` — `addSchuljahr()` (ca. Zeile 1411)

`addSchuljahr` ruft `newClass(cls.name, cls.type)` auf — das funktioniert bereits korrekt nachdem Task 1 erledigt ist. Kein weiterer Change nötig, aber:

**Step 1: Verifizieren**
Neues Schuljahr anlegen wenn eine Spanisch-Klasse existiert → im neuen Schuljahr erscheint die Spanisch-Klasse korrekt im Spanisch-Abschnitt, ohne Schularbeiten.

**Step 2: Commit (wenn alles passt)**
```bash
git add index.html
git commit -m "test: verify spanisch class copy on new Schuljahr"
```

---

### Abschluss-Test (manuell)

1. Server starten: `python server.py`
2. Spanisch-Klasse „5B" anlegen
3. 3 Schüler:innen hinzufügen
4. Wiederholung anlegen, Punkte eintragen
5. Präsentation anlegen, Noten eintragen
6. Mündl. Mitarbeit eintragen
7. Gesamtnote-Tab: alle drei Teilnoten sichtbar, Gesamtnote = arithmetisches Mittel der drei
8. Semester 2 öffnen → gleiche Struktur, kein SA-Tab
9. Jahresnote-Tab → funktioniert
10. Deutschklasse wählen → alle Tabs unverändert
11. Neues Schuljahr → Spanisch-Klasse wird korrekt kopiert
