# Semester Support — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add two independent semesters per class; all grade logic applies per semester; Semester 2 Gesamtnote includes a configurable weight for the Semester 1 overall grade.

**Architecture:** Semester data is nested inside the class object as `cls.semester1` and `cls.semester2`, each with its own `schularbeiten`, `wiederholungen`, `praesentationen`, `hausaufgaben`, `gewichtung`, and `studentData`. Students at class level hold identity only (`{id, name}`). A new global `activeSemester` controls which semester is shown. Semester tabs appear above the existing content tabs.

**Tech Stack:** Vanilla JS, Bootstrap 5 CSS, single `index.html` file

---

### Task 1: Data model — `newClass`, `newStudent`, `activeSemester` global

**Files:**
- Modify: `index.html`

**Step 1: Add `activeSemester` global after `activeSaId` (line 660)**

Find:
```js
let activeSaId = null;
```
Replace with:
```js
let activeSaId = null;
let activeSemester = 'semester1'; // 'semester1' | 'semester2'
```

**Step 2: Rewrite `newClass()` (line 912)**

Find:
```js
function newClass(name) {
    const saId = genId();
    return {
        id: genId(), name: name.trim(), students: [],
        schularbeiten: [{id: saId, name: '1. Schularbeit'}],
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20}
    };
}
```
Replace with:
```js
function newClass(name) {
    const saId1 = genId(), saId2 = genId();
    const semBase = (saId) => ({
        schularbeiten: [{id: saId, name: '1. Schularbeit'}],
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20},
        studentData: {}
    });
    const sem2 = semBase(saId2);
    sem2.gewichtung.semester1Note = 0;
    return {
        id: genId(), name: name.trim(), students: [],
        semester1: semBase(saId1),
        semester2: sem2
    };
}
```

**Step 3: Rewrite `newStudent()` (line 972)**

Find:
```js
function newStudent(name) {
    return {
        id: genId(), name: name.trim(),
        schularbeiten: {},
        wiederholungen: {}, praesentationen: {}, hausaufgaben: {}
    };
}
```
Replace with:
```js
function newStudent(name) {
    return { id: genId(), name: name.trim() };
}
```

**Step 4: Add helper `getSData` after `newStudent`**

Add this new function right after `newStudent`:
```js
function getSData(sem, sid) {
    if (!sem.studentData[sid]) sem.studentData[sid] = {schularbeiten:{}, wiederholungen:{}, praesentationen:{}, hausaufgaben:{}};
    return sem.studentData[sid];
}
```

**Step 5: Verify**
Open browser console on `http://localhost:5000`, run:
```js
const c = newClass('Test'); console.log(JSON.stringify(c, null, 2));
```
Expected: class with `semester1` and `semester2` objects, each with `schularbeiten`, `gewichtung`, `studentData:{}`. `semester2.gewichtung.semester1Note` should be `0`.

---

### Task 2: Migration — `migrateData()`

**Files:**
- Modify: `index.html`

**Step 1: Replace `migrateData()` entirely**

Find the entire `migrateData()` function (starts at line 682) and replace it:

```js
function migrateData() {
    for (const cls of data.classes) {

        // ── Migrate flat structure → semester1 ──────────────────────
        if (!cls.semester1) {
            const saId = genId();
            cls.semester1 = {
                schularbeiten: cls.schularbeiten || [{id: saId, name: '1. Schularbeit'}],
                wiederholungen:  cls.wiederholungen  || [],
                praesentationen: cls.praesentationen || [],
                hausaufgaben:    cls.hausaufgaben    || [],
                gewichtung:      cls.gewichtung      || {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20},
                studentData: {}
            };

            // Migrate old sa1/sa2 weights → schularbeiten on semester1
            const g1 = cls.semester1.gewichtung;
            if (g1.sa1 !== undefined || g1.sa2 !== undefined) {
                g1.schularbeiten = (+(g1.sa1)||0) + (+(g1.sa2)||0);
                delete g1.sa1; delete g1.sa2;
            }
            if (g1.schularbeiten === undefined) g1.schularbeiten = 40;

            // Migrate old schularbeiten array: legacy sa1/sa2 → migration IDs
            if (!cls.schularbeiten) {
                // already handled above
            } else {
                // already copied into semester1.schularbeiten
            }

            // Migrate student grade data → semester1.studentData
            for (const s of (cls.students || [])) {
                const sd = { schularbeiten:{}, wiederholungen:{}, praesentationen:{}, hausaufgaben:{} };

                // Migrate old fixed schularbeit1/2
                if (s.schularbeit1 !== undefined) {
                    sd.schularbeiten['sa1-legacy'] = {
                        aufgabenstellung: s.schularbeit1?.aufgabenstellung ?? null,
                        fehler:           s.schularbeit1?.fehler           ?? null,
                        wortschatz:       s.schularbeit1?.wortschatz       ?? null,
                        textorganisation: s.schularbeit1?.textorganisation ?? null,
                        kommentar:        s.kommentar1 ?? ''
                    };
                    delete s.schularbeit1;
                }
                if (s.schularbeit2 !== undefined) {
                    sd.schularbeiten['sa2-legacy'] = {
                        aufgabenstellung: s.schularbeit2?.aufgabenstellung ?? null,
                        fehler:           s.schularbeit2?.fehler           ?? null,
                        wortschatz:       s.schularbeit2?.wortschatz       ?? null,
                        textorganisation: s.schularbeit2?.textorganisation ?? null,
                        kommentar:        s.kommentar2 ?? ''
                    };
                    delete s.schularbeit2;
                }
                delete s.kommentar1; delete s.kommentar2;

                // Migrate already-migrated dynamic fields
                if (s.schularbeiten)   sd.schularbeiten   = s.schularbeiten;
                if (s.wiederholungen)  sd.wiederholungen  = s.wiederholungen;
                if (s.praesentationen) sd.praesentationen = s.praesentationen;
                if (s.hausaufgaben)    sd.hausaufgaben    = s.hausaufgaben;
                delete s.schularbeiten; delete s.wiederholungen;
                delete s.praesentationen; delete s.hausaufgaben;

                cls.semester1.studentData[s.id] = sd;
            }

            // Delete flat fields from class
            delete cls.schularbeiten; delete cls.wiederholungen;
            delete cls.praesentationen; delete cls.hausaufgaben; delete cls.gewichtung;
        }

        // ── Ensure semester2 exists ──────────────────────────────────
        if (!cls.semester2) {
            const saId = genId();
            cls.semester2 = {
                schularbeiten: [{id: saId, name: '1. Schularbeit'}],
                wiederholungen: [], praesentationen: [], hausaufgaben: [],
                gewichtung: {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20, semester1Note:0},
                studentData: {}
            };
        }
        if (cls.semester2.gewichtung.semester1Note === undefined) {
            cls.semester2.gewichtung.semester1Note = 0;
        }

        // ── Ensure students list exists ──────────────────────────────
        if (!cls.students) cls.students = [];
    }
}
```

**Step 2: Verify migration**

Stop/restart server. Reload `http://localhost:5000`. In console:
```js
const cls = data.classes[0];
console.log(Object.keys(cls));
// expected: ['id','name','students','semester1','semester2']
console.log(cls.semester1.schularbeiten);
// expected: array of SA objects
console.log(cls.semester1.studentData);
// expected: object with student IDs as keys
console.log(cls.semester2.gewichtung.semester1Note);
// expected: 0
```

---

### Task 3: Semester tab bar UI — `renderContent`, `selectSemester`, `selectClass`

**Files:**
- Modify: `index.html`

**Step 1: Add CSS for semester tabs after the `.sa-tab-add:hover` rule**

Find:
```css
            .sa-tab-add:hover { background: rgba(74,222,128,0.08); }
```
Add after it:
```css

            /* ── Semester tabs ───────────────────────────────── */
            .semester-tab-bar {
                display: flex; gap: 4px; margin-bottom: 1rem;
            }
            .semester-tab {
                padding: 6px 18px; border-radius: 8px 8px 0 0;
                border: 1px solid rgba(255,255,255,0.08); border-bottom: none;
                background: rgba(255,255,255,0.04); color: #6b7a90;
                cursor: pointer; font-size: .85rem;
                transition: background 0.12s, color 0.12s;
            }
            .semester-tab:hover { background: rgba(255,255,255,0.08); color: #c0c8db; }
            .semester-tab.active { background: rgba(20,184,166,0.14); border-color: rgba(20,184,166,0.35); color: #5ee8da; font-weight:600; }
```

**Step 2: Add `selectSemester` function after `selectTab`**

Find:
```js
function selectTab(tab)  { activeTab=tab; renderTabContent(); updateTabLinks(); }
```
Add after it:
```js
function selectSemester(sem) {
    activeSemester = sem;
    const cls = data.classes.find(c=>c.id===activeClassId);
    activeSaId = cls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
    activeTab = 'sa';
    renderContent();
}
```

**Step 3: Update `renderContent` to add semester tab bar**

Find in `renderContent`:
```js
        <ul class="nav class-tabs" id="class-tabs">
```
Add the semester tab bar immediately before it:
```js
        <div class="semester-tab-bar">
            <div class="semester-tab ${activeSemester==='semester1'?'active':''}" onclick="selectSemester('semester1')">1. Semester</div>
            <div class="semester-tab ${activeSemester==='semester2'?'active':''}" onclick="selectSemester('semester2')">2. Semester</div>
        </div>
        <ul class="nav class-tabs" id="class-tabs">
```

**Step 4: Update `selectClass` to initialize `activeSemester` SA**

Find:
```js
function selectClass(id) {
    activeClassId=id;
    const _selCls = data.classes.find(c=>c.id===id);
    activeSaId = _selCls?.schularbeiten?.[0]?.id ?? null;
    activeTab='sa'; renderSidebar(); renderContent();
}
```
Replace with:
```js
function selectClass(id) {
    activeClassId=id;
    const _selCls = data.classes.find(c=>c.id===id);
    activeSaId = _selCls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
    activeTab='sa'; renderSidebar(); renderContent();
}
```

**Step 5: Update `addClass` to set `activeSaId` correctly**

Find:
```js
function addClass(name)          { const c=newClass(name); data.classes.push(c); activeClassId=c.id; activeSaId=c.schularbeiten[0].id; saveData(); render(); }
```
Replace with:
```js
function addClass(name) {
    const c=newClass(name); data.classes.push(c);
    activeClassId=c.id; activeSemester='semester1';
    activeSaId=c.semester1.schularbeiten[0].id;
    saveData(); render();
}
```

**Step 6: Update DOMContentLoaded init**

Find:
```js
    activeClassId = data.classes[0]?.id ?? null;
    const _initCls = data.classes[0];
    activeSaId = _initCls?.schularbeiten?.[0]?.id ?? null;
```
Replace with:
```js
    activeClassId = data.classes[0]?.id ?? null;
    const _initCls = data.classes[0];
    activeSaId = _initCls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
```

**Step 7: Update `renderTabContent` to pass `sem`**

Find:
```js
function renderTabContent() {
    const area = document.getElementById('tab-content');
    if (!area) return;
    const cls = data.classes.find(c=>c.id===activeClassId);
    if (!cls) return;
    switch(activeTab) {
        case 'sa':     area.innerHTML = renderTabSA(cls);     attachSAListeners();    break;
        case 'wdh':    area.innerHTML = renderTabWDH(cls);    attachWDHListeners();   break;
        case 'praes':  area.innerHTML = renderTabPraes(cls);  attachPraesListeners(); break;
        case 'ha':     area.innerHTML = renderTabHA(cls);     attachHAListeners();    break;
        case 'gesamt': area.innerHTML = renderTabGesamt(cls); attachGesamtListeners(); break;
    }
}
```
Replace with:
```js
function renderTabContent() {
    const area = document.getElementById('tab-content');
    if (!area) return;
    const cls = data.classes.find(c=>c.id===activeClassId);
    if (!cls) return;
    const sem = cls[activeSemester];
    switch(activeTab) {
        case 'sa':     area.innerHTML = renderTabSA(cls, sem);     attachSAListeners();    break;
        case 'wdh':    area.innerHTML = renderTabWDH(cls, sem);    attachWDHListeners();   break;
        case 'praes':  area.innerHTML = renderTabPraes(cls, sem);  attachPraesListeners(); break;
        case 'ha':     area.innerHTML = renderTabHA(cls, sem);     attachHAListeners();    break;
        case 'gesamt': area.innerHTML = renderTabGesamt(cls, sem); attachGesamtListeners(); break;
    }
}
```

**Step 8: Verify in browser**

Reload. Two tabs "1. Semester" / "2. Semester" should appear at top. Clicking them switches (content may look broken — that's OK, render functions not yet updated).

---

### Task 4: SA management — adapt to semester

**Files:**
- Modify: `index.html`

**Step 1: Update `addSA`**

Find:
```js
function addSA() {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const n = cls.schularbeiten.length + 1;
    const sa = {id: genId(), name: n + '. Schularbeit'};
    cls.schularbeiten.push(sa);
    activeSaId = sa.id;
    saveData(); renderTabContent();
}
```
Replace with:
```js
function addSA() {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const n = sem.schularbeiten.length + 1;
    const sa = {id: genId(), name: n + '. Schularbeit'};
    sem.schularbeiten.push(sa);
    activeSaId = sa.id;
    saveData(); renderTabContent();
}
```

**Step 2: Update `deleteSA`**

Find:
```js
function deleteSA(saId) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    if (cls.schularbeiten.length <= 1) return; // minimum 1
    cls.schularbeiten = cls.schularbeiten.filter(sa=>sa.id!==saId);
    for (const s of cls.students) delete s.schularbeiten[saId];
    if (activeSaId === saId) activeSaId = cls.schularbeiten[0].id;
    saveData(); renderTabContent();
}
```
Replace with:
```js
function deleteSA(saId) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    if (sem.schularbeiten.length <= 1) return; // minimum 1
    sem.schularbeiten = sem.schularbeiten.filter(sa=>sa.id!==saId);
    for (const sd of Object.values(sem.studentData)) delete sd.schularbeiten[saId];
    if (activeSaId === saId) activeSaId = sem.schularbeiten[0].id;
    saveData(); renderTabContent();
}
```

**Step 3: Update `updateSAField`**

Find:
```js
function updateSAField(sid, saId, field, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        if (!s.schularbeiten[saId]) s.schularbeiten[saId] = {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
        const n = val==='' ? null : parseInt(val,10);
        s.schularbeiten[saId][field] = (val===''||isNaN(n)) ? null : n;
        saveData(); updateSACells(cls, s, saId); return;
    }
}
```
Replace with:
```js
function updateSAField(sid, saId, field, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    if (!sd.schularbeiten[saId]) sd.schularbeiten[saId] = {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
    const n = val==='' ? null : parseInt(val,10);
    sd.schularbeiten[saId][field] = (val===''||isNaN(n)) ? null : n;
    saveData();
    const s = cls.students.find(s=>s.id===sid);
    if (s) updateSACells(sem, s, saId);
}
```

**Step 4: Update `updateKommentar`**

Find:
```js
function updateKommentar(sid, saId, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        if (!s.schularbeiten[saId]) s.schularbeiten[saId] = {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
        s.schularbeiten[saId].kommentar = val;
        saveData(); return;
    }
}
```
Replace with:
```js
function updateKommentar(sid, saId, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    if (!sd.schularbeiten[saId]) sd.schularbeiten[saId] = {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
    sd.schularbeiten[saId].kommentar = val;
    saveData();
}
```

**Step 5: Update `renderTabSA` signature and internals**

Find:
```js
function renderTabSA(cls) {
    const sas = cls.schularbeiten || [];
    if (!activeSaId || !sas.find(sa=>sa.id===activeSaId)) {
        activeSaId = sas[0]?.id ?? null;
    }
```
Replace with:
```js
function renderTabSA(cls, sem) {
    const sas = sem.schularbeiten || [];
    if (!activeSaId || !sas.find(sa=>sa.id===activeSaId)) {
        activeSaId = sas[0]?.id ?? null;
    }
```

Then find inside `renderTabSA`:
```js
                    ${cls.students.map(s => renderSARow(s, activeSaId)).join('')}
```
Replace with:
```js
                    ${cls.students.map(s => renderSARow(getSData(sem, s.id), s, activeSaId)).join('')}
```

**Step 6: Update `renderSARow` signature**

Find:
```js
function renderSARow(s, saId) {
    const sa = s.schularbeiten?.[saId] || {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
```
Replace with:
```js
function renderSARow(sd, s, saId) {
    const sa = sd.schularbeiten?.[saId] || {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
```

**Step 7: Update `updateSACells`**

Find:
```js
function updateSACells(cls, s, saId) {
    const sa = s.schularbeiten?.[saId] || {};
```
Replace with:
```js
function updateSACells(sem, s, saId) {
    const sd = getSData(sem, s.id);
    const sa = sd.schularbeiten?.[saId] || {};
```

**Step 8: Update `hasPositiveSA`**

Find:
```js
function hasPositiveSA(cls, s) {
    const sas = cls.schularbeiten || [];
    if (sas.length === 0) return true;
    return sas.some(sa => {
        const saData = s.schularbeiten?.[sa.id];
```
Replace with:
```js
function hasPositiveSA(sem, s) {
    const sas = sem.schularbeiten || [];
    if (sas.length === 0) return true;
    const sd = sem.studentData?.[s.id] || {};
    return sas.some(sa => {
        const saData = sd.schularbeiten?.[sa.id];
```

---

### Task 5: WDH management — adapt to semester

**Files:**
- Modify: `index.html`

**Step 1: Update `addWdh`, `editWdh`, `deleteWdh`**

Find:
```js
function addWdh(name, maxPunkte) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.wiederholungen.push({id:genId(), name:name.trim(), maxPunkte:+maxPunkte});
    saveData(); renderTabContent();
}
function editWdh(wid, name, maxPunkte) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const w = cls.wiederholungen.find(w=>w.id===wid); if(!w) return;
    w.name=name.trim(); w.maxPunkte=+maxPunkte; saveData(); renderTabContent();
}
function deleteWdh(wid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.wiederholungen = cls.wiederholungen.filter(w=>w.id!==wid);
    for (const s of cls.students) delete s.wiederholungen[wid];
    saveData(); renderTabContent();
```
Replace with:
```js
function addWdh(name, maxPunkte) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls[activeSemester].wiederholungen.push({id:genId(), name:name.trim(), maxPunkte:+maxPunkte});
    saveData(); renderTabContent();
}
function editWdh(wid, name, maxPunkte) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const w = cls[activeSemester].wiederholungen.find(w=>w.id===wid); if(!w) return;
    w.name=name.trim(); w.maxPunkte=+maxPunkte; saveData(); renderTabContent();
}
function deleteWdh(wid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    sem.wiederholungen = sem.wiederholungen.filter(w=>w.id!==wid);
    for (const sd of Object.values(sem.studentData)) delete sd.wiederholungen[wid];
    saveData(); renderTabContent();
```

**Step 2: Update `updateWdhField`**

Find:
```js
function updateWdhField(sid, wid, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        const n = val==='' ? null : parseFloat(val);
        s.wiederholungen[wid] = (val===''||isNaN(n)) ? null : n;
        saveData();
        const tn = calcWdhTeilnote(cls, sid);
        setBadgeDec('wdh-note-' + sid, tn);
        return;
    }
}
```
Replace with:
```js
function updateWdhField(sid, wid, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    const n = val==='' ? null : parseFloat(val);
    sd.wiederholungen[wid] = (val===''||isNaN(n)) ? null : n;
    saveData();
    const tn = calcWdhTeilnote(sem, sid);
    setBadgeDec('wdh-note-' + sid, tn);
}
```

**Step 3: Update `calcWdhTeilnote`**

Find:
```js
function calcWdhTeilnote(cls, sid) {
    const s = cls.students.find(s => s.id === sid);
    const wdhs = cls.wiederholungen || [];
    if (!s || wdhs.length === 0) return null;
    const notes = [];
    for (const w of wdhs) {
        const val = s.wiederholungen?.[w.id];
```
Replace with:
```js
function calcWdhTeilnote(sem, sid) {
    const sd = sem.studentData?.[sid] || {};
    const wdhs = sem.wiederholungen || [];
    if (wdhs.length === 0) return null;
    const notes = [];
    for (const w of wdhs) {
        const val = sd.wiederholungen?.[w.id];
```

**Step 4: Update `renderTabWDH` signature**

Find:
```js
function renderTabWDH(cls) {
```
Replace with:
```js
function renderTabWDH(cls, sem) {
```

Then inside `renderTabWDH`, replace all references:
- `cls.wiederholungen` → `sem.wiederholungen`
- `cls.students` stays as-is (identity)
- Any `s.wiederholungen` references → `(sem.studentData?.[s.id]||{}).wiederholungen`
- Any `calcWdhTeilnote(cls, sid)` → `calcWdhTeilnote(sem, sid)`

**Important:** Read `renderTabWDH` carefully before editing. The key pattern to replace is wherever it reads student grade data (`s.wiederholungen?.[w.id]`) — replace with `getSData(sem, s.id).wiederholungen?.[w.id]`.

---

### Task 6: Präsentation management — adapt to semester

**Files:**
- Modify: `index.html`

**Step 1: Update `addPraes`, `editPraes`, `deletePraes`**

Find:
```js
function addPraes(name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.praesentationen.push({id:genId(), name:name.trim()}); saveData(); renderTabContent();
}
function editPraes(pid, name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const p = cls.praesentationen.find(p=>p.id===pid); if(!p) return;
    p.name=name.trim(); saveData(); renderTabContent();
}
function deletePraes(pid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.praesentationen = cls.praesentationen.filter(p=>p.id!==pid);
    for (const s of cls.students) delete s.praesentationen[pid];
    saveData(); renderTabContent();
}
```
Replace with:
```js
function addPraes(name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls[activeSemester].praesentationen.push({id:genId(), name:name.trim()}); saveData(); renderTabContent();
}
function editPraes(pid, name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const p = cls[activeSemester].praesentationen.find(p=>p.id===pid); if(!p) return;
    p.name=name.trim(); saveData(); renderTabContent();
}
function deletePraes(pid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    sem.praesentationen = sem.praesentationen.filter(p=>p.id!==pid);
    for (const sd of Object.values(sem.studentData)) delete sd.praesentationen[pid];
    saveData(); renderTabContent();
}
```

**Step 2: Update `updatePraesField`**

Find:
```js
function updatePraesField(sid, pid, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        const n = val==='' ? null : parseInt(val,10);
        s.praesentationen[pid] = (val===''||isNaN(n)) ? null : n;
        saveData();
        const tn = calcPraesTeilnote(cls, sid);
        setBadgeDec('praes-note-' + sid, tn);
        return;
    }
}
```
Replace with:
```js
function updatePraesField(sid, pid, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    const n = val==='' ? null : parseInt(val,10);
    sd.praesentationen[pid] = (val===''||isNaN(n)) ? null : n;
    saveData();
    const tn = calcPraesTeilnote(sem, sid);
    setBadgeDec('praes-note-' + sid, tn);
}
```

**Step 3: Update `calcPraesTeilnote`**

Find:
```js
function calcPraesTeilnote(cls, sid) {
    const s = cls.students.find(s => s.id === sid);
    const praes = cls.praesentationen || [];
    if (!s || praes.length === 0) return null;
    const notes = [];
    for (const p of praes) {
        const val = s.praesentationen?.[p.id];
```
Replace with:
```js
function calcPraesTeilnote(sem, sid) {
    const sd = sem.studentData?.[sid] || {};
    const praes = sem.praesentationen || [];
    if (praes.length === 0) return null;
    const notes = [];
    for (const p of praes) {
        const val = sd.praesentationen?.[p.id];
```

**Step 4: Update `renderTabPraes` signature and internals**

Same pattern as WDH:
- Signature: `renderTabPraes(cls, sem)`
- `cls.praesentationen` → `sem.praesentationen`
- `s.praesentationen?.[p.id]` → `getSData(sem, s.id).praesentationen?.[p.id]`
- `calcPraesTeilnote(cls, sid)` → `calcPraesTeilnote(sem, sid)`

---

### Task 7: Hausübungen management — adapt to semester

**Files:**
- Modify: `index.html`

**Step 1: Update `addHA`, `editHA`, `deleteHA`**

Find:
```js
function addHA(name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.hausaufgaben.push({id:genId(), name:name.trim()}); saveData(); renderTabContent();
}
function editHA(hid, name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const h = cls.hausaufgaben.find(h=>h.id===hid); if(!h) return;
    h.name=name.trim(); saveData(); renderTabContent();
}
function deleteHA(hid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.hausaufgaben = cls.hausaufgaben.filter(h=>h.id!==hid);
    for (const s of cls.students) delete s.hausaufgaben[hid];
    saveData(); renderTabContent();
}
```
Replace with:
```js
function addHA(name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls[activeSemester].hausaufgaben.push({id:genId(), name:name.trim()}); saveData(); renderTabContent();
}
function editHA(hid, name) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const h = cls[activeSemester].hausaufgaben.find(h=>h.id===hid); if(!h) return;
    h.name=name.trim(); saveData(); renderTabContent();
}
function deleteHA(hid) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    sem.hausaufgaben = sem.hausaufgaben.filter(h=>h.id!==hid);
    for (const sd of Object.values(sem.studentData)) delete sd.hausaufgaben[hid];
    saveData(); renderTabContent();
}
```

**Step 2: Update `updateHAField` and `setAllHA`**

Find:
```js
function updateHAField(sid, hid, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        s.hausaufgaben[hid] = val==='' ? null : val;
        saveData();
        updateHACells(cls, s);
        return;
    }
}
```
Replace with:
```js
function updateHAField(sid, hid, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    const sd = getSData(sem, sid);
    sd.hausaufgaben[hid] = val==='' ? null : val;
    saveData();
    const s = cls.students.find(s=>s.id===sid);
    if (s) updateHACells(sem, s);
}
```

Find:
```js
function setAllHA(hid, val) {
    const cls = data.classes.find(c => c.id === activeClassId);
    if (!cls) return;
    for (const s of cls.students) {
        s.hausaufgaben[hid] = val === '' ? null : val;
    }
    saveData();
    renderTabContent();
}
```
Replace with:
```js
function setAllHA(hid, val) {
    const cls = data.classes.find(c => c.id === activeClassId); if(!cls) return;
    const sem = cls[activeSemester];
    for (const s of cls.students) {
        getSData(sem, s.id).hausaufgaben[hid] = val === '' ? null : val;
    }
    saveData();
    renderTabContent();
}
```

**Step 3: Update `calcHATeilnote`**

Find:
```js
function calcHATeilnote(cls, sid) {
    const s = cls.students.find(s => s.id === sid);
    const has = cls.hausaufgaben || [];
    if (!s || has.length === 0) return null;
    let achieved = 0, possible = 0;
    for (const h of has) {
        const val = s.hausaufgaben?.[h.id];
```
Replace with:
```js
function calcHATeilnote(sem, sid) {
    const sd = sem.studentData?.[sid] || {};
    const has = sem.hausaufgaben || [];
    if (has.length === 0) return null;
    let achieved = 0, possible = 0;
    for (const h of has) {
        const val = sd.hausaufgaben?.[h.id];
```

**Step 4: Update `haStats` and `updateHACells`**

Find:
```js
function haStats(cls, sid) {
    const s = cls.students.find(s=>s.id===sid);
    if (!s) return {achieved:null, possible:null};
    let achieved=0, possible=0;
    for (const h of cls.hausaufgaben) {
        const val = s.hausaufgaben?.[h.id];
```
Replace with:
```js
function haStats(sem, sid) {
    const sd = sem.studentData?.[sid] || {};
    let achieved=0, possible=0;
    for (const h of sem.hausaufgaben) {
        const val = sd.hausaufgaben?.[h.id];
```

Find:
```js
function updateHACells(cls, s) {
    const {achieved, possible} = haStats(cls, s.id);
```
Replace with:
```js
function updateHACells(sem, s) {
    const {achieved, possible} = haStats(sem, s.id);
```

**Step 5: Update `renderTabHA` signature and internals**

Same pattern:
- Signature: `renderTabHA(cls, sem)`
- `cls.hausaufgaben` → `sem.hausaufgaben`
- `s.hausaufgaben?.[h.id]` → `getSData(sem, s.id).hausaufgaben?.[h.id]`
- `calcHATeilnote(cls, sid)` → `calcHATeilnote(sem, sid)`
- `haStats(cls, sid)` → `haStats(sem, sid)`
- `updateHACells(cls, s)` → `updateHACells(sem, s)`

---

### Task 8: Gewichtung + Gesamtnote — adapt to semester + Sem2 extras

**Files:**
- Modify: `index.html`

**Step 1: Update `updateGewichtung`**

Find:
```js
function updateGewichtung(key, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls.gewichtung[key] = +val || 0;
    saveData();
    updateGesamtColumn(cls);
    updateWeightSum();
}
```
Replace with:
```js
function updateGewichtung(key, val) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    cls[activeSemester].gewichtung[key] = +val || 0;
    saveData();
    updateGesamtColumn(cls, cls[activeSemester]);
    updateWeightSum();
}
```

**Step 2: Update `calcGesamtnote` — add `sem` param + Semester 2 logic**

Find:
```js
function calcGesamtnote(cls, s) {
    const g = cls.gewichtung || {};
    const sas = cls.schularbeiten || [];
    const saWeight = +(g.schularbeiten || 0);
    const wdhNote   = calcWdhTeilnote(cls, s.id);
    const praesNote = calcPraesTeilnote(cls, s.id);
    const haNote    = calcHATeilnote(cls, s.id);

    const components = [
        {val: wdhNote,   w: +(g.wiederholung  || 0)},
        {val: praesNote, w: +(g.praesentation || 0)},
        {val: haNote,    w: +(g.hausaufgaben  || 0)},
    ];

    if (sas.length > 0 && saWeight > 0) {
        const wPerSA = saWeight / sas.length;
        for (const sa of sas) {
            const saData = s.schularbeiten?.[sa.id];
            const note = saData ? calcNote(calcGesamt(saData)) : null;
            components.push({val: note?.decimal ?? null, w: wPerSA});
        }
    }

    let sumW = 0, sumWN = 0;
    for (const c of components) {
        if (c.val !== null && c.w > 0) { sumWN += c.val * c.w; sumW += c.w; }
    }
    if (sumW === 0) return null;
    return sumWN / sumW;
}
```
Replace with:
```js
function calcGesamtnote(cls, sem, s) {
    const g = sem.gewichtung || {};
    const sas = sem.schularbeiten || [];
    const saWeight = +(g.schularbeiten || 0);
    const sd = sem.studentData?.[s.id] || {};
    const wdhNote   = calcWdhTeilnote(sem, s.id);
    const praesNote = calcPraesTeilnote(sem, s.id);
    const haNote    = calcHATeilnote(sem, s.id);

    const components = [
        {val: wdhNote,   w: +(g.wiederholung  || 0)},
        {val: praesNote, w: +(g.praesentation || 0)},
        {val: haNote,    w: +(g.hausaufgaben  || 0)},
    ];

    if (sas.length > 0 && saWeight > 0) {
        const wPerSA = saWeight / sas.length;
        for (const sa of sas) {
            const saData = sd.schularbeiten?.[sa.id];
            const note = saData ? calcNote(calcGesamt(saData)) : null;
            components.push({val: note?.decimal ?? null, w: wPerSA});
        }
    }

    // Semester 2: include Semester 1 Gesamtnote as extra component
    if (sem === cls.semester2 && +(g.semester1Note || 0) > 0) {
        const sem1Dec = calcGesamtnote(cls, cls.semester1, s);
        components.push({val: sem1Dec, w: +(g.semester1Note || 0)});
    }

    let sumW = 0, sumWN = 0;
    for (const c of components) {
        if (c.val !== null && c.w > 0) { sumWN += c.val * c.w; sumW += c.w; }
    }
    if (sumW === 0) return null;
    return sumWN / sumW;
}
```

**Step 3: Update `renderTabGesamt` — signature + Sem2 extras**

Find:
```js
function renderTabGesamt(cls) {
    const g = cls.gewichtung;
    const saWeight = +(g.schularbeiten || 0);
    const sas = cls.schularbeiten || [];
    const wPerSA = sas.length > 0 ? (saWeight / sas.length).toFixed(0) : 0;
    const totalW = saWeight+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```
Replace with:
```js
function renderTabGesamt(cls, sem) {
    const g = sem.gewichtung;
    const saWeight = +(g.schularbeiten || 0);
    const sas = sem.schularbeiten || [];
    const wPerSA = sas.length > 0 ? (saWeight / sas.length).toFixed(0) : 0;
    const isSem2 = sem === cls.semester2;
    const totalW = saWeight+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0)+(isSem2?(+(g.semester1Note)||0):0);
```

Then in the weight card inputs, find:
```js
                ${weightInput('schularbeiten', `Schularbeiten (${sas.length}× gleichwertig)`, g.schularbeiten)}
                ${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
                ${weightInput('praesentation','Präsentation',  g.praesentation)}
                ${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
```
Replace with:
```js
                ${weightInput('schularbeiten', `Schularbeiten (${sas.length}× gleichwertig)`, g.schularbeiten)}
                ${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
                ${weightInput('praesentation','Präsentation',  g.praesentation)}
                ${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
                ${isSem2 ? weightInput('semester1Note','1. Semester', g.semester1Note) : ''}
```

In the table header, find:
```js
                        ${sas.map(sa => `<th class="text-center th-sa1">${esc(sa.name)}<br><small>${wPerSA} %</small></th>`).join('')}
```
Replace with:
```js
                        ${sas.map(sa => `<th class="text-center th-sa1">${esc(sa.name)}<br><small>${wPerSA} %</small></th>`).join('')}
                        ${isSem2 ? `<th class="text-center th-sa2">1. Sem.<br><small>${g.semester1Note||0} %</small></th>` : ''}
```

In the student data calculation inside the rows, find:
```js
                        const hasSAData = sas.some(sa => s.schularbeiten?.[sa.id]);
                        const wdh = calcWdhTeilnote(cls, s.id);
                        const pr  = calcPraesTeilnote(cls, s.id);
                        const ha  = calcHATeilnote(cls, s.id);
                        const ges = calcGesamtnote(cls, s);

                        const forced    = hasSAData && !hasPositiveSA(cls, s);
```
Replace with:
```js
                        const sd = sem.studentData?.[s.id] || {};
                        const hasSAData = sas.some(sa => sd.schularbeiten?.[sa.id]);
                        const wdh = calcWdhTeilnote(sem, s.id);
                        const pr  = calcPraesTeilnote(sem, s.id);
                        const ha  = calcHATeilnote(sem, s.id);
                        const ges = calcGesamtnote(cls, sem, s);

                        const forced    = hasSAData && !hasPositiveSA(sem, s);
```

In the row cells, add the Semester 1 note column after the existing SA columns:
Find:
```js
                            ${sas.map(sa => {
                                const saData = s.schularbeiten?.[sa.id];
                                const n = saData ? calcNote(calcGesamt(saData)) : null;
                                return `<td class="td-sa1 text-center">${noteBadgeSA(n,'gsn-'+sa.id+'-'+s.id)}</td>`;
                            }).join('')}
```
Replace with:
```js
                            ${sas.map(sa => {
                                const saData = sd.schularbeiten?.[sa.id];
                                const n = saData ? calcNote(calcGesamt(saData)) : null;
                                return `<td class="td-sa1 text-center">${noteBadgeSA(n,'gsn-'+sa.id+'-'+s.id)}</td>`;
                            }).join('')}
                            ${isSem2 ? (() => {
                                const sem1Dec = calcGesamtnote(cls, cls.semester1, s);
                                const sem1Note = sem1Dec !== null ? calcNote ? noteInt(sem1Dec) : null : null;
                                return `<td class="td-sa2 text-center">${sem1Note !== null ? `<span class="note-badge note-${sem1Note}">${sem1Note}</span>` : '<span class="note-badge note-empty">—</span>'}</td>`;
                            })() : ''}
```

**Step 4: Update `updateGesamtColumn`**

Find:
```js
function updateGesamtColumn(cls) {
    if (activeTab !== 'gesamt') return;
    document.querySelectorAll('#gesamt-tbody tr').forEach(row => {
        const sid = row.dataset.sid;
        const s = cls.students.find(s=>s.id===sid); if(!s) return;
        const ges = calcGesamtnote(cls, s);

        const sas = cls.schularbeiten || [];
        const hasSAData = sas.some(sa => s.schularbeiten?.[sa.id]);
        const forced    = hasSAData && !hasPositiveSA(cls, s);
```
Replace with:
```js
function updateGesamtColumn(cls, sem) {
    if (activeTab !== 'gesamt') return;
    document.querySelectorAll('#gesamt-tbody tr').forEach(row => {
        const sid = row.dataset.sid;
        const s = cls.students.find(s=>s.id===sid); if(!s) return;
        const sd = sem.studentData?.[s.id] || {};
        const ges = calcGesamtnote(cls, sem, s);

        const sas = sem.schularbeiten || [];
        const hasSAData = sas.some(sa => sd.schularbeiten?.[sa.id]);
        const forced    = hasSAData && !hasPositiveSA(sem, s);
```

**Step 5: Update `updateWeightSum`**

Find:
```js
function updateWeightSum() {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const g = cls.gewichtung;
    const total = (+(g.schularbeiten)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```
Replace with:
```js
function updateWeightSum() {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const g = cls[activeSemester].gewichtung;
    const isSem2 = activeSemester === 'semester2';
    const total = (+(g.schularbeiten)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0)+(isSem2?(+(g.semester1Note)||0):0);
```

**Step 6: Final smoke test**

Open `http://localhost:5000`:
1. Reload — existing data migrates into Semester 1, Semester 2 is empty
2. Two semester tabs visible at top
3. Enter SA grades in Semester 1 → Gesamtnote calculates
4. Switch to Semester 2 → empty tables, fresh state
5. Gesamtnote tab in Semester 2 → weight card shows "1. Semester" input
6. Enter `50` for 1. Semester weight → semester 1 note appears in table column
7. Add SA, Wdh in Semester 2 → data stays separate from Semester 1
8. Reload → all data persists correctly in both semesters

---

## Done

Each class now has two fully independent semesters. The Semester 2 Gesamtnote automatically incorporates the Semester 1 overall grade with a configurable weight.
