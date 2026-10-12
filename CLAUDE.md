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
| `server.py` | Flask server — serves `index.html`, `GET/POST /api/data`, plus the in-app update endpoints (`/api/app-info`, `/api/update`, `/api/rollback`) |
| `data.json` | Persistent storage — the entire app state as JSON |
| `mac/` | Mac-App packaging (PyInstaller): `launcher.py`, `notenbuch.spec`, `build_mac.sh`, `ANLEITUNG.txt`, `make_build.py` |

### Auslieferung an die Mac-App (In-App-Updates)

The app runs on the teacher's MacBook as a PyInstaller bundle; data lives in `~/Library/Application Support/Notenbuch/` and never leaves the Mac. The version is `<meta name="app-version">` in `index.html` (also update `<title>` and `#sidebar-version`).

- **Normal release** (only `index.html` changed): bump the version, commit, push, then `gh release create v<X.Y.Z> --title "Notenbuch v<X.Y.Z>" --notes "<what's new, in German, for the teacher>"`. The app checks `releases/latest` on start, downloads `index.html` from `raw.githubusercontent.com/<repo>/<tag>/index.html` and the server stores it in Application Support (backup of `data.json` in `backups/`, previous version kept for rollback). The repo is public, so it must never contain student data.
- **New Mac build** (only when `server.py`/`launcher.py`/spec change, or for first install): `python mac/make_build.py` → `dist-mac/Notenbuch-v<X.Y.Z>.zip`, which is sent to the teacher.
- Local test of the update mode without a Mac: set `NOTENBUCH_APPDIR=<temp dir>` before importing/starting `server.py`.

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

**Schülerprofile** (`data.profile[pid]`): person-level data spanning classes and school years (Gespräche with optional reminder date, Kommentar, Legasthenie, Förderung; Verhalten + Beobachtungen per school year in `jahre[sjId]`). Each class student carries `profilId`; student `id`s are regenerated on every class transfer, so `profilId` is the stable identity. `migrateData()` links students by normalized name (`pfAttach`), never twice in the same class. Profile code lives in the `SCHÜLERPROFILE` section of `index.html` (`pf*` functions).

Semester 2 `gewichtung` contains an extra key `semester1Note` (weight of S1 final grade in S2 calculation).

**Matura** (tab `matura`, only for `oberstufe` classes whose name starts with `8`): `cls.matura = { pruefer, students: { [sid]: { knr, locked, t: [ {m, c}, {m, c} ] } } }` — one SRDP Beurteilungsraster per text. `m` = highlighted cells (`'<row>:<col>'`), `c` = ticked boxes (`inh|struk|k|stil|norm|k3` → column 0–4, note = 5 − column). K1/K2 = `c.k` of text 1/2, K3 = Ø of `c.k3` of both texts, Gesamtnote = Ø K1, K2, K3; any negative Teilnote (K3: Ø ≥ 4,5) forces 5. At exactly x,50 the teacher picks the note manually (`ms.grenz = {ges, note}`, only valid while Ø is unchanged) — see `mrEndnote()`. The tab has two sub-views (`maturaView`: `liste` | `raster`); the printed footer "Gesamtnote:" gets the final note as a word. `ms.tp` = chosen Themenpaket (1–3, not printed). Locking requires every checkbox row ticked in both texts, a Themenpaket, a Kandidatennummer and a decided Grenzfall (`mrMissing()`); printing is only possible for locked students. Raster texts are in `MR_RASTER`; printing (`mrPrint`) renders A4-landscape pages in an iframe that reproduce the official Word form — keep its layout unchanged (legally prescribed). Code lives in the `MATURA` section (`mr*` functions).

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
