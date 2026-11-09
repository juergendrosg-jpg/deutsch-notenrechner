# Online-Version (Vercel + Supabase) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `index.html` läuft zusätzlich online (Vercel, statisch) mit Login und Datenspeicherung pro Person in Supabase – die Mac-App bleibt unverändert funktionsfähig.

**Architecture:** Ein `index.html`, zwei Speicherwege. `ONLINE` wird aus `location.hostname` abgeleitet; lokal läuft alles wie bisher über `/api/data`, online über `supabase-js` (Auth + eine JSON-Zeile pro Person, RLS). Speichern online gebündelt (Debounce) über eine SQL-Funktion mit Versions-Check und täglicher Sicherung. Design: [2026-11-08-online-hosting-design.md](2026-11-08-online-hosting-design.md).

**Tech Stack:** Vanilla JS in `index.html`, `@supabase/supabase-js@2.45.4` (UMD via jsDelivr), Supabase Postgres + Auth (Frankfurt), Vercel Static Hosting.

**Hinweise für die Umsetzung**
- Es gibt keine Test-Suite. Jede Aufgabe endet mit einer **manuellen Prüfung** (lokal `python server.py` → http://localhost:5000; online-Modus siehe Task 9).
- **Keine Zwischen-Commits** (Wunsch des Users). Commit + Release erst in Task 11, wenn der User die Version freigibt.
- Zeilennummern beziehen sich auf v1.4.1 und verschieben sich – immer per Suche nach dem zitierten Code ansetzen.

---

### Task 1: Datenbank-Schema als SQL-Datei

**Files:**
- Create: `supabase/schema.sql`

**Step 1: Datei anlegen**

```sql
-- Notenbuch – Supabase-Schema. Im Supabase-Dashboard unter "SQL Editor" einmal ausführen.

create table if not exists public.notenbuch_data (
    user_id    uuid primary key references auth.users on delete cascade,
    data       jsonb not null,
    version    int not null default 0,
    updated_at timestamptz not null default now()
);

create table if not exists public.notenbuch_backups (
    id         bigserial primary key,
    user_id    uuid not null references auth.users on delete cascade,
    data       jsonb not null,
    created_at timestamptz not null default now()
);
create index if not exists notenbuch_backups_user on public.notenbuch_backups (user_id, created_at);

alter table public.notenbuch_data    enable row level security;
alter table public.notenbuch_backups enable row level security;

-- Jede Person sieht/ändert nur die eigene Zeile.
create policy "own data" on public.notenbuch_data
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own backups" on public.notenbuch_backups
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Speichern mit Konfliktschutz + täglicher Sicherung (läuft als aufrufende Person → RLS gilt).
-- p_expected = Version, die der Browser geladen hat. Passt sie nicht → Fehler 'conflict'.
create or replace function public.save_notenbuch(p_data jsonb, p_expected int)
returns int language plpgsql security invoker as $$
declare v int;
begin
    -- erster Speichervorgang des Tages: alten Stand sichern
    insert into public.notenbuch_backups (user_id, data)
        select user_id, data from public.notenbuch_data
        where user_id = auth.uid() and version = p_expected
          and updated_at::date < current_date;
    delete from public.notenbuch_backups
        where user_id = auth.uid() and created_at < now() - interval '30 days';

    insert into public.notenbuch_data (user_id, data, version)
        values (auth.uid(), p_data, 1)
    on conflict (user_id) do update
        set data = excluded.data, version = notenbuch_data.version + 1, updated_at = now()
        where notenbuch_data.version = p_expected
    returning version into v;

    if v is null then   -- Zeile existiert, aber mit anderer Version
        raise exception 'conflict' using errcode = 'P0001';
    end if;
    return v;
end $$;
```

Ablauf: Gibt es noch keine Zeile, wird eingefügt (Version 1). Gibt es eine, wird nur aktualisiert, wenn ihre Version der geladenen entspricht. Sonst bleibt `v` leer → Konflikt, und die Transaktion (samt Sicherung) wird zurückgerollt.

**Step 2: Prüfen** – Datei enthält keine Schlüssel oder Daten (wird öffentlich auf GitHub).

---

### Task 2: Vercel-Konfiguration

**Files:**
- Create: `vercel.json`
- Create: `.vercelignore`

**Step 1: `vercel.json`**

```json
{
    "framework": null,
    "buildCommand": "",
    "outputDirectory": ".",
    "cleanUrls": true,
    "headers": [
        { "source": "/(.*)", "headers": [
            { "key": "X-Frame-Options", "value": "DENY" },
            { "key": "Referrer-Policy", "value": "no-referrer" },
            { "key": "Cache-Control", "value": "no-cache" }
        ] }
    ]
}
```

**Step 2: `.vercelignore`** – nur die Seite ausliefern (kein `server.py`, keine Builds, keine `.docx`):

```
*
!index.html
!vercel.json
```

**Step 3: Prüfen** – `git status` zeigt nur die zwei neuen Dateien; `data.json` ist weiterhin per `.gitignore` ausgeschlossen.

---

### Task 3: Modus-Erkennung und Supabase-Konfiguration

**Files:**
- Modify: `index.html` – direkt über `async function loadData()` (Abschnitt „DATEN – Laden / Speichern / Migration“, ca. Z. 1431)

**Step 1: Konstanten + Hilfsfunktionen einfügen**

```js
// ================================================================
// ONLINE-MODUS – lokal (Mac-App) über /api/data, sonst Supabase.
// SB_KEY ist der öffentliche "anon"/"publishable" Key – darf ins Repo.
// ================================================================
const ONLINE = !['localhost', '127.0.0.1'].includes(location.hostname);
const SB_URL = 'https://DEIN-PROJEKT.supabase.co';   // aus Supabase → Project Settings → API
const SB_KEY = 'DEIN-ANON-KEY';
const SB_JS  = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js';
let sb = null;          // Supabase-Client
let sbVersion = 0;      // geladene Version → Konfliktschutz
let sbTimer = null;     // Debounce
let sbSaving = false, sbDirty = false, sbConflict = false;

function loadScript(src) {
    return new Promise((res, rej) => {
        const s = document.createElement('script');
        s.src = src; s.onload = res; s.onerror = () => rej(new Error('Laden fehlgeschlagen: ' + src));
        document.head.appendChild(s);
    });
}

async function sbInit() {
    await loadScript(SB_JS);
    sb = supabase.createClient(SB_URL, SB_KEY, {auth: {detectSessionInUrl: false}});
    const {data: {session}} = await sb.auth.getSession();
    return session;
}
```

`detectSessionInUrl: false`, weil die App `location.hash` fürs Routing nutzt.

**Step 2: Prüfen** – lokal laden, Konsole: `ONLINE` → `false`; Supabase-Script wird nicht geladen (Netzwerk-Tab).

---

### Task 4: Laden und Speichern umstellen

**Files:**
- Modify: `index.html` – `loadData()` und `saveData()` (ca. Z. 1431–1447)

**Step 1: `loadData()` ersetzen**

```js
async function loadData() {
    if (ONLINE) {
        // Fehler werden NICHT verschluckt: ohne Daten darf online nicht gearbeitet werden.
        const {data: row, error} = await sb.from('notenbuch_data').select('data, version').maybeSingle();
        if (error) throw error;
        if (row) { data = row.data; sbVersion = row.version; }
    } else {
        try {
            const r = await fetch('/api/data');
            if (r.ok) data = await r.json();
        } catch(e) { console.error('loadData failed', e); }
    }
    migrateData();
}
```

**Step 2: `saveData()` ersetzen und `sbFlush()` ergänzen**

```js
function saveData() {
    pfCleanup();
    fwAfterChange();
    if (ONLINE) {
        sbDirty = true;
        clearTimeout(sbTimer);
        sbTimer = setTimeout(sbFlush, 1000);
        return;
    }
    fetch('/api/data', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(() => showToast()).catch(e => console.error('saveData failed', e));
}

async function sbFlush() {
    clearTimeout(sbTimer);
    if (sbSaving || sbConflict || !sbDirty) return;
    sbSaving = true; sbDirty = false;
    let res;
    try { res = await sb.rpc('save_notenbuch', {p_data: data, p_expected: sbVersion}); }
    catch(e) { res = {error: e}; }
    sbSaving = false;
    if (res.error) {
        if (res.error.code === 'P0001') { sbConflict = true; sbShowConflict(); return; }
        console.error('sbFlush failed', res.error);
        sbDirty = true;
        showToast('Speichern fehlgeschlagen – neuer Versuch …', true);
        sbTimer = setTimeout(sbFlush, 5000);
        return;
    }
    sbVersion = res.data;
    showToast();
    if (sbDirty) sbFlush();   // während des Speicherns geändert
}

function sbShowConflict() {
    showToast('Nicht gespeichert – Daten wurden anderswo geändert', true);
    if (confirm('Die Daten wurden inzwischen in einem anderen Tab oder auf einem anderen Gerät geändert.\n\n'
        + 'OK = neu laden (deine letzten Änderungen hier gehen verloren)\n'
        + 'Abbrechen = hier bleiben, z. B. um vorher zu exportieren')) location.reload();
}

// Tab wird verlassen → sofort speichern; ungespeichert schließen → Browser fragt nach
document.addEventListener('visibilitychange', () => { if (ONLINE && document.hidden) sbFlush(); });
window.addEventListener('beforeunload', e => {
    if (ONLINE && (sbDirty || sbSaving)) { e.preventDefault(); e.returnValue = ''; }
});
```

**Step 3: Prüfen** – lokal: Note eintragen → grüner Toast „Gespeichert“, `data.json` geändert (Verhalten wie vorher).

---

### Task 5: Fehler-Toast

**Files:**
- Modify: `index.html` – CSS nach `.toast.show { … }` (ca. Z. 484); `showToast()` (ca. Z. 5596)

**Step 1: CSS ergänzen**

```css
.toast.toast-error { background: #fee2e2; color: #b91c1c; border-color: rgba(185,28,28,0.3); }
```

**Step 2: `showToast()` ersetzen** (einziger bisheriger Aufrufer ist `saveData()` ohne Argumente → kompatibel)

```js
function showToast(msg = 'Gespeichert', isError = false) {
    const el = document.getElementById('toast-saved');
    el.querySelector('.toast-body').innerHTML =
        `<i class="bi bi-${isError ? 'exclamation-triangle-fill' : 'check-circle-fill'}"></i> ${esc(msg)}`;
    el.classList.toggle('toast-error', isError);
    el.classList.add('show');
    clearTimeout(showToast.t);
    // Fehler bleiben stehen, bis der nächste Erfolg sie ersetzt
    if (!isError) showToast.t = setTimeout(() => el.classList.remove('show'), 1500);
}
```

**Step 3: Prüfen** – Konsole: `showToast('Test', true)` → rot, bleibt; `showToast()` → grün, verschwindet.

---

### Task 6: Login-Maske, Start-Ablauf, Konto-Knöpfe

**Files:**
- Modify: `index.html` – HTML vor `<!-- ═══ TOAST`; Sidebar nach `#sidebar-footer`; CSS; INIT-Abschnitt (ca. Z. 5709)

**Step 1: Login-HTML** (vor `<!-- ═══ TOAST ═══`)

```html
<!-- ═══ LOGIN (nur online) ═══════════════════════════════════ -->
<div id="login-screen" class="d-none">
    <form class="login-card" onsubmit="sbLogin(event)">
        <h5 class="mb-3">Notenbuch</h5>
        <input type="email" id="login-email" class="form-control mb-2" placeholder="E-Mail" required autocomplete="username">
        <input type="password" id="login-pw" class="form-control mb-2" placeholder="Passwort" required autocomplete="current-password">
        <div id="login-error" class="small mb-2" style="color:#b91c1c"></div>
        <button type="submit" class="btn btn-primary w-100" id="btn-login">Anmelden</button>
    </form>
</div>
```

**Step 2: CSS** (im `@layer components`-Block)

```css
#login-screen { position: fixed; inset: 0; z-index: 2000; display: flex; align-items: center; justify-content: center; background: var(--paper, #faf8f4); }
#login-screen.d-none { display: none; }
.login-card { width: min(340px, calc(100vw - 32px)); padding: 24px; background: #fff; border-radius: var(--r-md, 10px); box-shadow: var(--shadow-lg); }
```

**Step 3: Konto-Knöpfe in die Sidebar** (direkt nach dem schließenden `</div>` von `#sidebar-footer`)

```html
<div id="sidebar-account" class="d-none" style="display:flex; gap:4px; padding: 4px 8px 0;">
    <button type="button" class="btn btn-xs btn-outline-secondary w-50" onclick="sbChangePassword()" title="Passwort ändern"><i class="bi bi-key"></i> Passwort</button>
    <button type="button" class="btn btn-xs btn-outline-secondary w-50" onclick="sbLogout()" title="Abmelden"><i class="bi bi-box-arrow-right"></i> Abmelden</button>
</div>
```

(Falls `.d-none` hier mit dem Inline-`display:flex` kollidiert: `.d-none` ist `!important` – prüfen; sonst Inline-Style in eine Klasse verschieben.)

**Step 4: Start-Ablauf umbauen** – im INIT-Abschnitt

`document.addEventListener('DOMContentLoaded', async () => {` umbenennen zu `async function appStart() {` (Ende `});` → `}`) und Folgendes einfügen:

```js
async function boot() {
    if (ONLINE) {
        let session;
        try { session = await sbInit(); }
        catch(e) { document.body.innerHTML = '<p style="padding:2rem">Verbindung zum Server fehlgeschlagen. Bitte Seite neu laden.</p>'; return; }
        if (!session) { document.getElementById('login-screen').classList.remove('d-none'); return; }
    }
    appStart();
}
document.addEventListener('DOMContentLoaded', boot);

async function sbLogin(ev) {
    ev.preventDefault();
    const btn = document.getElementById('btn-login'), err = document.getElementById('login-error');
    btn.disabled = true; err.textContent = '';
    const {error} = await sb.auth.signInWithPassword({
        email: document.getElementById('login-email').value.trim(),
        password: document.getElementById('login-pw').value
    });
    btn.disabled = false;
    if (error) { err.textContent = 'Anmeldung fehlgeschlagen – E-Mail oder Passwort falsch.'; return; }
    document.getElementById('login-screen').classList.add('d-none');
    appStart();
}

async function sbLogout() {
    await sbFlush();
    if (sbDirty || sbSaving) { alert('Es wird noch gespeichert – bitte kurz warten und erneut versuchen.'); return; }
    await sb.auth.signOut();
    location.reload();
}

async function sbChangePassword() {
    const pw = prompt('Neues Passwort (mindestens 8 Zeichen):');
    if (!pw) return;
    if (pw.length < 8) { alert('Das Passwort ist zu kurz.'); return; }
    const {error} = await sb.auth.updateUser({password: pw});
    alert(error ? 'Fehler: ' + error.message : 'Passwort wurde geändert.');
}
```

**Step 5: Ladefehler online abfangen** – in `appStart()` die erste Zeile `await loadData();` ersetzen durch:

```js
    try { await loadData(); }
    catch(e) {
        console.error(e);
        document.getElementById('content-area').innerHTML =
            '<div class="empty-state"><h5>Daten konnten nicht geladen werden</h5><p>Bitte Seite neu laden.</p></div>';
        return;
    }
    if (ONLINE) {
        document.getElementById('sidebar-account').classList.remove('d-none');
        const v = document.getElementById('sidebar-version');
        v.onclick = null; v.title = 'Online-Version'; v.style.cursor = 'default';
    }
```

**Step 6: Prüfen** – lokal: App startet wie bisher, keine Login-Maske, keine Konto-Knöpfe.

---

### Task 7: Update-Funktion online abschalten

**Files:**
- Modify: `index.html` – `updCheck()` und `updOpen()` (ca. Z. 5620, 5643)

**Step 1:** Als erste Zeile in beide Funktionen:

```js
    if (ONLINE) return;   // online kommen Updates per Git-Push über Vercel
```

**Step 2: Prüfen** – lokal weiterhin: Klick auf Version öffnet den Update-Dialog.

---

### Task 8: Rückfrage beim Import

**Files:**
- Modify: `index.html` – `importData()` (ca. Z. 1870), nach der Prüfung `if (!parsed.classes && !parsed.schuljahre) { … }`

**Step 1:**

```js
        if (!confirm('Alle aktuellen Daten werden durch den Inhalt der Datei ersetzt.\n\nTipp: Vorher „Exportieren“ für eine Sicherung.\n\nFortfahren?')) return;
```

**Step 2: Prüfen** – lokal: Import → Rückfrage; „Abbrechen“ lässt Daten unverändert.

---

### Task 9: Online-Modus lokal testen (vor dem Deployment)

Voraussetzung: Supabase-Projekt existiert (Task 10, Schritte 1–4) und `SB_URL`/`SB_KEY` sind eingetragen.

**Step 1:** Statisch ausliefern unter einem Hostnamen ≠ localhost:

```bash
python -m http.server 8080 --bind 0.0.0.0
```

Aufruf über die LAN-IP, z. B. `http://192.168.x.x:8080/` → `ONLINE === true`.

**Step 2: Checkliste**
- [ ] Login-Maske erscheint; falsches Passwort → Fehlermeldung; richtiges → App.
- [ ] Neue Klasse anlegen → nach ~1 s grüner Toast; Supabase → Table Editor zeigt Zeile, `version` steigt.
- [ ] Seite neu laden → Daten sind da.
- [ ] Zweites Testkonto: sieht leere App, nicht die Daten des ersten.
- [ ] Zwei Tabs, in beiden ändern → im zweiten Konflikt-Dialog.
- [ ] DevTools → Network „Offline“ → ändern → roter Toast; wieder online → grün nach ≤ 5 s.
- [ ] Ändern und sofort Tab schließen → Browser fragt nach.
- [ ] Export online → Datei in Mac-Modus (localhost:5000) importieren → identisch; umgekehrt ebenso.
- [ ] Klick auf Version tut online nichts; Abmelden → Login-Maske.
- [ ] `notenbuch_backups`: nach `update notenbuch_data set updated_at = now() - interval '1 day'` (SQL Editor) und einer Änderung entsteht eine Sicherung.

---

### Task 10: Einrichtungsanleitung für den User

**Files:**
- Create: `docs/ONLINE-EINRICHTUNG.md`

Schritt-für-Schritt auf Deutsch, für Laien:
1. **Supabase**: supabase.com → „Sign in with GitHub“ → New project, Name `notenbuch`, Region **Central EU (Frankfurt)**, sicheres DB-Passwort notieren.
2. **SQL Editor** → Inhalt von `supabase/schema.sql` einfügen → Run.
3. **Authentication → Sign In / Providers**: „Allow new users to sign up“ **aus**; Email-Provider an, „Confirm email“ aus.
4. **Project Settings → API**: Project URL und `anon`/publishable Key in `index.html` (`SB_URL`, `SB_KEY`) eintragen.
5. **Personen anlegen**: Authentication → Users → „Add user → Create new user“ (E-Mail + Startpasswort, „Auto confirm“). Passwort persönlich übergeben; Person ändert es über „Passwort“ in der Sidebar.
6. **Vercel**: vercel.com → „Continue with GitHub“ → Add New → Project → Repo `deutsch-notenrechner` importieren → Framework „Other“ → Deploy. Adresse z. B. `deutsch-notenrechner.vercel.app` (unter Settings → Domains änderbar).
7. **Datenschutz**: Supabase DPA abschließen (Dashboard → Organization → Legal Documents); Freigabe der Schule einholen.
8. **Optional** Daten übernehmen: in der Mac-App „Exportieren“ → online anmelden → „Importieren“.
9. **Hinweis Pause**: Nach 1 Woche ohne Nutzung pausiert Supabase das Projekt → Dashboard → „Restore project“.

---

### Task 11: Version, Doku, Release (erst nach Freigabe durch den User)

**Files:**
- Modify: `index.html` – `<meta name="app-version">`, `<title>`, `#sidebar-version` → `1.5.0`
- Modify: `CLAUDE.md` – Abschnitt „Online-Version“: Modus-Erkennung, `sb*`-Funktionen, `supabase/schema.sql`, Deployment per Push, `SB_KEY` öffentlich / Service-Key nie ins Repo

**Steps (nach „Version fertig“ vom User):**

```bash
git add index.html CLAUDE.md vercel.json .vercelignore supabase/schema.sql docs/
git commit -m "feat: v1.5.0 – Online-Version (Vercel + Supabase) mit Login"
git push
gh release create v1.5.0 --title "Notenbuch v1.5.0" --notes "Import fragt jetzt vor dem Ersetzen der Daten nach. Speicherfehler werden deutlich angezeigt."
```

Danach: Vercel-Deployment öffnen, Checkliste aus Task 9 auf der echten Adresse wiederholen. Mac-App über das Release aktualisieren und prüfen, dass sie lokal unverändert läuft (Speichern, Update-Dialog).
