# Sidebar Collapse Design

**Date:** 2026-05-03

## Ziel

Die linke Sidebar lässt sich mit einem Pfeil-Button ein- und ausklappen. Im eingeklappten Zustand bleibt ein schmaler Streifen (44px) sichtbar, der Klassen-Icons mit Tooltips zeigt.

## Layout & Animation

- `#sidebar` bekommt `transition: width 0.2s ease`
- Offen: `width: 210px`, geschlossen: `width: 44px`
- `#app-layout` (Flex-Container) braucht keine Änderung

## Toggle-Button

- Neuer `<button id="sidebar-toggle">` wird als erstes Element in `#sidebar` eingefügt
- Icon: `bi-chevron-left` (offen) → `bi-chevron-right` (geschlossen)
- Rechtsbündig im Streifen, immer sichtbar
- Klick ruft `toggleSidebar()` auf

## Collapsed-Zustand

- CSS-Klasse `sidebar-collapsed` wird auf `#sidebar` gesetzt
- Folgende Elemente werden per CSS ausgeblendet (`overflow: hidden; width: 0; opacity: 0`):
  - `#schuljahr-selector`
  - `.sidebar-group-label`
  - `.sidebar-group-head button` (Plus-Buttons)
  - `.sj-class-name` (Klassenname-Text in den Klassen-Items)
  - `#sidebar-footer`
- Klassen-Items werden zentriert auf ein einzelnes Icon reduziert

## Klassen-Icons im collapsed-Zustand

- Jedes Klassen-Item zeigt im collapsed-Zustand ein Icon (z.B. `bi-book`) zentriert
- Das Icon-Element bekommt `title="<Klassenname>"` → nativer Browser-Tooltip
- Klick auf das Icon aktiviert die Klasse wie im normalen Zustand

## State-Persistenz

- Beim Zuklappen: `localStorage.setItem('sidebarCollapsed', '1')`
- Beim Aufklappen: `localStorage.removeItem('sidebarCollapsed')`
- Beim Seitenload: Zustand sofort (ohne Animation, via Klasse vor CSS-Transition) anwenden

## Implementierungsschritte

1. CSS: `#sidebar` Transition + `sidebar-collapsed` Regeln
2. HTML: `#sidebar-toggle` Button in Sidebar einfügen
3. JS: `toggleSidebar()` Funktion + localStorage
4. JS: Seitenload-Initialisierung des Zustands
5. JS/CSS: Klassen-Icons im collapsed-Zustand (in `renderSidebar()`)
