# Schuljahr Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Schuljahr" (school year) layer above classes so students stay in their class across years but grades are fresh per school year.

**Architecture:** `data` gets a new root structure: `{ activeSchuljahrId, schuljahre: [{id, name, classes}] }`. All existing `data.classes` accesses are routed through a new `activeClasses()` helper. The sidebar gets a school-year selector strip at the top plus a "new school year" modal.

**Tech Stack:** Vanilla JS + Tailwind CSS CDN v4 + Flask. Single file: `index.html`. No build step.

---

## Task 1: Data migration — wrap existing classes in first Schuljahr

**Files:**
- Modify: `index.html` — `migrateData()` at line 898, global state at line 800

**Step 1: Update global state declaration**

At line 800, change:
```js
let data = {classes: []};
```
to:
```js
let data = {schuljahre: [], activeSchuljahrId: null};
```

**Step 2: Add `activeClasses()` helper right after `genId()` (after line 1011)**

```js
function activeClasses() {
    const sj = data.schuljahre.find(s => s.id === data.activeSchuljahrId);
    return sj ? sj.classes : [];
}
function activeSchuljahr() {
    return data.schuljahre.find(s => s.id === data.activeSchuljahrId) ?? null;
}
```

**Step 3: Add Schuljahr migration at the TOP of `migrateData()` (before the `for (const cls of data.classes)` loop, line 899)**

```js
// ── Migrate flat data.classes → schuljahre structure ──────────
if (!data.schuljahre || !Array.isArray(data.schuljahre)) {
    const existingClasses = data.classes || [];
    const sjId = genId();
    data.schuljahre = [{ id: sjId, name: 'Importiert', classes: existingClasses }];
    data.activeSchuljahrId = sjId;
    delete data.classes;
}
if (!data.activeSchuljahrId || !data.schuljahre.find(s => s.id === data.activeSchuljahrId)) {
    data.activeSchuljahrId = data.schuljahre[0]?.id ?? null;
}
```

**Step 4: Fix the `for` loop in `migrateData()` — it still references `data.classes`**

Change line 899:
```js
for (const cls of data.classes) {
```
to:
```js
for (const sj of data.schuljahre) { for (const cls of sj.classes) {
```

And close the extra brace at the end of the loop (after the last `}` that closes the per-class block, add another `}`).

**Step 5: Manual test**

Start `python server.py`, open browser. Existing data should appear exactly as before. Check browser console for errors.

---

## Task 2: Replace all `data.classes` references with `activeClasses()`

**Files:**
- Modify: `index.html` — all JS functions that read/write `data.classes`

These are the places to update (search for `data.classes`):

| Location | Old | New |
|---|---|---|
| `importData()` line 851 | `parsed.classes` check | keep as-is (migration handles it) |
| `importData()` line 855 | `data = parsed` | add `migrateData()` call after |
| `addClass()` line 1262 | `data.classes.push(c)` | `activeClasses().push(c)` |
| `deleteClass()` line 1269 | `data.classes = data.classes.filter(...)` | use `activeSchuljahr().classes = activeClasses().filter(...)` |
| `deleteClass()` line 1270 | `data.classes[0]?.id` | `activeClasses()[0]?.id` |
| `addStudent()` line 1340 | `data.classes.find(...)` | `activeClasses().find(...)` |
| `editStudent()` line 1344 | `for (const cls of data.classes)` | `for (const cls of activeClasses())` |
| `deleteStudent()` line 1350 | `for (const cls of data.classes)` | `for (const cls of activeClasses())` |
| `renderSidebar()` line 1548 | `data.classes.filter(...)` x2 | `activeClasses().filter(...)` x2 |
| `renderContent()` line 1556 | `!data.classes.length` | `!activeClasses().length` |
| `renderContent()` line 1560 | `data.classes.find(...)` | `activeClasses().find(...)` |
| `selectClass()` line 1588 | `data.classes.find(...)` | `activeClasses().find(...)` |
| `selectSemester()` line 1595 | `data.classes.find(...)` | `activeClasses().find(...)` |
| `renderTabContent()` line 1611 | `data.classes.find(...)` | `activeClasses().find(...)` |
| `DOMContentLoaded` line 2549 | `data.classes[0]?.id` | `activeClasses()[0]?.id` |
| `DOMContentLoaded` line 2550 | `data.classes[0]` | `activeClasses()[0]` |
| All other `data.classes.find(c=>c.id===activeClassId)` patterns | → | `activeClasses().find(c=>c.id===activeClassId)` |

**Step 1: Do a global search for `data.classes` in index.html and replace all occurrences per the table above.**

Use Grep to find all occurrences first:
```
grep -n "data\.classes" index.html
```

**Step 2: Fix `importData()` — after `data = parsed`, call `migrateData()` and `render()`**

```js
data = parsed;
migrateData();
saveData();
render();
```

**Step 3: Also update `editClass()` and other class mutation functions that use `data.classes.find(...)`**

Search pattern: `data\.classes\.find`  
Replace with: `activeClasses().find`

**Step 4: Manual test**

Reload, create a class, add a student, enter grades. Verify everything still works.

---

## Task 3: Add Schuljahr selector to sidebar HTML

**Files:**
- Modify: `index.html` — sidebar HTML at line 602, CSS in `<style>` block

**Step 1: Add CSS for the Schuljahr selector (in the `@layer components` block, after `.sidebar-group-label` styles ~line 449)**

```css
/* ── Schuljahr selector ── */
#schuljahr-selector {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 8px 8px 4px 8px;
    border-bottom: 1px solid var(--paper-line);
    margin-bottom: 4px;
}
.sj-chip {
    font-size: 11px; font-weight: 500;
    padding: 2px 8px; border-radius: 20px;
    cursor: pointer;
    background: var(--paper-line);
    color: var(--ink-soft);
    border: 1px solid transparent;
    white-space: nowrap;
}
.sj-chip.active {
    background: var(--rose-200);
    color: var(--rose-500);
    border-color: var(--rose-300);
}
.sj-chip:hover:not(.active) { background: var(--rose-100); }
.sj-add-btn {
    font-size: 13px; line-height: 1;
    padding: 2px 6px; border-radius: 20px;
    cursor: pointer;
    background: transparent;
    color: var(--ink-mute);
    border: 1px dashed var(--ink-faint);
}
.sj-add-btn:hover { color: var(--rose-500); border-color: var(--rose-300); }
```

**Step 2: Add Schuljahr selector HTML to sidebar, before the Unterstufe section (before line 603)**

Replace the opening `<div id="sidebar">` block content. After `<div id="sidebar">`, add:

```html
<div id="schuljahr-selector">
    <!-- filled by renderSidebar() -->
</div>
```

The existing Unterstufe/Oberstufe divs stay below it.

**Step 3: Manual test** — Sidebar should show the "Importiert" chip.

---

## Task 4: Add `renderSchuljahrSelector()` and wire into `renderSidebar()`

**Files:**
- Modify: `index.html` — `renderSidebar()` at line 1536

**Step 1: Add `renderSchuljahrSelector()` above `renderSidebar()`**

```js
function renderSchuljahrSelector() {
    const el = document.getElementById('schuljahr-selector');
    if (!el) return;
    el.innerHTML = data.schuljahre.map(sj =>
        `<span class="sj-chip ${sj.id===data.activeSchuljahrId?'active':''}" onclick="selectSchuljahr('${sj.id}')">${esc(sj.name)}</span>`
    ).join('') + `<button class="sj-add-btn" onclick="openAddSchuljahr()" title="Neues Schuljahr">+</button>`;
}
```

**Step 2: Add `selectSchuljahr()` function**

```js
function selectSchuljahr(sjId) {
    data.activeSchuljahrId = sjId;
    activeClassId = activeClasses()[0]?.id ?? null;
    const initCls = activeClasses()[0];
    activeSaId = initCls?.[activeSemester]?.schularbeiten?.[0]?.id ?? null;
    activeTab = 'sa';
    saveData();
    render();
}
```

**Step 3: Call `renderSchuljahrSelector()` at the start of `renderSidebar()`**

```js
function renderSidebar() {
    renderSchuljahrSelector();
    // ... rest unchanged
```

**Step 4: Manual test** — clicking chips should switch context (currently only one chip).

---

## Task 5: Add "Neues Schuljahr" modal HTML

**Files:**
- Modify: `index.html` — modal section (around line 764, after existing modals)

**Step 1: Add the modal HTML before `</body>` or after the last `</dialog>`**

```html
<!-- Neues Schuljahr -->
<dialog id="modalAddSchuljahr">
    <div class="modal-header">
        <h6 class="modal-title"><i class="bi bi-calendar-plus"></i>Neues Schuljahr</h6>
        <button type="button" class="btn-close" onclick="hideModal('modalAddSchuljahr')">×</button>
    </div>
    <div class="modal-body">
        <label class="form-label form-label-sm">Bezeichnung</label>
        <input type="text" class="form-control form-control-sm" id="inp-sj-name" placeholder="z.B. 2025/26" maxlength="20">
    </div>
    <div class="modal-footer py-2">
        <button type="button" class="btn btn-sm btn-secondary" onclick="hideModal('modalAddSchuljahr')">Abbrechen</button>
        <button type="button" class="btn btn-sm btn-primary" id="btn-save-add-sj">Erstellen</button>
    </div>
</dialog>
```

---

## Task 6: Add `openAddSchuljahr()` and `addSchuljahr()` logic

**Files:**
- Modify: `index.html` — class management section (~line 1240), `DOMContentLoaded` listener

**Step 1: Add functions after `deleteClass()` (~line 1272)**

```js
function openAddSchuljahr() {
    document.getElementById('inp-sj-name').value = '';
    showModal('modalAddSchuljahr');
}

function addSchuljahr(name) {
    // Copy classes from active Schuljahr: keep id(new), name, type, students — drop semester data
    const sourceCls = activeClasses();
    const newClasses = sourceCls.map(cls => ({
        id: genId(),
        name: cls.name,
        type: cls.type,
        students: cls.students.map(s => ({ id: genId(), name: s.name })),
        ...newClass(cls.name, cls.type), // gives fresh semester1/semester2/jahresnote
    }));
    // newClass() returns {id,name,type,students,...} — override id/name/type/students:
    const sjId = genId();
    const newSj = {
        id: sjId,
        name: name.trim(),
        classes: sourceCls.map(cls => {
            const fresh = newClass(cls.name, cls.type);
            fresh.students = cls.students.map(s => ({ id: genId(), name: s.name }));
            return fresh;
        })
    };
    data.schuljahre.push(newSj);
    data.activeSchuljahrId = sjId;
    activeClassId = newSj.classes[0]?.id ?? null;
    const initCls = newSj.classes[0];
    activeSaId = initCls?.semester1?.schularbeiten?.[0]?.id ?? null;
    activeTab = 'sa';
    activeSemester = 'semester1';
    saveData();
    render();
}
```

**Step 2: Wire the modal button in `DOMContentLoaded` (after the last existing listener, before the closing `});`)**

```js
document.getElementById('btn-save-add-sj').addEventListener('click', () => {
    const n = document.getElementById('inp-sj-name').value.trim();
    if (!n) return;
    hideModal('modalAddSchuljahr');
    addSchuljahr(n);
});
onEnter('inp-sj-name', 'btn-save-add-sj');
```

**Step 3: Also add the new dialog to the backdrop-click handler in `DOMContentLoaded`** — it uses `document.querySelectorAll('dialog')` so it automatically picks up new dialogs. No change needed.

**Step 4: Manual test — full flow**

1. Open app — see "Importiert" chip, all old data present
2. Click `+` → modal opens
3. Enter "2025/26" → click Erstellen
4. New chip appears and becomes active
5. All classes are present with students, but no grades
6. Switch back to "Importiert" chip → old grades visible
7. Enter a grade in "2025/26" → switch away and back → grade persists

---

## Task 7: Rename "Importiert" to a proper year (optional UX polish)

**Files:**
- Modify: `index.html` — migration in `migrateData()`

If the old data has no `schuljahr` set, the migration names it "Importiert". Change the default name to be more useful:

In Task 1 Step 3, replace `name: 'Importiert'` with:
```js
name: (() => {
    const y = new Date().getFullYear();
    const m = new Date().getMonth(); // 0-indexed
    // Austrian school year: Sept (8) – June (5) next year
    return m >= 8 ? `${y}/${String(y+1).slice(2)}` : `${y-1}/${String(y).slice(2)}`;
})()
```

This gives e.g. "2024/25" automatically for existing data at first migration.

**Step 1: Apply the change, reload, verify the chip shows the correct year instead of "Importiert".**

---

## Verification Checklist

```
[ ] python server.py starts without error
[ ] Existing data loads — classes + grades intact
[ ] Schuljahr chip is shown in sidebar (auto-named by year)
[ ] [+] button opens "Neues Schuljahr" modal
[ ] After creating "2025/26": classes present, students present, no grades
[ ] Switching between school years shows correct grades
[ ] Editing grades in one year does NOT affect the other
[ ] Adding a new class in one year does NOT appear in the other
[ ] Export/import still works (migrateData handles old format)
[ ] No JS errors in browser console
```
