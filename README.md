# Handoff: Notenbuch Redesign

## Übersicht

Das **Notenbuch** ist ein internes Tool zum Eintragen und Verwalten von Schulnoten einer Deutschklasse. Dieses Handoff-Paket beschreibt das überarbeitete Design — modern, akademisch warm, mit zarten Rosa-Akzenten — und liefert alle Werte, Komponenten und Verhalten, die für die Umsetzung im bestehenden Code nötig sind.

## Über die Design-Dateien

Die HTML/CSS/JSX-Dateien in diesem Paket sind **Design-Referenzen** — Prototypen, die das angestrebte Aussehen und Verhalten zeigen. Sie sind **nicht** dazu gedacht, 1:1 in Produktion übernommen zu werden.

Die Aufgabe ist, dieses Design im bestehenden Notenbuch-Codebase nachzubauen — mit den dort bereits etablierten Patterns, Komponenten-Bibliotheken und Frameworks. Wenn der Code z. B. React + Tailwind nutzt, sollen die Tokens und Layouts in dieses System übersetzt werden.

## Fidelity

**Hi-Fi.** Farben, Typografie, Spacing, Radien und Interaktionen sind final und sollen pixelgenau nachgebaut werden.

## Bildschirme / Views

Es gibt aktuell **eine Hauptansicht** mit zwei Hauptbereichen:

### 1. Klassenübersicht (oben)

- **Zweck**: Alle Klassen sehen, gruppiert nach Schulstufe; eine auswählen, um deren Noten zu bearbeiten
- **Layout**:
  - Vertikal gestapelt: pro Stufe (Unterstufe, Oberstufe) eine eigene Sektion
  - Pro Sektion: Sektions-Überschrift links + "Klasse hinzufügen"-Button rechts
  - Darunter: CSS-Grid mit Klassen-Karten, `repeat(auto-fit, minmax(280px, 1fr))`, Gap 14px
- **Klassen-Karte**:
  - Padding: 14px 16px; Radius: 10px; Background: #fff; Border: 1px solid `--paper-line`
  - Inhalt:
    - Eyebrow oben: Stufe (Unterstufe/Oberstufe), Caps, 12px, ink-mute
    - Klassenname (z. B. "3A"): Lora 600, 22px, ink
    - Untere Zeile: Users-Icon + "{N} Schüler/innen", 12px, ink-mute
  - Hover: Border → rose-200, leichte Anhebung (translateY(-1px)), shadow-md
  - Active (ausgewählt): Background rose-50, Border rose-300

### 2. Aktiver Klassen-Block (darunter)

Erscheint sofort und reagiert auf die in der Übersicht gewählte Klasse.

- **Karten-Container**: weiß, Radius 10px, Border 1px `--paper-line`, shadow-sm
- **Header-Zeile**:
  - Background: `--paper-soft`
  - Klassenname (Lora 600, 17px) + Sub-Info "{N} Schüler/innen · {Stufe}" (12px, ink-mute)
  - Badge "aktiv" (Pill, rose-50/rose-500), Spacer, Buttons "Bearbeiten" und "Schüler/innen"
- **Semester-Tabs** (drei): "1. Semester", "2. Semester", "Jahresnote"
  - Container: weiß, Border-bottom `--paper-line`, Padding 12px 14px
  - Tab: Pill-Button, Padding 7px 14px, Radius 999px, 13px, weight 500
  - Inaktiv: text ink-mute, Background transparent
  - Hover: Background `--paper-soft`, text ink-soft
  - Aktiv: text rose-500, Background rose-50
- **Notenbestandteil-Tabs** (fünf): Schularbeiten, Wiederholungen, Präsentationen, Hausübungen, Gesamtnote
  - Container: Background `--paper-soft`, Padding 12px 18px, Border-bottom
  - Tab: Padding 7px 12px, Radius 6px, mit Icon (14px) + Label (12.5px)
  - Inaktiv: transparent, ink-mute; Icon in rose-400
  - Hover: weißlicher Hintergrund (`rgba(255,255,255,0.6)`)
  - Aktiv: Background #fff, Border 1px paper-line, shadow-sm; Icon rose-500
- **Sub-Tabs** (nur bei Schularbeiten): "1. Schularbeit", "2. Schularbeit"
  - Klassisches "Folder-Tab"-Pattern, Radius oben 6px
- **Notentabelle**:
  - Spalten: Name | Aufgabenstellung (0–8) | Fehler (≤3 → −1 Pkt) | Sprachrichtigkeit (auto*) | Wortschatz (0–8) | Textorganisation (0–8) | Gesamt (max 32) | Note | Dezimal | Kommentar
  - Header: 11.5px, uppercase, letter-spacing 0.04em, ink-mute, mit kleinerer Sub-Beschriftung darunter
  - Zellen: 13px, padding 10px 14px, border-bottom paper-line
  - Zeilen-Hover: Background rose-50
  - Number-Inputs: 48px breit, mono, zentrierter Text, Radius 6px
  - Auto-Inputs (Sprachrichtigkeit): readonly, Background paper-soft, kein Border
  - Note-Badge: 32×32 Kreis, Lora 600 14px, Pastellton je nach Note (siehe Tokens)
  - Dezimal: mono 13px
  - Kommentar-Input: full-width, italic placeholder
- **Footer der Tabelle**: Hinweise + "Gespeichert"-Indikator (kleiner grüner Dot + kursiv)

## Interaktionen & Verhalten

- **Klassenkarte klicken** → Wählt die Klasse aus; der Klassen-Block darunter zeigt deren Daten
- **Klasse hinzufügen** (pro Stufe separat): öffnet Dialog mit stufenspezifischen Optionen (Unterstufe und Oberstufe haben unterschiedliche Notenraster, Schularbeiten-Anzahl etc.)
- **Semester-Tab wechseln**: andere Notenmenge anzeigen (1. Sem, 2. Sem, Jahresnote)
- **Notenbestandteil-Tab wechseln**: andere Tabellen-Konfiguration anzeigen
- **Schularbeiten**: Sub-Tabs für 1./2. Schularbeit
- **Number-Input ändern**:
  - Sofort lokal anwenden, im Hintergrund speichern
  - "Sprachrichtigkeit" wird automatisch aus Fehlern berechnet (readonly)
  - "Gesamt" wird live aus den Spalten neu berechnet
  - "Note" und "Dezimal" werden aus Gesamt-Punkten abgeleitet
- **Speicher-Indikator**: rechts unten "Gespeichert" mit grünem Dot, sobald Backend bestätigt
- **Hover-Zeile**: rose-50 als sehr dezenter Hover-Hint
- **Focus-Rings**: rose-300 Border + rose-50 Glow (3px) auf allen Inputs

## State Management

- `activeKlasseId` (string)
- `activeSemester` (1 | 2 | 'jahr')
- `activePart` ('sa' | 'wh' | 'pr' | 'hu' | 'ges')
- `activeSchularbeit` (0 | 1, nur bei sa)
- `klassen` (Liste, gruppiert nach Stufe)
- `noten` (pro Klasse × Semester × Part × Schüler:in)
- `savingState` (idle | saving | saved | error) für den Speicher-Indikator

## Design Tokens

### Farben

| Token | Wert | Verwendung |
|---|---|---|
| `--paper` | `#faf7f2` | Haupt-Hintergrund (Papierton) |
| `--paper-soft` | `#f4efe6` | Subtiler Sekundär-Hintergrund |
| `--paper-line` | `#ece5d8` | Trennlinien, Borders |
| `--ink` | `#2a2a36` | Text primär, primärer Button-Bg |
| `--ink-soft` | `#4a4a5a` | Text sekundär |
| `--ink-mute` | `#8a8898` | Meta-Text, Labels |
| `--ink-faint` | `#c9c5d3` | Disabled, Sub-Beschriftungen |
| `--rose-50` | `#fdf5f6` | Aktiv-Hintergrund Tab/Karte |
| `--rose-100` | `#f9e6ea` | Pill-Bg, leichter Akzent |
| `--rose-200` | `#f3cdd5` | Hover-Border, Note 5 |
| `--rose-300` | `#e9aab7` | Focus-Border, Active-Border |
| `--rose-400` | `#dc8294` | Icons aktiv |
| `--rose-500` | `#c95f76` | Pill-Text, aktiver Tab-Text |
| `--leaf-500` | `#6b8a5e` | Grüner "Gespeichert"-Dot |

### Notenfarben (Pastell)

| Note | Background | Foreground |
|---|---|---|
| 1 | `#d4e0cc` | `#4a6440` |
| 2 | `#e3e0c2` | `#6a6230` |
| 3 | `#f0e4b8` | `#8a7430` |
| 4 | `#f0d4b8` | `#8a5a30` |
| 5 | `#f3cdd5` | `#8a3a4a` |

### Spacing & Radius

- Radius: `--r-sm: 6px`, `--r-md: 10px`, `--r-lg: 16px`
- Pill: `999px`
- Zell-Padding Tabelle: `10px 14px`
- Standard-Card-Padding: `14px 16px`
- Section-Gap: `22px`

### Schatten

- `shadow-sm`: `0 1px 2px rgba(42,42,54,0.04)`
- `shadow-md`: `0 2px 8px rgba(42,42,54,0.06), 0 1px 2px rgba(42,42,54,0.04)`
- `shadow-lg`: `0 8px 24px rgba(42,42,54,0.08), 0 2px 6px rgba(42,42,54,0.04)`

### Typografie

- **Serif** (Überschriften, Klassennamen, Notenbadge): `Lora` (Google Font), Fallback `Iowan Old Style, Georgia, serif`
- **Sans** (UI, Body): `Inter`, Fallback `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Mono** (Zahlen, Inputs): `JetBrains Mono`, Fallback `ui-monospace, 'SF Mono', monospace`

Google-Fonts-Import:
```html
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Größen-Übersicht:
- Page Title (Lora 600): 22px
- Card Title (Lora 600): 17px (Block-Header), 22px (Klassen-Karte)
- Section Title (Lora 500, uppercase, letter-spacing 0.06em): 14px
- Body / UI: 13–14px
- Tab labels: 12.5–13px
- Meta / Caps: 11–12px
- Note-Badge: 14px
- Tabellen-Header: 11.5px uppercase

## Assets

- **Logo** (`pixel-header.jsx → NotenbuchLogo`): Inline-SVG, 52×44 viewBox. Ein lineares Notizheft mit Bindung und 5 dünnen Hilfslinien plus ein rosa Bleistift, der über die obere rechte Ecke greift. Strokes 1.2–1.4px, Stroke-Color `--ink`. Bleistift-Body in `--rose-200`.
- **Icons**: Lucide-Stil, inline SVG (siehe `shared-grades.jsx → TabIcon`). Stroke 2px, currentColor. Verwendete Icons: `check-square`, `repeat`, `mic`, `edit`, `award`, `plus`, `users`, `edit2`, `moon`, `settings`.

Falls in eurem Codebase bereits eine Icon-Library wie `lucide-react` benutzt wird, sollten dieselben Icons von dort verwendet werden — die Mapping ist 1:1.

## Dateien in diesem Paket

- `Notenbuch Design.html` — Einstiegspunkt
- `styles.css` — Alle Design-Tokens und Komponenten-Styles. **Hauptreferenz.**
- `pixel-header.jsx` — Logo-SVG (`NotenbuchLogo`) + Header-Komponente
- `shared-grades.jsx` — `TabIcon`, `PartTabs`, `SemesterTabs`, `SubTabs`, `GradesTable`, sowie Sample-Daten (`SCHUELER`, `NOTEN_PARTS`)
- `variants.jsx` — `VariantA` als Komposition aller Teile (Hauptansicht)

## Hinweise zur Umsetzung

1. **Tokens zuerst**: Übernehmt die `:root`-Custom-Properties aus `styles.css` 1:1 in eure Token-Datei. Alles andere baut darauf auf.
2. **Schriftarten** müssen geladen sein, sonst kippt die Hierarchie (Lora ist namensgebend für den akademischen Charakter).
3. **Unterstufe vs. Oberstufe** sind UI-strukturell gleich, aber inhaltlich getrennt: zwei Sektionen, eigener "Hinzufügen"-Button, später ggf. eigenes Notenraster.
4. **Tab-Stile** sind drei verschiedene Patterns (Pills für Semester, Card-Tabs für Bestandteile, Folder-Tabs für Schularbeiten) — bitte alle drei beibehalten, sie sortieren die Hierarchie.
5. **Keine Pixelgrafiken, keine Margeriten** — frühere Iterationen hatten beides; die finale Version ist absichtlich reduziert.
6. **Hover/Active**: rose-50 ist der Standard-Subtle-Hover; nichts darüber hinaus.
