# Semester-Sperre Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow each class's semesters to be individually locked to prevent accidental edits after grading is complete.

**Architecture:** A `locked` boolean flag is stored directly on each semester object in `data.json`. On every render, all tab functions check this flag via a shared helper `isSemesterLocked()`. When locked, inputs are disabled, add/edit/delete buttons are hidden, and a banner is shown at the top of the tab content. The lock icon lives in the semester tab bar and has its own click handler separate from tab selection.

**Tech Stack:** Vanilla JS, Bootstrap Icons (`bi-lock-fill`, `bi-unlock`), Tailwind CDN v4. No build step — all changes in `index.html`. Server runs with `python server.py`.

---

### Task 1: Helper and toggle functions

**Files:**
- Modify: `index.html` — add two functions after `saveData()` (around line 982)

**Step 1: Add `isSemesterLocked` and `toggleSemesterLock` after the `saveData` function**

Find this line (~982):
```js
function exportData() {
```

Insert before it:
```js
function isSemesterLocked(cls, sem) {
    return cls?.[sem]?.locked === true;
}

function toggleSemesterLock(semKey) {
    const cls = activeClasses().find(c => c.id === activeClassId);
    if (!cls) return;
    const isLocked = isSemesterLocked(cls, semKey);
    const semLabel = semKey === 'semester1' ? '1. Semester' : '2. Semester';
    const msg = isLocked
        ? `Sperre für ${semLabel} aufheben?`
        : `${semLabel} sperren? Alle Eingaben werden schreibgeschützt.`;
    if (!confirm(msg)) return;
    cls[semKey].locked = !isLocked;
    saveData();
    render();
}
```

**Step 2: Manually test in browser**

- Start server: `python server.py`
- Open browser console, call `toggleSemesterLock('semester1')` — confirm dialog should appear, clicking OK should toggle `data.classes[0].semester1.locked` (check in console: `data.classes[0].semester1.locked`)

**Step 3: Commit**

```
git add index.html
git commit -m "feat: add isSemesterLocked and toggleSemesterLock helpers"
```

---

### Task 2: Lock icon in semester tab bar

**Files:**
- Modify: `index.html:1979-1984` — the semester tab bar inside `renderContent()`

**Step 1: Replace the two semester tab divs**

Current code (lines 1980-1981):
```js
<div class="semester-tab ${activeTab!=='jahr'&&activeTab!=='schueler'&&activeSemester==='semester1'?'active':''}" onclick="selectSemester('semester1')">1. Semester</div>
<div class="semester-tab ${activeTab!=='jahr'&&activeTab!=='schueler'&&activeSemester==='semester2'?'active':''}" onclick="selectSemester('semester2')">2. Semester</div>
```

Replace with:
```js
<div class="semester-tab ${activeTab!=='jahr'&&activeTab!=='schueler'&&activeSemester==='semester1'?'active':''} ${isSemesterLocked(cls,'semester1')?'sem-locked':''}" onclick="selectSemester('semester1')">
    ${isSemesterLocked(cls,'semester1') ? '<i class="bi bi-lock-fill" style="font-size:.8em;margin-right:3px;opacity:.7"></i>' : (activeSemester==='semester1'&&activeTab!=='jahr'&&activeTab!=='schueler' ? '<i class="bi bi-unlock" style="font-size:.8em;margin-right:3px;opacity:.4;cursor:pointer" onclick="event.stopPropagation();toggleSemesterLock(\'semester1\')" title="Semester sperren"></i>' : '')}
    1. Semester
    ${isSemesterLocked(cls,'semester1') ? `<i class="bi bi-lock-fill" onclick="event.stopPropagation();toggleSemesterLock('semester1')" title="Sperre aufheben" style="font-size:.85em;margin-left:4px;cursor:pointer;opacity:.8"></i>` : ''}
</div>
<div class="semester-tab ${activeTab!=='jahr'&&activeTab!=='schueler'&&activeSemester==='semester2'?'active':''} ${isSemesterLocked(cls,'semester2')?'sem-locked':''}" onclick="selectSemester('semester2')">
    ${isSemesterLocked(cls,'semester2') ? '<i class="bi bi-lock-fill" style="font-size:.8em;margin-right:3px;opacity:.7"></i>' : (activeSemester==='semester2'&&activeTab!=='jahr'&&activeTab!=='schueler' ? '<i class="bi bi-unlock" style="font-size:.8em;margin-right:3px;opacity:.4;cursor:pointer" onclick="event.stopPropagation();toggleSemesterLock(\'semester2\')" title="Semester sperren"></i>' : '')}
    2. Semester
    ${isSemesterLocked(cls,'semester2') ? `<i class="bi bi-lock-fill" onclick="event.stopPropagation();toggleSemesterLock('semester2')" title="Sperre aufheben" style="font-size:.85em;margin-left:4px;cursor:pointer;opacity:.8"></i>` : ''}
</div>
```

**Note on the icon logic:**
- If semester is **locked**: show `bi-lock-fill` before the label (decorative) + clickable `bi-lock-fill` after the label (to unlock). Both show for either active/inactive tab.
- If semester is **unlocked** and **active**: show a faint `bi-unlock` before the label (clickable, to lock). Hidden when tab not active to reduce clutter.

**Step 2: Add `.sem-locked` CSS style**

Find the `.semester-tab.active` style block (around line 387) and add after it:
```css
.semester-tab.sem-locked { opacity: .7; font-style: italic; }
```

**Step 3: Test in browser**

- Lock semester 1 via console: `toggleSemesterLock('semester1')`
- Verify: tab shows lock icon, tab is slightly dimmed/italic
- Click the lock icon → confirm dialog → tab unlocks
- Switch to unlocked active tab → faint unlock icon visible

**Step 4: Commit**

```
git add index.html
git commit -m "feat: show lock icon in semester tab bar"
```

---

### Task 3: Locked banner in renderTabContent

**Files:**
- Modify: `index.html:2024-2052` — `renderTabContent()` function

**Step 1: Add locked banner injection after switch statement**

After the `switch(activeTab)` block (after line 2040 `attachTopScrollbars()`), add a banner prepend. Replace this section of `renderTabContent`:

```js
switch(activeTab) {
    case 'sa':     area.innerHTML = renderTabSA(cls, sem);     attachSAListeners();    break;
    case 'wdh':    area.innerHTML = renderTabWDH(cls, sem);    attachWDHListeners();   break;
    case 'praes':  area.innerHTML = renderTabPraes(cls, sem);  attachPraesListeners(); break;
    case 'ha':     area.innerHTML = renderTabHA(cls, sem);     attachHAListeners();    break;
    case 'mm':       area.innerHTML = renderTabMM(cls, sem);        attachMMListeners();       break;
    case 'gesamt':   area.innerHTML = renderTabGesamt(cls, sem);    attachGesamtListeners();   break;
    case 'jahr':     area.innerHTML = renderTabJahresnote(cls);     attachJahrListeners();     break;
    case 'schueler': area.innerHTML = renderTabSchueler(cls);       attachSchuelerListeners(); break;
}
```

With:
```js
switch(activeTab) {
    case 'sa':     area.innerHTML = renderTabSA(cls, sem);     attachSAListeners();    break;
    case 'wdh':    area.innerHTML = renderTabWDH(cls, sem);    attachWDHListeners();   break;
    case 'praes':  area.innerHTML = renderTabPraes(cls, sem);  attachPraesListeners(); break;
    case 'ha':     area.innerHTML = renderTabHA(cls, sem);     attachHAListeners();    break;
    case 'mm':       area.innerHTML = renderTabMM(cls, sem);        attachMMListeners();       break;
    case 'gesamt':   area.innerHTML = renderTabGesamt(cls, sem);    attachGesamtListeners();   break;
    case 'jahr':     area.innerHTML = renderTabJahresnote(cls);     attachJahrListeners();     break;
    case 'schueler': area.innerHTML = renderTabSchueler(cls);       attachSchuelerListeners(); break;
}
const semTabs = ['sa','wdh','praes','ha','mm','gesamt'];
if (semTabs.includes(activeTab) && isSemesterLocked(cls, activeSemester)) {
    const semLabel = activeSemester === 'semester1' ? '1. Semester' : '2. Semester';
    const banner = document.createElement('div');
    banner.innerHTML = `<div style="background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:8px 14px;margin-bottom:12px;font-size:.88rem;color:#854d0e;display:flex;align-items:center;gap:8px;"><i class="bi bi-lock-fill"></i> <span>Das <strong>${semLabel}</strong> ist gesperrt — keine Änderungen möglich. <button onclick="toggleSemesterLock('${activeSemester}')" style="background:none;border:none;color:#92400e;text-decoration:underline;cursor:pointer;padding:0;font-size:inherit">Entsperren</button></span></div>`;
    area.insertBefore(banner.firstElementChild, area.firstChild);
}
```

**Step 2: Test in browser**

- Lock a semester, navigate to WDH tab — yellow banner should appear at top
- Click "Entsperren" link in banner → confirm dialog → banner disappears
- Jahresnote and Schüler:innen tabs should NOT show the banner

**Step 3: Commit**

```
git add index.html
git commit -m "feat: show locked banner in tab content when semester is locked"
```

---

### Task 4: Lock renderTabSA

**Files:**
- Modify: `index.html:2078-2249` — `renderTabSA(cls, sem)` function

**Step 1: Add locked flag at top of renderTabSA**

After `function renderTabSA(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Disable the "add SA" button and delete SA button when locked**

Line ~2092:
```js
${isOberstufe && canAddSA ? `<button class="sa-tab-add" onclick="addSA()" title="2. Schularbeit hinzufügen">+</button>` : ''}
```
Replace with:
```js
${isOberstufe && canAddSA && !locked ? `<button class="sa-tab-add" onclick="addSA()" title="2. Schularbeit hinzufügen">+</button>` : ''}
```

And line ~2090 (delete SA button):
```js
${isOberstufe && sas.length > 1 ? `<button class="sa-tab-del" onclick="deleteSA('${sa.id}')" title="Entfernen">×</button>` : ''}
```
Replace with:
```js
${isOberstufe && sas.length > 1 && !locked ? `<button class="sa-tab-del" onclick="deleteSA('${sa.id}')" title="Entfernen">×</button>` : ''}
```

**Step 3: Disable all cell inputs in SA rows**

Find the `renderSARowOberstufe` and standard SA row rendering. Search for `cell-input` in the SA table body. The inputs get `disabled` attribute added when `locked`:

In `renderSARowOberstufe` (find with grep: `function renderSARowOberstufe`), add `locked` parameter and pass `${locked ? 'disabled' : ''}` to each `<input>` and `<select>`.

Find the function signature and pass `locked` through:
```js
${cls.students.map(s => renderSARowOberstufe(getSData(sem, s.id), s, activeSaId)).join('')}
```
Change to:
```js
${cls.students.map(s => renderSARowOberstufe(getSData(sem, s.id), s, activeSaId, locked)).join('')}
```

Then in `function renderSARowOberstufe(sd, s, saId, locked=false)`, add `${locked?'disabled':''}` to the note select and kommentar textarea.

Also disable the `fpp-inp` (Fehler pro Punkt) input in the table header when locked by adding `${locked?'disabled':''}` to that input.

For the standard (non-Oberstufe) SA rows: find the `renderSARow` function (grep for it) and add `locked` parameter similarly.

**Step 4: Test in browser**

- Lock semester, go to SA tab — inputs should be grayed out, add button hidden
- Unlock — inputs become editable again

**Step 5: Commit**

```
git add index.html
git commit -m "feat: disable SA tab inputs and buttons when semester is locked"
```

---

### Task 5: Lock renderTabWDH

**Files:**
- Modify: `index.html:2251-2313` — `renderTabWDH(cls, sem)` function

**Step 1: Add locked flag**

After `function renderTabWDH(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Hide "Wiederholung hinzufügen" button when locked**

Line ~2257:
```js
<button class="btn btn-sm btn-primary" onclick="openAddWdh()"><i class="bi bi-plus-lg me-1"></i>Wiederholung</button>
```
Replace with:
```js
${!locked ? `<button class="btn btn-sm btn-primary" onclick="openAddWdh()"><i class="bi bi-plus-lg me-1"></i>Wiederholung</button>` : ''}
```

**Step 3: Hide edit/delete buttons per WDH column header when locked**

Lines ~2275-2276 (Bearbeiten/Löschen buttons in `<th>`):
```js
<button class="btn btn-xs btn-outline-light" onclick="openEditWdh('${w.id}')" title="Bearbeiten"><i class="bi bi-pencil"></i></button>
<button class="btn btn-xs btn-outline-danger" onclick="openDeleteWdh('${w.id}')" title="Löschen"><i class="bi bi-trash"></i></button>
```
Wrap in: `${!locked ? `...` : ''}`

**Step 4: Disable WDH point inputs and absent checkboxes when locked**

Line ~2297:
```js
<input class="cell-input wdh-inp" type="number" ...>
```
Add `${locked ? 'disabled' : ''}` to the input attributes.

Line ~2302:
```js
<input type="checkbox" class="wdh-absent" ...>
```
Add `${locked ? 'disabled' : ''}`.

**Step 5: Test and commit**

```
git add index.html
git commit -m "feat: disable WDH tab inputs and buttons when semester is locked"
```

---

### Task 6: Lock renderTabPraes

**Files:**
- Modify: `index.html:2349-2410` — `renderTabPraes(cls, sem)` function

**Step 1: Add locked flag**

After `function renderTabPraes(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Hide "Präsentation hinzufügen" button**

Line ~2355:
```js
<button class="btn btn-sm btn-primary" onclick="openAddPraes()">...
```
Wrap in `${!locked ? `...` : ''}`.

**Step 3: Hide edit/delete buttons per Präsentation column**

Find the `<th>` buttons for Präs (Bearbeiten/Löschen) and wrap in `${!locked ? ... : ''}`.

**Step 4: Disable grade select inputs in Präs table body**

Find the `<select>` for each student's Präs grade and add `${locked ? 'disabled' : ''}`.

**Step 5: Test and commit**

```
git add index.html
git commit -m "feat: disable Praes tab inputs and buttons when semester is locked"
```

---

### Task 7: Lock renderTabHA

**Files:**
- Modify: `index.html:2411-2565` — `renderTabHA(cls, sem)` function

**Step 1: Add locked flag**

After `function renderTabHA(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Hide "Hausübung hinzufügen" button**

Line ~2417:
```js
<button class="btn btn-sm btn-primary" onclick="openAddHA()">...
```
Wrap in `${!locked ? `...` : ''}`.

**Step 3: Hide edit/delete buttons per HA column**

Lines ~2434-2435 (pencil + trash buttons in `<th>`):
```js
<button class="btn btn-xs btn-outline-light" onclick="openEditHA('${h.id}')">...
<button class="btn btn-xs btn-outline-danger" onclick="openDeleteHA('${h.id}')">...
```
Wrap in `${!locked ? `...` : ''}`.

**Step 4: Disable "Für alle" row selects when locked**

Line ~2453:
```js
<select class="ha-alle-select" data-hid="${h.id}">
```
Add `${locked ? 'disabled' : ''}`.

**Step 5: Disable per-student HA selects**

Line ~2476:
```js
<select class="ha-select" data-sid="${s.id}" data-hid="${h.id}">
```
Add `${locked ? 'disabled' : ''}`.

**Step 6: Test and commit**

```
git add index.html
git commit -m "feat: disable HA tab inputs and buttons when semester is locked"
```

---

### Task 8: Lock renderTabMM

**Files:**
- Modify: `index.html:2566-2605` — `renderTabMM(cls, sem)` function

**Step 1: Add locked flag**

After `function renderTabMM(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Disable note select and kommentar textarea**

Line ~2585:
```js
<select class="cell-input mm-note-sel" data-sid="${s.id}">
```
Add `${locked ? 'disabled' : ''}`.

Line ~2590:
```js
<textarea class="komm-input mm-komm-ta" ...>
```
Add `${locked ? 'disabled' : ''}`.

**Step 3: Test and commit**

```
git add index.html
git commit -m "feat: disable MM tab inputs when semester is locked"
```

---

### Task 9: Lock renderTabGesamt (Gewichtungen)

**Files:**
- Modify: `index.html:2610+` — `renderTabGesamt(cls, sem)` and `weightInput()` helper

**Step 1: Add locked flag in renderTabGesamt**

After `function renderTabGesamt(cls, sem) {`, add:
```js
const locked = isSemesterLocked(cls, activeSemester);
```

**Step 2: Pass locked to weightInput calls**

All 5 `weightInput(...)` calls (lines ~2634-2638):
```js
${weightInput('schularbeiten', 'Schularbeiten', g.schularbeiten)}
${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
...
```
Change to pass `locked` as 4th argument:
```js
${weightInput('schularbeiten', 'Schularbeiten', g.schularbeiten, locked)}
${weightInput('wiederholung','Wiederholung',   g.wiederholung, locked)}
${weightInput('praesentation','Präsentation',  g.praesentation, locked)}
${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben, locked)}
${weightInput('muendlich','Mündl. Mitarbeit', g.muendlich, locked)}
```

**Step 3: Hide "Gewichtungen aus 1. Sem. übernehmen" button when locked**

Line ~2639:
```js
${activeSemester === 'semester2' ? `<button ...>↩ Gewichtungen aus 1. Sem. übernehmen</button>` : ''}
```
Change condition to `${activeSemester === 'semester2' && !locked ? ...}`.

**Step 4: Update `weightInput` function signature**

`function weightInput(key, label, val)` → `function weightInput(key, label, val, locked=false)`

Add `${locked ? 'disabled' : ''}` to the `<input>` inside.

**Step 5: Test and commit**

```
git add index.html
git commit -m "feat: disable Gesamt tab weight inputs when semester is locked"
```

---

### Task 10: Final integration test

**Step 1: Full walkthrough**

1. Open app in browser
2. Select a class, enter some grades in semester 1
3. Lock semester 1 via the tab icon
4. Verify: yellow banner in all tabs (SA, WDH, Praes, HA, MM, Gesamt)
5. Verify: all inputs disabled, add/edit/delete buttons hidden
6. Switch to semester 2 — verify it's still fully editable
7. Switch to Schüler:innen tab — verify it's still fully editable (no lock)
8. Unlock semester 1 — verify everything returns to normal
9. Reload page — verify lock state persists (saved in data.json)

**Step 2: Check data.json**

```
cat data.json
```
Confirm `"locked": true` appears in the semester object.

**Step 3: Final commit if any cleanup needed**

```
git add index.html
git commit -m "feat: complete semester lock feature"
```
