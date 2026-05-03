# Mündliche Mitarbeit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Mündliche Mitarbeit" tab with one Note (1–5) + Kommentar per student per semester, included in Gesamtnote with its own configurable weight.

**Architecture:** Single file (`index.html`) change only. Data stored in `studentData[sid].muendlicheMitarbeit = {note, kommentar}` and `sem.gewichtung.muendlich`. Migration handles existing data. No server changes needed.

**Tech Stack:** Vanilla JS, Tailwind CDN v4, Bootstrap Icons — no build step.

---

### Task 1: Migration + data defaults

**Files:**
- Modify: `index.html:1093-1109` (migration block after zwischenpruefung)
- Modify: `index.html:1511-1513` (`getSData`)
- Modify: `index.html:1352-1368` (`newClass`)

**Step 1: Add `muendlich` to `newClass()` gewichtung default (line 1360)**

Change:
```js
gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20},
```
To:
```js
gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20, muendlich:0},
```
This applies to the `semBase` factory inside `newClass()`.

**Step 2: Add `muendlicheMitarbeit` to `getSData()` default (line 1512)**

Change:
```js
if (!sem.studentData[sid]) sem.studentData[sid] = {schularbeiten:{}, wiederholungen:{}, praesentationen:{}, hausaufgaben:{}, zwischenpruefung: null};
```
To:
```js
if (!sem.studentData[sid]) sem.studentData[sid] = {schularbeiten:{}, wiederholungen:{}, praesentationen:{}, hausaufgaben:{}, zwischenpruefung: null, muendlicheMitarbeit: {note: null, kommentar: ''}};
```

**Step 3: Add migration block after the `zwischenpruefung` migration (after line 1101)**

After the block:
```js
        // ── Ensure zwischenpruefung field exists on all studentData entries ──
        for (const semKey of ['semester1', 'semester2']) {
            const sem = cls[semKey];
            if (!sem) continue;
            for (const sid of Object.keys(sem.studentData || {})) {
                if (sem.studentData[sid].zwischenpruefung === undefined)
                    sem.studentData[sid].zwischenpruefung = null;
            }
        }
```

Add immediately after:
```js
        // ── Ensure muendlicheMitarbeit exists on all studentData entries ──
        for (const semKey of ['semester1', 'semester2']) {
            const sem = cls[semKey];
            if (!sem) continue;
            if (sem.gewichtung && sem.gewichtung.muendlich === undefined)
                sem.gewichtung.muendlich = 0;
            for (const sid of Object.keys(sem.studentData || {})) {
                if (!sem.studentData[sid].muendlicheMitarbeit)
                    sem.studentData[sid].muendlicheMitarbeit = {note: null, kommentar: ''};
            }
        }
```

**Step 4: Verify by loading the app — no console errors, existing data unchanged**

Run: `python server.py` then open `http://localhost:5000` in browser. Check browser console for errors.

**Step 5: Commit**
```bash
git add index.html
git commit -m "feat: add muendlicheMitarbeit data model + migration"
```

---

### Task 2: Calculation function

**Files:**
- Modify: `index.html:1241-1262` (`calcGesamtnote`)

**Step 1: Add `calcMMTeilnote()` after `calcHATeilnote` (around line 1217, before `calcSATeilnote`)**

Insert the new function before `calcSATeilnote`:
```js
// Teilnote Mündliche Mitarbeit (direkt eingegebene Note 1–5)
function calcMMTeilnote(sem, sid) {
    const sd = sem.studentData?.[sid] || {};
    const n = sd.muendlicheMitarbeit?.note;
    if (n === null || n === undefined || n === '') return null;
    const v = +n;
    return (v >= 1 && v <= 5) ? v : null;
}
```

**Step 2: Add muendlich component to `calcGesamtnote()` (line 1253)**

Change the `components` array:
```js
    const components = [
        {val: saTeilnote, w: saWeight},
        {val: wdhNote,   w: +(g.wiederholung  || 0)},
        {val: praesNote, w: +(g.praesentation || 0)},
        {val: haNote,    w: +(g.hausaufgaben  || 0)},
    ];
```
To:
```js
    const mmNote = calcMMTeilnote(sem, s.id);
    const components = [
        {val: saTeilnote, w: saWeight},
        {val: wdhNote,   w: +(g.wiederholung  || 0)},
        {val: praesNote, w: +(g.praesentation || 0)},
        {val: haNote,    w: +(g.hausaufgaben  || 0)},
        {val: mmNote,    w: +(g.muendlich     || 0)},
    ];
```

**Step 3: Commit**
```bash
git add index.html
git commit -m "feat: add calcMMTeilnote + muendlich weight to calcGesamtnote"
```

---

### Task 3: Update functions for saving MM data

**Files:**
- Modify: `index.html` — add new functions after `updateZwischenpruefung` (around line 1696)

**Step 1: Add `updateMMNote()` and `updateMMKommentar()` after `updateZwischenpruefung()`**

Insert after the closing `}` of `updateZwischenpruefung` (after line ~1696):
```js
function updateMMNote(sid, val) {
    const cls = activeClasses().find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    snapshotForUndo();
    sd.muendlicheMitarbeit.note = val === '' ? null : +val;
    if ((+val === 1 || +val === 5) && window.pixelguyNoteHint) window.pixelguyNoteHint(+val);
    saveDataWithUndo();
}

function updateMMKommentar(sid, val) {
    const cls = activeClasses().find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    snapshotForUndo();
    sd.muendlicheMitarbeit.kommentar = val;
    saveDataWithUndo();
}
```

**Step 2: Commit**
```bash
git add index.html
git commit -m "feat: add updateMMNote + updateMMKommentar"
```

---

### Task 4: Render the MM tab

**Files:**
- Modify: `index.html` — add `renderTabMM()` and `attachMMListeners()` after `attachHAListeners` (around line 2265)

**Step 1: Add `renderTabMM()` and `attachMMListeners()` after the HA section (after `setAllHA`/`updateHACells`, around line 2285)**

Insert before the `// ================================================================` comment of the Gesamtnote section (around line 2305):
```js
// ================================================================
// RENDER – Tab Mündliche Mitarbeit
// ================================================================
function renderTabMM(cls, sem) {
    if (!cls.students.length) return emptyStudents();
    return `
        <div class="table-wrapper">
            <table class="grade-table table table-bordered table-sm mb-0">
                <thead>
                    <tr>
                        <th class="sticky-col" style="min-width:180px;">Name</th>
                        <th class="text-center th-sa1">Note<br><span style="opacity:.7">1–5</span></th>
                        <th class="th-sa1">Kommentar</th>
                    </tr>
                </thead>
                <tbody id="mm-tbody">
                    ${cls.students.map(s => {
                        const mm = getSData(sem, s.id).muendlicheMitarbeit || {note: null, kommentar: ''};
                        const note = mm.note ?? '';
                        return `<tr data-sid="${s.id}">
                            <td class="sticky-col">${studentNameCell(s)}</td>
                            <td class="td-sa1 text-center">
                                <select class="cell-input mm-note-sel" data-sid="${s.id}">
                                    <option value="">—</option>
                                    ${[1,2,3,4,5].map(n => `<option value="${n}" ${note==n?'selected':''}>${n}</option>`).join('')}
                                </select>
                            </td>
                            <td class="td-sa1"><textarea class="komm-input mm-komm-ta" data-sid="${s.id}" placeholder="Kommentar...">${esc(mm.kommentar||'')}</textarea></td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>`;
}

function attachMMListeners() {
    document.querySelectorAll('.mm-note-sel').forEach(sel => {
        sel.addEventListener('change', function() { updateMMNote(this.dataset.sid, this.value); });
    });
    document.querySelectorAll('.mm-komm-ta').forEach(ta => {
        ta.addEventListener('change', function() { updateMMKommentar(this.dataset.sid, this.value); });
    });
}
```

**Step 2: Commit**
```bash
git add index.html
git commit -m "feat: add renderTabMM + attachMMListeners"
```

---

### Task 5: Wire up tab navigation

**Files:**
- Modify: `index.html:1779-1785` (tab bar in `renderContent`)
- Modify: `index.html:1819-1827` (`renderTabContent` switch)

**Step 1: Add 'mm' tab link in `renderContent()` tab bar (line 1783-1784)**

Change:
```js
            <li class="nav-item"><a class="nav-link ${activeTab==='ha'?'active':''}" href="#" onclick="selectTab('ha');return false;"><i class="bi bi-house me-1"></i>Hausübungen</a></li>
            <li class="nav-item"><a class="nav-link ${activeTab==='gesamt'?'active':''}" href="#" onclick="selectTab('gesamt');return false;"><i class="bi bi-calculator me-1"></i>Gesamtnote</a></li>
```
To:
```js
            <li class="nav-item"><a class="nav-link ${activeTab==='ha'?'active':''}" href="#" onclick="selectTab('ha');return false;"><i class="bi bi-house me-1"></i>Hausübungen</a></li>
            <li class="nav-item"><a class="nav-link ${activeTab==='mm'?'active':''}" href="#" onclick="selectTab('mm');return false;"><i class="bi bi-chat-dots me-1"></i>Mündl. Mitarbeit</a></li>
            <li class="nav-item"><a class="nav-link ${activeTab==='gesamt'?'active':''}" href="#" onclick="selectTab('gesamt');return false;"><i class="bi bi-calculator me-1"></i>Gesamtnote</a></li>
```

**Step 2: Add 'mm' case to `renderTabContent()` switch (line 1824)**

Change:
```js
        case 'gesamt':   area.innerHTML = renderTabGesamt(cls, sem);    attachGesamtListeners();   break;
```
To:
```js
        case 'mm':       area.innerHTML = renderTabMM(cls, sem);        attachMMListeners();       break;
        case 'gesamt':   area.innerHTML = renderTabGesamt(cls, sem);    attachGesamtListeners();   break;
```

**Step 3: Test in browser — click "Mündl. Mitarbeit" tab, enter a note and kommentar, reload page to verify persistence**

**Step 4: Commit**
```bash
git add index.html
git commit -m "feat: wire up Mündliche Mitarbeit tab navigation"
```

---

### Task 6: Gesamtnote tab — add weight input + column

**Files:**
- Modify: `index.html:2312` (`totalW` in `renderTabGesamt`)
- Modify: `index.html:2326-2327` (weight inputs)
- Modify: `index.html:2340-2341` (table header columns)
- Modify: `index.html:2352-2393` (table body row rendering)
- Modify: `index.html:2607-2616` (`updateWeightSum`)

**Step 1: Update `totalW` to include `muendlich` (line 2312)**

Change:
```js
    const totalW =saWeight+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```
To:
```js
    const totalW =saWeight+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0)+(+(g.muendlich)||0);
```

**Step 2: Add `muendlich` weight input (line 2326)**

Change:
```js
                ${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
```
To:
```js
                ${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
                ${weightInput('muendlich','Mündl. Mitarbeit', g.muendlich)}
```

**Step 3: Add "Mündl." column header in table (after HÜ column, before Wunschpr., line 2340-2341)**

Change:
```js
                        <th class="text-center th-ha">HÜ<br><small>${g.hausaufgaben||0} %</small></th>
                        <th class="text-center th-zp">Wunschpr.</th>
```
To:
```js
                        <th class="text-center th-ha">HÜ<br><small>${g.hausaufgaben||0} %</small></th>
                        <th class="text-center th-praes">Mündl.<br><small>${g.muendlich||0} %</small></th>
                        <th class="text-center th-zp">Wunschpr.</th>
```

**Step 4: Add "Mündl." value cell in table body rows (after HA cell, before Wunschpr. cell)**

In the row rendering section, add `calcMMTeilnote` to the existing variable declarations (after line 2352):
```js
                        const ha  = calcHATeilnote(sem, s.id);
```
Add after:
```js
                        const mm  = calcMMTeilnote(sem, s.id);
```

Then add the cell after the HÜ cell (after line 2392):
```js
                            <td class="td-ha text-center">${ha !== null ? `<span class="note-badge note-${ha}" id="gsha-${s.id}">${fmtNote2(ha)}</span>` : `<span class="note-badge note-empty" id="gsha-${s.id}">—</span>`}</td>
```
Add after:
```js
                            <td class="td-praes text-center">${mm !== null ? `<span class="note-badge note-${mm}" id="gsmm-${s.id}">${mm}</span>` : `<span class="note-badge note-empty" id="gsmm-${s.id}">—</span>`}</td>
```

**Step 5: Update `updateWeightSum()` to include `muendlich` (line 2611)**

Change:
```js
    const total = (+(g.schularbeiten)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```
To:
```js
    const total = (+(g.schularbeiten)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0)+(+(g.muendlich)||0);
```

**Step 6: Test in browser**
- Go to Gesamtnote tab → verify new "Mündl. Mitarbeit" weight input appears
- Set weight to e.g. 20, enter a MM note in the MM tab → verify Gesamtnote updates
- Verify weight-sum warning works (e.g. all weights sum to 100 → green checkmark)

**Step 7: Commit**
```bash
git add index.html
git commit -m "feat: add Mündl. Mitarbeit weight + column to Gesamtnote tab"
```

---

### Task 7: Final smoke test

**Step 1: Full test checklist**
1. Open `http://localhost:5000`
2. Select a class (Unterstufe and Oberstufe)
3. Both semesters: click "Mündl. Mitarbeit" tab → table appears with all students
4. Enter Note 1–5 and Kommentar for a student → reload → data persists
5. Go to Gesamtnote tab → "Mündl. Mitarbeit" weight input visible, set to >0
6. Verify the student's Gesamtnote changes after entering a MM note
7. Verify weight-sum warning updates correctly
8. Check browser console: no JS errors
9. Export data as JSON → verify `muendlicheMitarbeit` field present in studentData
10. Import the exported JSON → no errors, all MM data intact

**Step 2: Commit if any fixes were needed**
```bash
git add index.html
git commit -m "fix: <describe what was fixed>"
```
