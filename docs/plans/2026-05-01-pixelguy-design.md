# Pixel-Männchen (PixelGuy) — Design

## Überblick

Ein SVG Pixel-Art Männchen das auf der App erscheint, einen witzigen oder liebevollen Spruch in einer Sprechblase zeigt, und nach 10 Sekunden wieder verschwindet. Trigger: Seitenlade (immer) und bestimmte Aktionen (zufällig).

## Charakter-Design

32×32 SVG Pixel-Art, dargestellt mit 4× Zoom (~128×160px sichtbar):
- **Haare:** blonde Pixel-Strähnen
- **Gesicht:** Hautfarbe, kleine Augen, Mund
- **Oberteil:** weißes T-Shirt
- **Hose:** blaue Jeans
- **Schuhe:** braune Birkenstocks (Boston-Style: geschlossene Kappe, breites Band)

## Overlay-System

- `<div id="pixelguy-overlay">` dynamisch in `<body>` eingefügt
- `position: fixed`, `z-index: 9999`
- Zufällige Position bei jedem Erscheinen (innerhalb Viewport mit Rand-Abstand)
- Animation: CSS `fadeIn` beim Erscheinen, `fadeOut` nach 10s → `display: none`

## Sprechblase

- HTML-div mit abgerundetem Rand und Dreieck-Pfeil zum Männchen
- Weißer Hintergrund, dunkler Text
- Position: oben links oder oben rechts vom Männchen (je nach Viewport-Rand)

## Trigger-System

`pixelguy.show(context)` — zeigt Männchen mit zufälligem Spruch aus dem Context-Pool.

| Context | Spruch-Pool (Beispiele) |
|---|---|
| `pageload` | "Guten Morgen, mein Schatz! ☀️", "Ich liebe dich ❤️", "Heute wird ein guter Tag!", "Was wär ich ohne dich?", "Du bist die beste Lehrerin der Welt 😍", diverse Lehrer-Witze |
| `note_1` | "Streber!", "Na, Liebling des Lehrers?", "Perfekt — wie du 😊", "Ein Einser! Fast so gut wie ich 😎" |
| `note_5` | "Hat er/sie das wirklich verdient?", "Autsch…", "Jemand braucht Nachhilfe 😬", "Ist das mit Absicht?" |

Wahrscheinlichkeit: `pageload` = 100%, Aktions-Trigger = ~40% (damit es nicht nervt).

## Integration

- Selbstständiger `<script>`-Block am Ende von `index.html`
- Kein Eingriff in bestehende Logik — bestehende Notenberechnungs-Funktionen werden nach dem `saveData()`-Aufruf mit `pixelguy.maybeShow('note_X')` erweitert
- `pixelguy.show('pageload')` bei `DOMContentLoaded`

## Dateien

| Änderung | Beschreibung |
|---|---|
| `index.html` | Pixel-Guy SVG-Charakter, Overlay-CSS, Trigger-Script am Ende einfügen |
