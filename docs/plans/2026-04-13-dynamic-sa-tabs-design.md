# Dynamic Schularbeit Tabs — Design

**Date:** 2026-04-13
**Status:** Approved

---

## Problem

The current app has exactly two fixed Schularbeiten (`schularbeit1`, `schularbeit2`) per student. Teachers may need 1, 2, 3 or more Schularbeiten per class. The number should be flexible, browser-tab-style.

---

## Decision

Dynamic SA sub-tabs inside the "Schularbeiten" main tab. Start with 1 SA. Add unlimited SAs via "+". Delete with double confirmation.

---

## Data Model

### Class

```js
// BEFORE
gewichtung: { sa1: 20, sa2: 20, wiederholung: 20, praesentation: 20, hausaufgaben: 20 }

// AFTER
schularbeiten: [
  { id: "abc1", name: "1. Schularbeit" },
  { id: "abc2", name: "2. Schularbeit" }
]
gewichtung: { schularbeiten: 40, wiederholung: 20, praesentation: 20, hausaufgaben: 20 }
```

### Student

```js
// BEFORE
schularbeit1: { aufgabenstellung, fehler, wortschatz, textorganisation }
schularbeit2: { aufgabenstellung, fehler, wortschatz, textorganisation }
kommentar1: ''
kommentar2: ''

// AFTER
schularbeiten: {
  "abc1": { aufgabenstellung: null, fehler: null, wortschatz: null, textorganisation: null, kommentar: '' },
  "abc2": { ... }
}
```

### New student default

```js
{ id, name, schularbeiten: {}, wiederholungen: {}, praesentationen: {}, hausaufgaben: {} }
```

---

## UI

### Tab bar inside "Schularbeiten" section

```
[ 1. Schularbeit ×]  [ 2. Schularbeit ×]  [+]
┌────────────────────────────────────────────────┐
│  Standard SA-Tabelle für die aktive SA         │
│  (Aufgabenstellung / Fehler / Sprachrichtigkeit│
│   / Wortschatz / Textorganisation / Gesamt /   │
│   Note / Kommentar)                            │
└────────────────────────────────────────────────┘
```

- `[+]` adds a new SA (`n. Schularbeit`) and activates it
- `[×]` on each tab: first click shows inline "Sicher?" state, second click deletes
- Deleting the active tab activates the nearest remaining tab
- Deleting the last SA is not allowed (minimum 1)
- New class: 1 SA created by default

### State

A new JS variable `activeSaId` tracks the currently active SA tab (similar to `activeTab`).

---

## Gesamtnote Calculation

`gewichtung.schularbeiten` (e.g. 40%) is divided equally among all SAs:

```
weight_per_sa = gewichtung.schularbeiten / cls.schularbeiten.length
```

For each student, each SA's decimal grade (from GRADE_TABLE) is averaged with equal weight.

If a student has no grade for an SA, that SA is skipped (same null-handling as Wiederholungen).

---

## Migration

`migrateData()` handles existing data:

1. If `cls.schularbeiten` is missing: create it from `gewichtung.sa1` / `gewichtung.sa2`
   - If both exist: `[{id:'sa1-legacy', name:'1. Schularbeit'}, {id:'sa2-legacy', name:'2. Schularbeit'}]`
   - If only `sa1`: `[{id:'sa1-legacy', name:'1. Schularbeit'}]`
2. Migrate `gewichtung`: `schularbeiten = (sa1||0) + (sa2||0)`, delete `sa1` and `sa2`
3. For each student:
   - Convert `schularbeit1` → `schularbeiten['sa1-legacy']` (copy all fields + kommentar1)
   - Convert `schularbeit2` → `schularbeiten['sa2-legacy']` (copy all fields + kommentar2)
   - Delete old fields

---

## Files Changed

- `index.html` only (all logic is inline)

### Functions to add/change

| Function | Change |
|---|---|
| `newClass()` | add `schularbeiten: [{id, name:'1. Schularbeit'}]` |
| `newStudent()` | replace fixed SA fields with `schularbeiten: {}` |
| `migrateData()` | migrate old `schularbeit1/2`, `kommentar1/2`, `gewichtung.sa1/sa2` |
| `renderTabSA(cls)` | render sub-tab bar + active SA table |
| `renderSARow(s, saId)` | render one row for a specific SA |
| `attachSAListeners()` | attach input/textarea listeners for active SA |
| `updateSACells(cls, s, saId)` | update computed cells for specific SA |
| `updateSAField()` | write to `s.schularbeiten[saId][field]` |
| `updateKommentar()` | write to `s.schularbeiten[saId].kommentar` |
| `calcGesamtnote()` | use equal-weight average over all SAs |
| weight card in Gesamtnote tab | show single `schularbeiten` weight input |
| `activeSaId` | new global state variable |
| add/delete SA functions | `addSA(cls)`, `deleteSA(cls, saId)` |
