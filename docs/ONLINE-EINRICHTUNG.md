# Notenbuch online – Einrichtung

Diese Anleitung führt Schritt für Schritt durch die Einrichtung. Du brauchst nur deinen GitHub-Zugang. Die Bezeichnungen in den Dashboards können sich leicht ändern; im Zweifel nach dem fett gedruckten Begriff suchen.

**Reihenfolge:** Teil A (Supabase) → Werte an Claude geben → gemeinsamer Test → Version freigeben (Commit + Push) → Teil B (Vercel) → Teil C (Personen anlegen).

---

## Teil A – Supabase (Datenbank + Login)

1. **supabase.com** öffnen → **Start your project** → **Continue with GitHub**.
2. **New project**:
   - Name: `notenbuch`
   - Database Password: auf **Generate a password** klicken und das Passwort sicher aufheben (wird im Alltag nicht gebraucht)
   - Region: **Central EU (Frankfurt)**, wichtig für den Datenschutz
   - Plan: **Free**
   → **Create new project** und 1–2 Minuten warten.
3. Links **SQL Editor** → **New query** → den kompletten Inhalt der Datei `supabase/schema.sql` aus dem Projektordner hineinkopieren → **Run**. Es sollte „Success. No rows returned“ erscheinen.
4. Links **Authentication** → **Sign In / Providers** (oder **Settings**):
   - **Allow new users to sign up**: **aus**. Dann kann sich niemand selbst registrieren.
   - Unter **Email**: aktiviert lassen, **Confirm email**: **aus**.
   → Speichern.
5. Zwei Werte notieren:
   - **Project URL**, z. B. `https://abcdefgh.supabase.co`: in der Projekt-Übersicht oben auf **Connect** klicken, oder **Project Settings → Data API**. Notfalls aus der Browser-Adresszeile: `supabase.com/dashboard/project/abcdefgh…` → `https://abcdefgh.supabase.co`.
   - **Schlüssel:** **Project Settings → API Keys** → Reiter **Legacy API Keys** → **anon · public** (beginnt mit `eyJ…`). Falls es den Reiter nicht gibt: den **Publishable key** (`sb_publishable_…`).
   → Beide Werte an Claude geben; Claude trägt sie in `index.html` ein.
   ⚠️ **Niemals** den Schlüssel **service_role** bzw. **secret** weitergeben oder ins Repo stellen.
6. **Zwei Test-Personen anlegen** für den gemeinsamen Test: **Authentication → Users → Add user → Create new user**, E-Mail + Passwort eingeben, Häkchen **Auto Confirm User** → **Create user**.
7. **Datenschutzvertrag (DPA):** in Supabase unter **Organization → Settings → Legal Documents** (bzw. „DPA“) den Auftragsverarbeitungsvertrag abrufen bzw. abschließen und aufbewahren.

---

## Teil B – Vercel (Webseite)

Erst wenn die neue Version auf GitHub ist (Claude macht den Push nach deiner Freigabe).

1. **vercel.com** öffnen → **Sign Up** → Plan **Hobby** → **Continue with GitHub**.
2. **Add New… → Project** → beim Repository `deutsch-notenrechner` auf **Import** klicken. Falls es nicht in der Liste steht: **Adjust GitHub App Permissions** und dem Repo Zugriff geben.
3. Einstellungen:
   - Framework Preset: **Other**
   - alles andere so lassen
   → **Deploy**.
4. Nach ca. 30 Sekunden ist die Seite online, z. B. unter `deutsch-notenrechner.vercel.app`. Eine andere Adresse kannst du unter **Settings → Domains** einstellen, z. B. `notenbuch-drosg.vercel.app`.

Ab jetzt geht jede neue Version automatisch online, sobald sie auf GitHub gepusht wird.

---

## Teil C – Personen einladen

Für jede Person: **Supabase → Authentication → Users → Add user → Create new user** → E-Mail, Startpasswort, **Auto Confirm User** → **Create user**.

Adresse und Startpasswort persönlich weitergeben. Nach dem ersten Login ändert die Person ihr Passwort in der Sidebar unter **Passwort**.

**Passwort vergessen:** Die Person **nicht löschen**, sonst sind auch ihre Daten weg. Stattdessen im **SQL Editor** ausführen (E-Mail und neues Passwort anpassen):

```sql
update auth.users
set encrypted_password = crypt('NeuesPasswort123', gen_salt('bf'))
where email = 'person@example.at';
```

Danach das neue Passwort weitergeben; die Person ändert es beim nächsten Login wieder.

---

## Alltag

- **Daten von der Mac-App übernehmen:** in der Mac-App **Exportieren** → online anmelden → **Importieren** → Datei wählen.
- **Zurück zur Mac-App:** online **Exportieren** → in der Mac-App **Importieren**.
- **Sicherungen:** Online wird täglich automatisch eine Sicherung angelegt (30 Tage). Zusätzlich hin und wieder **Exportieren**, z. B. am Semesterende.
- **Pause nach 1 Woche:** Supabase pausiert Gratis-Projekte, die eine Woche lang nicht benutzt werden, z. B. in den Ferien. Die Daten bleiben erhalten. Dann zeigt das Notenbuch „Verbindung zum Server fehlgeschlagen“ oder „Daten konnten nicht geladen werden“ → supabase.com → Projekt öffnen → **Restore project** → ein paar Minuten warten.
- **Roter Hinweis „Speichern fehlgeschlagen“:** meist kein Internet. Das Notenbuch versucht es automatisch weiter. Den Tab nicht schließen, solange der Hinweis rot ist.
- **Hinweis „Daten wurden anderswo geändert“:** Das Notenbuch war in zwei Tabs oder auf zwei Geräten offen. Neu laden übernimmt den neueren Stand.
