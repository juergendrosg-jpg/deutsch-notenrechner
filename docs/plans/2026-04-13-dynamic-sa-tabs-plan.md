# Dynamic Schularbeit Tabs — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the fixed `schularbeit1`/`schularbeit2` data model with a dynamic array of Schularbeiten, rendered as browser-like sub-tabs inside the "Schularbeiten" main tab.

**Architecture:** All changes are in `index.html`. The class stores a `schularbeiten` array of `{id, name}` descriptors. Each student stores a `schularbeiten` object keyed by SA id. A new `activeSaId` global tracks the active sub-tab. The Gesamtnote uses a single `gewichtung.schularbeiten` weight split equally across all SAs.

**Tech Stack:** Vanilla JS, Bootstrap 5 CSS, native `<dialog>` modals

---

### Task 1: Update data model — `newClass`, `newStudent`, `activeSaId`

**Files:**
- Modify: `index.html` lines 627, 832–838, 850–858

**Step 1: Add `activeSaId` global after `activeTab` (line 627)**

Find:
```js
let activeTab = 'sa'; // 'sa' | 'wdh' | 'praes' | 'ha' | 'gesamt'
```
Replace with:
```js
let activeTab = 'sa'; // 'sa' | 'wdh' | 'praes' | 'ha' | 'gesamt'
let activeSaId = null;
```

**Step 2: Update `newClass()` (lines 832–838)**

Find:
```js
function newClass(name) {
    return {
        id: genId(), name: name.trim(), students: [],
        wiederholungen: [], praesentationen: [], hausaufgaben: [],
        gewichtung: {sa1:20, sa2:20, wiederholung:20, praesentation:20, hausaufgaben:20}
    };
}
```
Replace with:
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

**Step 3: Update `newStudent()` (lines 850–858)**

Find:
```js
function newStudent(name) {
    return {
        id: genId(), name: name.trim(),
        schularbeit1: {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null},
        schularbeit2: {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null},
        wiederholungen: {}, praesentationen: {}, hausaufgaben: {},
        kommentar1: '', kommentar2: ''
    };
}
```
Replace with:
```js
function newStudent(name) {
    return {
        id: genId(), name: name.trim(),
        schularbeiten: {},
        wiederholungen: {}, praesentationen: {}, hausaufgaben: {}
    };
}
```

**Step 4: Verify in browser**

Open `http://localhost:5000`, add a new class, add a student. In browser console run:
```js
data.classes[0].schularbeiten   // should be [{id:..., name:'1. Schularbeit'}]
data.classes[0].students[0].schularbeiten  // should be {}
data.classes[0].gewichtung      // should have schularbeiten:40, no sa1/sa2
```

---

### Task 2: Migrate existing data in `migrateData()`

**Files:**
- Modify: `index.html` lines 649–667

**Step 1: Replace `migrateData()` entirely**

Find:
```js
function migrateData() {
    for (const cls of data.classes) {
        if (!cls.wiederholungen)  cls.wiederholungen  = [];
        if (!cls.praesentationen) cls.praesentationen = [];
        if (!cls.hausaufgaben)    cls.hausaufgaben    = [];
        if (!cls.gewichtung) cls.gewichtung = {sa1:20, sa2:20, wiederholung:20, praesentation:20, hausaufgaben:20};
        if (!cls.students)    cls.students    = [];
        for (const s of cls.students) {
            if (!s.wiederholungen)  s.wiederholungen  = {};
            if (!s.praesentationen) s.praesentationen = {};
            if (!s.hausaufgaben)    s.hausaufgaben    = {};
            if (s.kommentar !== undefined && s.kommentar1 === undefined) {
                s.kommentar1 = s.kommentar; delete s.kommentar;
            }
            if (s.kommentar1 === undefined) s.kommentar1 = '';
            if (s.kommentar2 === undefined) s.kommentar2 = '';
        }
    }
}
```
Replace with:
```js
function migrateData() {
    for (const cls of data.classes) {
        if (!cls.wiederholungen)  cls.wiederholungen  = [];
        if (!cls.praesentationen) cls.praesentationen = [];
        if (!cls.hausaufgaben)    cls.hausaufgaben    = [];
        if (!cls.students)        cls.students        = [];

        // Migrate old fixed SA fields → dynamic schularbeiten array
        if (!cls.schularbeiten) {
            const hasSA1 = cls.gewichtung?.sa1 !== undefined;
            const hasSA2 = cls.gewichtung?.sa2 !== undefined;
            cls.schularbeiten = [];
            if (hasSA1 || !hasSA2) cls.schularbeiten.push({id:'sa1-legacy', name:'1. Schularbeit'});
            if (hasSA2)            cls.schularbeiten.push({id:'sa2-legacy', name:'2. Schularbeit'});
        }

        // Migrate gewichtung: sa1+sa2 → schularbeiten
        if (!cls.gewichtung) {
            cls.gewichtung = {schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20};
        } else if (cls.gewichtung.sa1 !== undefined || cls.gewichtung.sa2 !== undefined) {
            cls.gewichtung.schularbeiten = (+(cls.gewichtung.sa1)||0) + (+(cls.gewichtung.sa2)||0);
            delete cls.gewichtung.sa1;
            delete cls.gewichtung.sa2;
        } else if (cls.gewichtung.schularbeiten === undefined) {
            cls.gewichtung.schularbeiten = 40;
        }

        for (const s of cls.students) {
            if (!s.wiederholungen)  s.wiederholungen  = {};
            if (!s.praesentationen) s.praesentationen = {};
            if (!s.hausaufgaben)    s.hausaufgaben    = {};
            if (!s.schularbeiten)   s.schularbeiten   = {};

            // Migrate old schularbeit1 / schularbeit2 fixed fields
            if (s.schularbeit1 !== undefined) {
                s.schularbeiten['sa1-legacy'] = {
                    aufgabenstellung: s.schularbeit1.aufgabenstellung ?? null,
                    fehler:           s.schularbeit1.fehler           ?? null,
                    wortschatz:       s.schularbeit1.wortschatz       ?? null,
                    textorganisation: s.schularbeit1.textorganisation ?? null,
                    kommentar:        s.kommentar1 ?? ''
                };
                delete s.schularbeit1;
            }
            if (s.schularbeit2 !== undefined) {
                s.schularbeiten['sa2-legacy'] = {
                    aufgabenstellung: s.schularbeit2.aufgabenstellung ?? null,
                    fehler:           s.schularbeit2.fehler           ?? null,
                    wortschatz:       s.schularbeit2.wortschatz       ?? null,
                    textorganisation: s.schularbeit2.textorganisation ?? null,
                    kommentar:        s.kommentar2 ?? ''
                };
                delete s.schularbeit2;
            }
            delete s.kommentar1;
            delete s.kommentar2;
        }
    }
}
```

**Step 2: Verify in browser**

Reload `http://localhost:5000`. If there's existing data from before, open browser console:
```js
data.classes[0].schularbeiten   // should be array with sa1-legacy and/or sa2-legacy
data.classes[0].gewichtung      // should have schularbeiten:N, no sa1/sa2
data.classes[0].students[0].schularbeiten  // should have sa1-legacy entry
```

---

### Task 3: SA management functions — `addSA`, `deleteSA`, `selectSA`

**Files:**
- Modify: `index.html` — add after `deleteClass()` function (around line 840)

**Step 1: Add SA management functions after `deleteClass`**

Find:
```js
function deleteClass(id) {
    data.classes = data.classes.filter(c=>c.id!==id);
    if (activeClassId===id) activeClassId = data.classes[0]?.id ?? null;
    saveData(); render();
}
```
Replace with:
```js
function deleteClass(id) {
    data.classes = data.classes.filter(c=>c.id!==id);
    if (activeClassId===id) activeClassId = data.classes[0]?.id ?? null;
    saveData(); render();
}

function addSA() {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    const n = cls.schularbeiten.length + 1;
    const sa = {id: genId(), name: n + '. Schularbeit'};
    cls.schularbeiten.push(sa);
    activeSaId = sa.id;
    saveData(); renderTabContent();
}

function selectSA(saId) {
    activeSaId = saId;
    renderTabContent();
}

function deleteSA(saId) {
    const cls = data.classes.find(c=>c.id===activeClassId); if(!cls) return;
    if (cls.schularbeiten.length <= 1) return; // minimum 1
    cls.schularbeiten = cls.schularbeiten.filter(sa=>sa.id!==saId);
    for (const s of cls.students) delete s.schularbeiten[saId];
    if (activeSaId === saId) activeSaId = cls.schularbeiten[0].id;
    saveData(); renderTabContent();
}
```

**Step 2: Initialize `activeSaId` when a class is selected**

Find:
```js
function selectClass(id) {
```
Read the full `selectClass` function body. After setting `activeClassId = id`, add:
```js
const cls = data.classes.find(c=>c.id===id);
activeSaId = cls?.schularbeiten?.[0]?.id ?? null;
```

Also update the `DOMContentLoaded` init after `activeClassId = data.classes[0]?.id ?? null;`:

Find:
```js
    activeClassId = data.classes[0]?.id ?? null;
    render();
```
Replace with:
```js
    activeClassId = data.classes[0]?.id ?? null;
    const _initCls = data.classes[0];
    activeSaId = _initCls?.schularbeiten?.[0]?.id ?? null;
    render();
```

**Step 3: Verify**

Open `http://localhost:5000`. In console: `activeSaId` should be the id of the first SA of the active class.

---

### Task 4: Rewrite `renderTabSA(cls)` with sub-tab bar

**Files:**
- Modify: `index.html` lines 1074–1096 and 1098–1108

**Step 1: Replace `renderTabSA` and `saSubHeaders`**

Find the entire `renderTabSA` function:
```js
function renderTabSA(cls) {
    if (!cls.students.length) return emptyStudents();
    return `
        <div class="table-wrapper">
            <table class="grade-table table table-bordered table-sm mb-0" id="sa-table">
                <thead>
                    <tr>
                        <th class="sticky-col" rowspan="2" style="background:#343a40;color:#fff;min-width:180px;">Name</th>
                        <th colspan="8" class="text-center th-sa1">1. Schularbeit</th>
                        <th colspan="8" class="text-center th-sa2">2. Schularbeit</th>
                    </tr>
                    <tr>
                        ${saSubHeaders('th-sa1')}
                        ${saSubHeaders('th-sa2')}
                    </tr>
                </thead>
                <tbody id="sa-tbody">
                    ${cls.students.map(s => renderSARow(s)).join('')}
                </tbody>
            </table>
        </div>
        <p class="text-muted small mt-2"><i class="bi bi-info-circle me-1"></i>* Sprachrichtigkeit: <code>MAX(0; 8 − GANZZAHL(Fehler / 3))</code> &nbsp;|&nbsp; Grenzfälle mit <strong>*</strong> markiert.</p>`;
}
```
Replace with:
```js
function renderTabSA(cls) {
    const sas = cls.schularbeiten || [];
    if (!activeSaId || !sas.find(sa=>sa.id===activeSaId)) {
        activeSaId = sas[0]?.id ?? null;
    }
    const tabBar = `
        <div class="sa-tab-bar">
            ${sas.map(sa => `
                <div class="sa-tab ${sa.id===activeSaId?'active':''}" data-said="${sa.id}">
                    <span onclick="selectSA('${sa.id}')">${esc(sa.name)}</span>
                    ${sas.length > 1
                        ? `<button class="sa-tab-del" data-said="${sa.id}" title="Schularbeit löschen" onclick="confirmDeleteSA('${sa.id}',this)">×</button>`
                        : ''}
                </div>`).join('')}
            <button class="sa-tab-add" onclick="addSA()" title="Schularbeit hinzufügen">+</button>
        </div>`;
    if (!activeSaId || !cls.students.length) {
        return tabBar + (cls.students.length ? '' : emptyStudents());
    }
    return tabBar + `
        <div class="table-wrapper">
            <table class="grade-table table table-bordered table-sm mb-0" id="sa-table">
                <thead>
                    <tr>
                        <th class="sticky-col" style="background:#343a40;color:#fff;min-width:180px;">Name</th>
                        <th class="text-center th-sa1" title="Aufgabenstellung (max. 8)">Aufgaben&shy;stellung<br><span style="opacity:.7">0–8</span></th>
                        <th class="text-center th-sa1" title="Fehler (Eingabe)">Fehler</th>
                        <th class="text-center th-sa1" title="Sprachrichtigkeit (auto)">Sprach&shy;richtigkeit<br><span style="opacity:.7">auto *</span></th>
                        <th class="text-center th-sa1" title="Wortschatz (max. 8)">Wort&shy;schatz<br><span style="opacity:.7">0–8</span></th>
                        <th class="text-center th-sa1" title="Textorganisation (max. 8)">Text&shy;organisation<br><span style="opacity:.7">0–8</span></th>
                        <th class="text-center th-sa1" title="Gesamtpunkte (max. 32)">Gesamt<br><span style="opacity:.7">max 32</span></th>
                        <th class="text-center th-sa1">Note</th>
                        <th class="text-center th-sa1">Kommentar</th>
                    </tr>
                </thead>
                <tbody id="sa-tbody">
                    ${cls.students.map(s => renderSARow(s, activeSaId)).join('')}
                </tbody>
            </table>
        </div>
        <p class="text-muted small mt-2"><i class="bi bi-info-circle me-1"></i>* Sprachrichtigkeit: <code>MAX(0; 8 − GANZZAHL(Fehler / 3))</code> &nbsp;|&nbsp; Grenzfälle mit <strong>*</strong> markiert.</p>`;
}
```

**Step 2: Delete the now-unused `saSubHeaders` function**

Find and delete entirely:
```js
function saSubHeaders(cls) {
    return `
        <th class="text-center ${cls}" title="Aufgabenstellung (max. 8)">Aufgaben&shy;stellung<br><span style="opacity:.7">0–8</span></th>
        <th class="text-center ${cls}" title="Fehler (Eingabe)">Fehler</th>
        <th class="text-center ${cls}" title="Sprachrichtigkeit (auto)">Sprach&shy;richtigkeit<br><span style="opacity:.7">auto *</span></th>
        <th class="text-center ${cls}" title="Wortschatz (max. 8)">Wort&shy;schatz<br><span style="opacity:.7">0–8</span></th>
        <th class="text-center ${cls}" title="Textorganisation (max. 8)">Text&shy;organisation<br><span style="opacity:.7">0–8</span></th>
        <th class="text-center ${cls}" title="Gesamtpunkte (max. 32)">Gesamt<br><span style="opacity:.7">max 32</span></th>
        <th class="text-center ${cls}">Note</th>
        <th class="text-center ${cls}">Kommentar</th>`;
}
```

**Step 3: Add CSS for the SA tab bar**

Find the existing `.class-tabs` CSS block and add after it:
```css
/* ── SA sub-tabs ─────────────────────────────── */
.sa-tab-bar {
    display: flex; align-items: center; gap: 3px;
    margin-bottom: 1rem; flex-wrap: wrap;
}
.sa-tab {
    display: flex; align-items: center; gap: 4px;
    padding: 5px 12px; border-radius: 7px 7px 0 0;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-bottom: none; cursor: pointer;
    font-size: .84rem; color: #6b7a90;
    transition: background 0.12s, color 0.12s;
}
.sa-tab:hover { background: rgba(255,255,255,0.08); color: #c0c8db; }
.sa-tab.active { background: rgba(85,73,232,0.18); border-color: rgba(85,73,232,0.35); color: #9b93f7; }
.sa-tab span { cursor: pointer; }
.sa-tab-del {
    background: none; border: none; color: inherit;
    opacity: .5; font-size: .9rem; padding: 0 2px;
    cursor: pointer; line-height: 1;
}
.sa-tab-del:hover { opacity: 1; color: #f87191; }
.sa-tab-del.confirm { color: #f87191; opacity: 1; font-weight: 700; }
.sa-tab-add {
    background: none; border: 1px dashed rgba(255,255,255,0.15);
    border-radius: 7px; color: #4ade80; font-size: 1.1rem;
    padding: 3px 10px; cursor: pointer; line-height: 1;
    transition: background 0.12s;
}
.sa-tab-add:hover { background: rgba(74,222,128,0.08); }
```

**Step 4: Add `confirmDeleteSA` function (double-confirm via button state)**

Add after `deleteSA`:
```js
function confirmDeleteSA(saId, btn) {
    if (btn.dataset.confirm === '1') {
        deleteSA(saId);
    } else {
        btn.dataset.confirm = '1';
        btn.classList.add('confirm');
        btn.textContent = '?';
        setTimeout(() => {
            btn.dataset.confirm = '0';
            btn.classList.remove('confirm');
            btn.textContent = '×';
        }, 2500);
    }
}
```

---

### Task 5: Rewrite `renderSARow` and `updateSACells`

**Files:**
- Modify: `index.html` lines 1110–1135 and 1161–1169

**Step 1: Replace `renderSARow`**

Find:
```js
function renderSARow(s) {
    const sa1=s.schularbeit1, sa2=s.schularbeit2;
    const sp1=calcSprachrichtigkeit(sa1.fehler), sp2=calcSprachrichtigkeit(sa2.fehler);
    const g1=calcGesamt(sa1), g2=calcGesamt(sa2);
    const n1=calcNote(g1), n2=calcNote(g2);
    return `
    <tr data-sid="${s.id}">
        <td class="sticky-col">${studentNameCell(s)}</td>
        <td class="td-sa1 text-center">${numInp(s.id,'schularbeit1','aufgabenstellung',sa1.aufgabenstellung,0,8)}</td>
        <td class="td-sa1 text-center">${numInp(s.id,'schularbeit1','fehler',sa1.fehler,0,null)}</td>
        <td class="td-sa1 text-center"><span class="cell-ro" id="sp1-${s.id}">${sp1??'—'}</span></td>
        <td class="td-sa1 text-center">${numInp(s.id,'schularbeit1','wortschatz',sa1.wortschatz,0,8)}</td>
        <td class="td-sa1 text-center">${numInp(s.id,'schularbeit1','textorganisation',sa1.textorganisation,0,8)}</td>
        <td class="td-sa1 text-center"><span class="cell-ro" id="g1-${s.id}">${g1??'—'}</span></td>
        <td class="td-sa1 text-center">${noteBadgeSA(n1,'n1-'+s.id)}</td>
        <td class="td-sa1"><textarea class="komm-input" data-sid="${s.id}" data-field="kommentar1" placeholder="Kommentar SA1...">${esc(s.kommentar1||'')}</textarea></td>
        <td class="td-sa2 text-center">${numInp(s.id,'schularbeit2','aufgabenstellung',sa2.aufgabenstellung,0,8)}</td>
        <td class="td-sa2 text-center">${numInp(s.id,'schularbeit2','fehler',sa2.fehler,0,null)}</td>
        <td class="td-sa2 text-center"><span class="cell-ro" id="sp2-${s.id}">${sp2??'—'}</span></td>
        <td class="td-sa2 text-center">${numInp(s.id,'schularbeit2','wortschatz',sa2.wortschatz,0,8)}</td>
        <td class="td-sa2 text-center">${numInp(s.id,'schularbeit2','textorganisation',sa2.textorganisation,0,8)}</td>
        <td class="td-sa2 text-center"><span class="cell-ro" id="g2-${s.id}">${g2??'—'}</span></td>
        <td class="td-sa2 text-center">${noteBadgeSA(n2,'n2-'+s.id)}</td>
        <td class="td-sa2"><textarea class="komm-input" data-sid="${s.id}" data-field="kommentar2" placeholder="Kommentar SA2...">${esc(s.kommentar2||'')}</textarea></td>
    </tr>`;
}
```
Replace with:
```js
function renderSARow(s, saId) {
    const sa = s.schularbeiten?.[saId] || {aufgabenstellung:null,fehler:null,wortschatz:null,textorganisation:null,kommentar:''};
    const sp = calcSprachrichtigkeit(sa.fehler);
    const g  = calcGesamt(sa);
    const n  = calcNote(g);
    return `
    <tr data-sid="${s.id}">
        <td class="sticky-col">${studentNameCell(s)}</td>
        <td class="td-sa1 text-center">${numInp(s.id, saId, 'aufgabenstellung', sa.aufgabenstellung, 0, 8)}</td>
        <td class="td-sa1 text-center">${numInp(s.id, saId, 'fehler', sa.fehler, 0, null)}</td>
        <td class="td-sa1 text-center"><span class="cell-ro" id="sp-${s.id}">${sp??'—'}</span></td>
        <td class="td-sa1 text-center">${numInp(s.id, saId, 'wortschatz', sa.wortschatz, 0, 8)}</td>
        <td class="td-sa1 text-center">${numInp(s.id, saId, 'textorganisation', sa.textorganisation, 0, 8)}</td>
        <td class="td-sa1 text-center"><span class="cell-ro" id="g-${s.id}">${g??'—'}</span></td>
        <td class="td-sa1 text-center">${noteBadgeSA(n, 'n-'+s.id)}</td>
        <td class="td-sa1"><textarea class="komm-input" data-sid="${s.id}" data-said="${saId}" placeholder="Kommentar...">${esc(sa.kommentar||'')}</textarea></td>
    </tr>`;
}
```

**Step 2: Replace `updateSACells`**

Find:
```js
function updateSACells(cls, s) {
    const sa1=s.schularbeit1, sa2=s.schularbeit2;
    const sp1=calcSprachrichtigkeit(sa1.fehler), sp2=calcSprachrichtigkeit(sa2.fehler);
    const g1=calcGesamt(sa1), g2=calcGesamt(sa2);
    const n1=calcNote(g1), n2=calcNote(g2);
    setTxt('sp1-'+s.id, sp1??'—'); setTxt('g1-'+s.id, g1??'—');
    setTxt('sp2-'+s.id, sp2??'—'); setTxt('g2-'+s.id, g2??'—');
    setBadgeSA('n1-'+s.id, n1); setBadgeSA('n2-'+s.id, n2);
}
```
Replace with:
```js
function updateSACells(cls, s, saId) {
    const sa = s.schularbeiten?.[saId] || {};
    const sp = calcSprachrichtigkeit(sa.fehler);
    const g  = calcGesamt(sa);
    const n  = calcNote(g);
    setTxt('sp-'+s.id, sp??'—');
    setTxt('g-'+s.id,  g??'—');
    setBadgeSA('n-'+s.id, n);
}
```

---

### Task 6: Fix `updateSAField` and `updateKommentar`

**Files:**
- Modify: `index.html` lines 877–890

**Step 1: Replace `updateSAField`**

Find:
```js
function updateSAField(sid, saKey, field, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        const n = val==='' ? null : parseInt(val,10);
        s[saKey][field] = (val===''||isNaN(n)) ? null : n;
        saveData(); updateSACells(cls, s); return;
    }
}
```
Replace with:
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

**Step 2: Replace `updateKommentar`**

Find:
```js
function updateKommentar(sid, field, val) {
    for (const cls of data.classes) {
        const s = cls.students.find(s=>s.id===sid); if(!s) continue;
        s[field] = val; saveData(); return;
    }
}
```
Replace with:
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

---

### Task 7: Fix `attachSAListeners`

**Files:**
- Modify: `index.html` lines 1151–1159

**Step 1: Replace `attachSAListeners`**

Find:
```js
function attachSAListeners() {
    const tbody = document.getElementById('sa-tbody'); if(!tbody) return;
    tbody.querySelectorAll('.sa-inp').forEach(inp => {
        inp.addEventListener('change', function() { updateSAField(this.dataset.sid, this.dataset.sa, this.dataset.field, this.value); });
    });
    tbody.querySelectorAll('.komm-input').forEach(ta => {
        ta.addEventListener('change', function() { updateKommentar(this.dataset.sid, this.dataset.field, this.value); });
    });
}
```
Replace with:
```js
function attachSAListeners() {
    const tbody = document.getElementById('sa-tbody'); if(!tbody) return;
    tbody.querySelectorAll('.sa-inp').forEach(inp => {
        inp.addEventListener('change', function() { updateSAField(this.dataset.sid, this.dataset.sa, this.dataset.field, this.value); });
    });
    tbody.querySelectorAll('.komm-input').forEach(ta => {
        ta.addEventListener('change', function() { updateKommentar(this.dataset.sid, this.dataset.said, this.value); });
    });
}
```

Note: only `data-field` → `data-said` changes in the komm-input listener.

---

### Task 8: Fix Gesamtnote — weight card + `calcGesamtnote`

**Files:**
- Modify: `index.html` lines 768–790 and ~1454–1458

**Step 1: Replace `calcGesamtnote`**

Find:
```js
function calcGesamtnote(cls, s) {
    const g = cls.gewichtung || {};
    const sa1Note  = calcNote(calcGesamt(s.schularbeit1));
    const sa2Note  = calcNote(calcGesamt(s.schularbeit2));
    const wdhNote  = calcWdhTeilnote(cls, s.id);
    const praesNote= calcPraesTeilnote(cls, s.id);
    const haNote   = calcHATeilnote(cls, s.id);

    const components = [
        {val: sa1Note?.decimal   ?? null, w: +(g.sa1         || 0)},
        {val: sa2Note?.decimal   ?? null, w: +(g.sa2         || 0)},
        {val: wdhNote,                    w: +(g.wiederholung || 0)},
        {val: praesNote,                  w: +(g.praesentation|| 0)},
        {val: haNote,                     w: +(g.hausaufgaben || 0)},
    ];

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

    // Add each SA with equal share of the total SA weight
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

**Step 2: Fix the weight card in the Gesamtnote tab**

Find:
```js
${weightInput('sa1',         '1. Schularbeit', g.sa1)}
${weightInput('sa2',         '2. Schularbeit', g.sa2)}
${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
${weightInput('praesentation','Präsentation',  g.praesentation)}
${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
```
Replace with:
```js
${weightInput('schularbeiten', `Schularbeiten (${cls.schularbeiten?.length||1}× gleichwertig)`, g.schularbeiten)}
${weightInput('wiederholung','Wiederholung',   g.wiederholung)}
${weightInput('praesentation','Präsentation',  g.praesentation)}
${weightInput('hausaufgaben','Hausübungen',    g.hausaufgaben)}
```

**Step 3: Fix the weight sum check**

Search for code that sums all weights (likely computes `totalW`). It currently adds `g.sa1` and `g.sa2`. Update to use `g.schularbeiten`:

Find (around line 1437 area, look for `+(g.sa1||0)+(+(g.sa2||0))`):
```js
const totalW = (+(g.sa1)||0)+(+(g.sa2)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```
Replace with:
```js
const totalW = (+(g.schularbeiten)||0)+(+(g.wiederholung)||0)+(+(g.praesentation)||0)+(+(g.hausaufgaben)||0);
```

Also find the second occurrence of this same sum (in `renderGesamtRow` or similar) and apply the same fix.

**Step 4: Fix the Gesamtnote table header** (currently shows "1. SA" and "2. SA" columns)

Search for `th-sa1` and `th-sa2` column headers in the Gesamtnote render function. Replace the two fixed SA columns with dynamic ones:

Find (look for something like):
```js
<th class="text-center th-sa1">1. SA<br><small>${g.sa1||0} %</small></th>
<th class="text-center th-sa2">2. SA<br><small>${g.sa2||0} %</small></th>
```
Replace with (dynamic, one column per SA):
```js
${(cls.schularbeiten||[]).map((sa,i) => `<th class="text-center th-sa1">${esc(sa.name)}<br><small>${saWeight > 0 ? (saWeight/(cls.schularbeiten.length)).toFixed(0) : 0} %</small></th>`).join('')}
```
where `saWeight = +(g.schularbeiten||0)`. Make sure `saWeight` is computed before this template.

**Step 5: Fix the Gesamtnote table rows** — they currently show `noteBadgeSA(n1,'gsn1-'+s.id)` and `noteBadgeSA(n2,'gsn2-'+s.id)` for fixed sa1/sa2. Replace with a dynamic map over `cls.schularbeiten`.

Find (look for):
```js
<td class="td-sa1 text-center">${noteBadgeSA(n1,'gsn1-'+s.id)}</td>
<td class="td-sa2 text-center">${noteBadgeSA(n2,'gsn2-'+s.id)}</td>
```
Replace with:
```js
${(cls.schularbeiten||[]).map(sa => {
    const saData = s.schularbeiten?.[sa.id];
    const n = saData ? calcNote(calcGesamt(saData)) : null;
    return `<td class="td-sa1 text-center">${noteBadgeSA(n,'gsn-'+sa.id+'-'+s.id)}</td>`;
}).join('')}
```

**Step 6: Fix `hasMindestensEinPositiveSA`**

Find the function that checks for a positive SA (grade ≤ 4). Currently checks `schularbeit1` and `schularbeit2`:
```js
// Hat der Schüler mindestens eine positive Schularbeit (Note ≤ 4)?
```
Read its body and replace it to iterate over `cls.schularbeiten` and check `s.schularbeiten[sa.id]`.

The function likely looks like:
```js
function hasMindestensEinPositiveSA(s) {
    const n1 = calcNote(calcGesamt(s.schularbeit1));
    const n2 = calcNote(calcGesamt(s.schularbeit2));
    return (n1 && n1.note <= 4) || (n2 && n2.note <= 4);
}
```
Replace with:
```js
function hasMindestensEinPositiveSA(cls, s) {
    const sas = cls.schularbeiten || [];
    if (sas.length === 0) return true;
    return sas.some(sa => {
        const saData = s.schularbeiten?.[sa.id];
        if (!saData) return false;
        const n = calcNote(calcGesamt(saData));
        return n && n.note <= 4;
    });
}
```
Then update all call sites of `hasMindestensEinPositiveSA(s)` to pass `cls` as first argument: `hasMindestensEinPositiveSA(cls, s)`.

**Step 7: Final smoke test**

Open `http://localhost:5000`:
1. Add a class → should have "1. Schularbeit" tab with `[+]` button
2. Click `[+]` → "2. Schularbeit" tab appears
3. Enter grades in SA1, switch to SA2, enter different grades
4. Click `[×]` on SA2 → shows `?` → click again → SA2 deleted
5. Check Gesamtnote tab → weight card shows "Schularbeiten (1× gleichwertig)"
6. Reload → data persists correctly

---

## Done

The Schularbeiten section now uses dynamic sub-tabs. Any number of SAs can be added. Each SA has its own grade table. The Gesamtnote splits the SA weight equally across all SAs.
