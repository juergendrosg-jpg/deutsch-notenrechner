# Semester Support — Design

**Date:** 2026-04-20
**Status:** Approved

---

## Problem

Each class currently has a single flat set of grades (Schularbeiten, Wiederholungen, etc.). Teachers need two independent semesters per class. Semester 2's Gesamtnote must also include a configurable weight for the Semester 1 overall grade.

---

## Decision

Two symmetric semester objects (`semester1`, `semester2`) nested inside each class. A new `activeSemester` global controls which semester is shown. Semester tabs appear at the top of the main area, above the existing tabs.

---

## Data Model

### Class (after migration)

```js
{
  id, name,
  students: [{id, name}],          // identity only — shared across semesters

  semester1: {
    schularbeiten: [{id, name}],
    wiederholungen: [],
    praesentationen: [],
    hausaufgaben: [],
    gewichtung: { schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20 },
    studentData: {
      [studentId]: {
        schularbeiten:   {},
        wiederholungen:  {},
        praesentationen: {},
        hausaufgaben:    {}
      }
    }
  },

  semester2: {
    schularbeiten: [{id, name}],
    wiederholungen: [],
    praesentationen: [],
    hausaufgaben: [],
    gewichtung: {
      schularbeiten:40, wiederholung:20, praesentation:20, hausaufgaben:20,
      semester1Note: 0    // extra weight field, only in semester2
    },
    studentData: { [studentId]: { ... } }
  }
}
```

### Student (after migration)

Students at class level hold only identity:
```js
{ id, name }
```

All grade data lives in `cls.semester1.studentData[s.id]` and `cls.semester2.studentData[s.id]`.

---

## Migration

`migrateData()` handles existing data:

1. If `cls.semester1` is missing:
   - Move `cls.schularbeiten`, `cls.wiederholungen`, `cls.praesentationen`, `cls.hausaufgaben`, `cls.gewichtung` → `cls.semester1.*`
   - For each student: move `s.schularbeiten`, `s.wiederholungen`, `s.praesentationen`, `s.hausaufgaben` → `cls.semester1.studentData[s.id]`; delete those fields from `s`
   - Initialize `cls.semester2` with empty arrays, default gewichtung (+ `semester1Note:0`), empty studentData
2. Ensure `cls.semester2.gewichtung.semester1Note` exists (default 0) for classes already migrated

---

## UI

### Semester tab bar (new, top of main area)

```
[ 1. Semester ]  [ 2. Semester ]
─────────────────────────────────────────────────
[ Schularbeiten | Wiederholungen | … | Gesamtnote ]
(content of active semester)
```

- New global: `activeSemester = 'semester1'`
- Clicking a semester tab sets `activeSemester` and re-renders the tab content
- `activeTab` and `activeSaId` continue to work within the active semester
- On class switch: `activeSemester` is preserved (user stays in same semester)

### Gesamtnote tab — Semester 2 extras

Weight card shows an additional input:
```
[ Schularbeiten (n× gleichwertig) ]  [ Wiederholung ]  [ Präsentation ]  [ Hausübungen ]  [ 1. Semester ]
```

The Gesamtnote table gets an extra column **"1. Sem."** showing the student's calculated Semester 1 Gesamtnote (read-only, auto-pulled).

---

## Gesamtnote Calculation — Semester 2

```js
function calcGesamtnote(cls, sem, s) {
    // existing components (SA, Wdh, Praes, HA) from sem
    // + one extra component:
    const sem1Note = calcGesamtnote(cls, cls.semester1, s);  // decimal
    components.push({ val: sem1Note, w: +(sem.gewichtung.semester1Note || 0) });
}
```

Null-handling: if a student has no Semester 1 grade, that component is skipped (weight 0 contribution) — same as all other null components.

`calcGesamtnote` gains a `sem` parameter so it works for both semesters.

---

## Functions Changed

| Function | Change |
|---|---|
| `migrateData()` | migrate flat fields → semester1, init semester2 |
| `newClass()` | create with semester1 + semester2 structure |
| `newStudent()` | identity only `{id, name}`, no grade fields |
| `addSA()`, `deleteSA()` | operate on `cls[activeSemester]` |
| `renderMain(cls)` | prepend semester tab bar |
| `renderTabContent()` | pass `sem = cls[activeSemester]` to all render functions |
| `renderTabSA(sem)` | use `sem.schularbeiten`, `sem.studentData` |
| `renderTabWDH(sem)` | use `sem.wiederholungen`, `sem.studentData` |
| `renderTabPraes(sem)` | use `sem.praesentationen`, `sem.studentData` |
| `renderTabHA(sem)` | use `sem.hausaufgaben`, `sem.studentData` |
| `renderTabGesamt(cls, sem)` | semester2: extra weight input + column |
| `calcGesamtnote(cls, sem, s)` | new `sem` param; semester2 adds sem1Note component |
| `updateSAField(sid, saId, field, val)` | write to `cls[activeSemester].studentData[sid]` |
| `updateKommentar(sid, saId, val)` | same |
| `calcWdhTeilnote(sem, sid)` | use `sem.wiederholungen`, `sem.studentData` |
| `calcPraesTeilnote(sem, sid)` | same pattern |
| `calcHATeilnote(sem, sid)` | same pattern |
| `updateGewichtung(key, val)` | write to `cls[activeSemester].gewichtung` |
| `activeSemester` | new global |

---

## Files Changed

- `index.html` only
