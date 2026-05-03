# Sidebar Collapse Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Die linke Sidebar lässt sich mit einem Pfeil-Button ein- und ausklappen; im eingeklappten Zustand bleibt ein 44px-Streifen mit Klassen-Icons sichtbar.

**Architecture:** CSS-Klasse `sidebar-collapsed` auf `#sidebar` steuert per Transition width 210px→44px. JS-Funktion `toggleSidebar()` setzt die Klasse und persistiert den Zustand in `localStorage`. `renderSidebar()` wird erweitert, um im collapsed-Zustand Icon-only Klassen-Items zu erzeugen.

**Tech Stack:** Vanilla JS, Tailwind CDN v4, Bootstrap Icons (bereits eingebunden)

---

### Task 1: CSS — Sidebar Transition und collapsed-Styles

**Files:**
- Modify: `index.html` (CSS-Block `<style type="text/tailwindcss">`, Abschnitt `/* Sidebar */` ab Zeile ~440)

**Step 1: Sidebar-Transition und collapsed-Breite hinzufügen**

Im `#sidebar`-Block nach `overflow-y: auto;` ergänzen:

```css
#sidebar {
    width: 210px; flex-shrink: 0;
    background: var(--paper-soft);
    border-right: 1px solid var(--paper-line);
    padding: 18px 12px;
    display: flex; flex-direction: column; gap: 18px;
    overflow-y: auto;
    transition: width 0.2s ease;
    overflow-x: hidden;
}
#sidebar.sidebar-collapsed {
    width: 44px;
    padding: 10px 4px;
    gap: 8px;
}
```

**Step 2: Elemente im collapsed-Zustand verstecken**

Nach dem `#sidebar.sidebar-collapsed`-Block hinzufügen:

```css
#sidebar.sidebar-collapsed #schuljahr-selector,
#sidebar.sidebar-collapsed .sidebar-group-label,
#sidebar.sidebar-collapsed .sidebar-group-head button,
#sidebar.sidebar-collapsed #sidebar-footer,
#sidebar.sidebar-collapsed .class-item-actions,
#sidebar.sidebar-collapsed .fw-semibold {
    display: none;
}
#sidebar.sidebar-collapsed .sidebar-group-head {
    justify-content: center;
}
```

**Step 3: Toggle-Button-Styles hinzufügen**

```css
#sidebar-toggle {
    display: flex; align-items: center; justify-content: flex-end;
    width: 100%; background: none; border: none; cursor: pointer;
    color: var(--ink-mute); padding: 2px 2px 2px 0;
    flex-shrink: 0;
}
#sidebar-toggle:hover { color: var(--rose-500); }
#sidebar.sidebar-collapsed #sidebar-toggle {
    justify-content: center;
}
```

**Step 4: collapsed class-item Styles**

```css
#sidebar.sidebar-collapsed .class-item {
    justify-content: center;
    padding: 8px 4px;
}
#sidebar.sidebar-collapsed .class-item-icon {
    font-size: 16px;
}
.class-item-icon { display: none; }
#sidebar.sidebar-collapsed .class-item-icon { display: inline; }
```

**Step 5: Manuell im Browser testen** — Noch keine JS-Logik, aber Styles können via DevTools durch temporäres Hinzufügen von `sidebar-collapsed` zu `#sidebar` geprüft werden.

**Step 6: Commit**

```
git add index.html
git commit -m "style: add sidebar collapse CSS (transition, collapsed state)"
```

---

### Task 2: HTML — Toggle-Button in Sidebar einfügen

**Files:**
- Modify: `index.html` (HTML-Bereich, `<div id="sidebar">` ab Zeile ~655)

**Step 1: Toggle-Button als erstes Kind von `#sidebar` einfügen**

Direkt nach `<div id="sidebar">` (Zeile 655) einfügen:

```html
<button id="sidebar-toggle" onclick="toggleSidebar()" title="Seitenleiste ein-/ausblenden">
    <i id="sidebar-toggle-icon" class="bi bi-chevron-left"></i>
</button>
```

**Step 2: Commit**

```
git add index.html
git commit -m "feat: add sidebar toggle button to HTML"
```

---

### Task 3: JS — `toggleSidebar()` Funktion

**Files:**
- Modify: `index.html` (JS-Bereich, nach der letzten Funktion vor `</script>`)

**Step 1: Funktion hinzufügen**

Im JS-Block, nach der letzten Funktion (suche nach `// Ende` oder füge vor `</script>` ein):

```javascript
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('sidebar-toggle-icon');
    const collapsed = sidebar.classList.toggle('sidebar-collapsed');
    icon.className = collapsed ? 'bi bi-chevron-right' : 'bi bi-chevron-left';
    if (collapsed) {
        localStorage.setItem('sidebarCollapsed', '1');
    } else {
        localStorage.removeItem('sidebarCollapsed');
    }
}
```

**Step 2: Initialisierung beim Seitenload**

Beim Seitenload soll der gespeicherte Zustand sofort (ohne Animation) angewendet werden. Suche die Stelle wo `render()` oder `migrateData()` initial aufgerufen wird (vermutlich ganz unten im `<script>`-Block, etwas wie `migrateData(); render();`).

Direkt **vor** diesem Aufruf einfügen:

```javascript
// Sidebar-Zustand vor erstem Render setzen (ohne Animation)
(function() {
    if (localStorage.getItem('sidebarCollapsed') === '1') {
        const sidebar = document.getElementById('sidebar');
        const icon = document.getElementById('sidebar-toggle-icon');
        sidebar.style.transition = 'none';
        sidebar.classList.add('sidebar-collapsed');
        if (icon) icon.className = 'bi bi-chevron-right';
        requestAnimationFrame(() => { sidebar.style.transition = ''; });
    }
})();
```

**Step 3: Manuell im Browser testen**
- Seite laden → Sidebar offen, Pfeil zeigt links
- Button klicken → Sidebar klappt auf 44px zusammen, Pfeil dreht sich
- Seite neu laden → Zustand bleibt erhalten

**Step 4: Commit**

```
git add index.html
git commit -m "feat: implement toggleSidebar with localStorage persistence"
```

---

### Task 4: JS — Klassen-Icons in `renderSidebar()` ergänzen

**Files:**
- Modify: `index.html` (JS-Funktion `renderSidebar()` ab Zeile ~1802)

**Step 1: `classItem`-Template um Icon erweitern**

Das bestehende `classItem`-Template (Zeile ~1806) sieht so aus:

```javascript
const classItem = cls => `
    <div class="class-item ${cls.id===activeClassId?'active':''}" data-id="${cls.id}" onclick="selectClass('${cls.id}')">
        <div class="fw-semibold">${esc(cls.name)}</div>
        <div class="class-item-actions">
            ...
        </div>
    </div>`;
```

Ein Icon-Element hinzufügen — **nach** `<div class="fw-semibold">` und **vor** `<div class="class-item-actions">`:

```javascript
const classItem = cls => `
    <div class="class-item ${cls.id===activeClassId?'active':''}" data-id="${cls.id}" onclick="selectClass('${cls.id}')" title="${esc(cls.name)}">
        <i class="class-item-icon bi bi-book" aria-hidden="true"></i>
        <div class="fw-semibold">${esc(cls.name)}</div>
        <div class="class-item-actions">
            <button class="btn btn-xs btn-outline-secondary" onclick="event.stopPropagation();openEditClass('${cls.id}')" title="Umbenennen"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-xs btn-outline-danger" onclick="event.stopPropagation();openDeleteClass('${cls.id}')" title="Löschen"><i class="bi bi-trash"></i></button>
        </div>
    </div>`;
```

Wichtig: `title="${esc(cls.name)}"` auf dem Wrapper-`div` ermöglicht den Browser-Tooltip im collapsed-Zustand.

**Step 2: Manuell im Browser testen**
- Sidebar aufklappen → normale Ansicht, kein sichtbares Icon-Element
- Sidebar zuklappen → Klassen-Icons erscheinen zentriert
- Hover über Icon → Tooltip mit Klassenname erscheint
- Klick auf Icon → Klasse wird aktiviert wie gewohnt

**Step 3: Commit**

```
git add index.html
git commit -m "feat: show class icons in collapsed sidebar with tooltip"
```

---

## Abschluss-Checkliste

- [ ] Sidebar öffnet/schließt mit Animation
- [ ] Pfeil dreht sich beim Toggle
- [ ] Zustand überlebt Seiten-Reload
- [ ] Klassen-Icons im collapsed-Zustand sichtbar, zentriert
- [ ] Tooltip mit Klassenname bei Hover
- [ ] Klick auf Icon aktiviert Klasse
- [ ] Kein Overflow / kein abgeschnittener Inhalt bei Animation
