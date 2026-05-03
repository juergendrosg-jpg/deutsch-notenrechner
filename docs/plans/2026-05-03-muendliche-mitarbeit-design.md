# Design: Tab "Mündliche Mitarbeit"

**Date:** 2026-05-03  
**Status:** Approved

## Summary

Add a new "Mündliche Mitarbeit" tab (for both Oberstufe and Unterstufe) with one Note (1–5) + Kommentar per student per semester, included in the Gesamtnote with its own configurable weight.

## Data Model

### `studentData[sid].muendlicheMitarbeit`
New field on every studentData entry in both semesters:
```json
{ "note": null, "kommentar": "" }
```

### `sem.gewichtung.muendlich`
New weight key, default `0`, so existing data is unaffected and the weight-sum warning stays correct.

### Migration (`migrateData()`)
For every class/semester/studentData entry:
- If `muendlicheMitarbeit` is missing → set to `{ note: null, kommentar: '' }`
- If `gewichtung.muendlich` is missing → set to `0`

## Tab

- Tab key: `'mm'`
- Label: "Mündl. Mitarbeit", icon `bi-chat-dots`
- Position: between Hausübungen and Gesamtnote in the tab bar
- Layout: simple table — **Name | Note (Dropdown 1–5) | Kommentar**
- Identical for Oberstufe and Unterstufe (no branching)
- No add/edit/delete of entries — just one row per student

## Gesamtnote

- New component in `calcGesamtnote()`: `{ val: muendlicheNote, w: g.muendlich }`
- New column "Mündl." in the Gesamtnote table (between HÜ and Wunschpr.)
- New `weightInput('muendlich', 'Mündl. Mitarbeit', g.muendlich)` in the weight card
- `totalW` in `renderTabGesamt` already sums all gewichtung values, so the warning updates automatically

## Functions to add/change

| Function | Change |
|---|---|
| `migrateData()` | Add muendlicheMitarbeit + gewichtung.muendlich migration |
| `newClass()` | Include `muendlich: 0` in default gewichtung |
| `getSData()` | Include `muendlicheMitarbeit` in default studentData shape |
| `calcGesamtnote()` | Add muendlich component |
| `renderContent()` | Add 'mm' tab link |
| `renderTabContent()` | Add 'mm' case |
| `renderTabGesamt()` | Add muendlich weight input + column |
| `renderTabMM()` | New function — renders the tab |
| `attachMMListeners()` | New function — wires up dropdowns + textareas |
| `updateMMNote()` | New function — saves note |
| `updateMMKommentar()` | New function — saves kommentar |
| `calcMMTeilnote()` | New function — returns note (1–5) or null |
