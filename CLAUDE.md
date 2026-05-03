# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install flask

# Run the development server (http://localhost:5000)
python server.py
```

No build step, no test suite — changes to `index.html` are live on reload.

## Architecture

This is an Austrian school grade management tool ("Deutsch Notenrechner") for a single teacher. It is a **single-page app** with no bundler or framework:

| File | Role |
|---|---|
| `index.html` | Entire frontend: HTML structure, CSS (Tailwind CDN v4 + custom), and all JavaScript (~2000 lines) |
| `server.py` | Minimal Flask server — serves `index.html` and two endpoints: `GET /api/data`, `POST /api/data` |
| `data.json` | Persistent storage — the entire app state as JSON |

### Data model (`data.json`)

```
{ classes: [ {
    id, name,
    students: [ { id, name } ],
    semester1: {
        schularbeiten: [ { id, name } ],
        wiederholungen: [ { id, name, maxPunkte } ],
        praesentationen: [ { id, name } ],
        hausaufgaben: [ { id, name } ],
        gewichtung: { schularbeiten, wiederholung, praesentation, hausaufgaben },
        studentData: {
            [studentId]: {
                schularbeiten: { [saId]: { aufgabenstellung, fehler, wortschatz, textorganisation, kommentar } },
                wiederholungen: { [wid]: <number> },
                praesentationen: { [pid]: <number> },
                hausaufgaben: { [hid]: "0"|"1"|"k" }
            }
        }
    },
    semester2: { ...same structure, gewichtung also has semester1Note }
} ] }
```

Semester 2 `gewichtung` contains an extra key `semester1Note` (weight of S1 final grade in S2 calculation).

### JavaScript architecture (`index.html`, line ~648 onward)

**Global state** (line ~671):
- `data` — in-memory copy of `data.json`
- `activeClassId`, `activeSemester` (`'semester1'|'semester2'`), `activeTab` (`'sa'|'wdh'|'praes'|'ha'|'gesamt'`), `activeSaId`

**Data flow**: Every mutation calls `saveData()` (async POST to `/api/data`) then `render()`.

**Render pipeline**: `render()` → `renderSidebar()` + `renderContent()` → `renderTabContent()` (dispatches to tab-specific render functions).

**Grade calculation** (line ~789):
- `calcSprachrichtigkeit(fehler)` — converts error count to sub-score
- `calcGesamt(sa)` → total points (0–32)
- `calcNote(gesamt)` + `GRADE_TABLE` — maps points to `{note, decimal, borderline}`
- `calcWdhTeilnote`, `calcPraesTeilnote`, `calcHATeilnote` — weighted partial grades
- `calcGesamtnote(cls, sem, student)` — final weighted average; recursively includes S1 result when computing S2

**Migration** (`migrateData()`, line ~697): Runs on every load to upgrade old data shapes (e.g. flat structure → semester1, legacy sa1/sa2 weight keys).

### Styling

Tailwind CDN v4 (`@tailwindcss/browser`) is used for utility classes. Custom component classes (`.btn`, `.grade-table`, `.note-badge`, etc.) are defined in a `<style type="text/tailwindcss">` block using `@layer components`. Bootstrap-compatible helper classes (`.d-flex`, `.d-none`, etc.) are also declared there because some JS-generated HTML uses them.

Note badge color classes: `.note-1` (best) through `.note-5` (worst), `.note-empty`, `.note-borderline`.
