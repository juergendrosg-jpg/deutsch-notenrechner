# Online-Version des Notenbuchs – Design

Datum: 2026-11-08 · Status: freigegeben

## Ziel

Das Notenbuch zusätzlich zur Mac-App online nutzbar machen – für 2–3 Personen, jede mit eigenen, getrennten Daten. Die Mac-App der Lehrerin läuft unverändert weiter; ein Rückweg von online zum Mac muss jederzeit möglich sein.

## Entscheidungen

- **Hosting:** Vercel (nur statische Auslieferung von `index.html`, keine Daten).
- **Daten + Login:** Supabase, Region Frankfurt (EU), Gratis-Tarif.
- **Datentrennung:** jede Person sieht nur ihre eigenen Daten (Row Level Security).
- **Mac-App:** bleibt parallel bestehen (`server.py`, Launcher, In-App-Updates unverändert).
- **Datenformat:** online pro Person exakt dasselbe JSON wie `data.json` → Export/Import 1:1 zwischen beiden Welten.

## Architektur

```
Mac-App (wie bisher)                  Online (neu)
index.html ── server.py ── data.json   index.html (Vercel, statisch)
                                          │  supabase-js (Auth + Daten)
                                          ▼
                                       Supabase (Frankfurt)
```

- Ein `index.html` für beide Modi. Moduserkennung beim Start: `location.hostname` ist `localhost`/`127.0.0.1` → **lokal** (bisheriges Verhalten), sonst → **online**.
- Speicherzugriff über eine kleine Abstraktion: `loadData()`/`saveData()` rufen je nach Modus den lokalen Weg (`/api/data`) oder Supabase auf.
- `supabase-js` wird nur im Online-Modus geladen (CDN, exakt gepinnte Version).
- Online wird der Update-Bereich (`upd*`) ausgeblendet; Updates kommen dort per Git-Push.

## Login

- E-Mail + Passwort über Supabase Auth. Selbstregistrierung deaktiviert; Personen werden im Supabase-Dashboard eingeladen.
- Login-Maske vor dem App-Inhalt, wenn keine Sitzung besteht.
- Abmelden-Knopf in der Sidebar (nur online).

## Datenbank

```sql
notenbuch_data (
  user_id    uuid primary key references auth.users,
  data       jsonb not null,
  version    int  not null default 0,   -- für Konfliktschutz
  updated_at timestamptz not null default now()
)

notenbuch_backups (
  id         bigserial primary key,
  user_id    uuid references auth.users,
  data       jsonb not null,
  created_at timestamptz not null default now()
)
```

RLS auf beiden Tabellen: Zugriff nur, wenn `user_id = auth.uid()`.

## Speichern

- Online wird gebündelt gespeichert (Debounce ~1 s nach der letzten Änderung); beim Schließen des Tabs sofort.
- **Konfliktschutz:** Speichern nur, wenn `version` in der DB noch der geladenen entspricht; sonst Warnung („Daten wurden auf einem anderen Gerät geändert – neu laden?“) statt stillem Überschreiben.
- **Fehler:** bei fehlgeschlagenem Speichern deutliche rote Meldung statt des grünen Toasts; automatischer Wiederholversuch.
- Lokaler Modus: Verhalten unverändert.

## Sicherungen, Export, Import

- Online: beim ersten Speichern eines Tages wird der vorherige Stand in `notenbuch_backups` kopiert; ältere als 30 Tage werden entfernt.
- **Export** (beide Modi): lädt die Daten als `notenbuch-JJJJ-MM-TT.json` herunter.
- **Import** (beide Modi): JSON-Datei wählen → Rückfrage → ersetzt die Daten, danach `migrateData()`.

## Auslieferung / GitHub

- Vercel ist mit `juergendrosg-jpg/deutsch-notenrechner` verbunden; Push auf `master` → online nach ~30 s.
- Mac-App weiterhin über `gh release` (siehe CLAUDE.md).
- Supabase-URL und öffentlicher Anon-Key stehen in `index.html` (dafür vorgesehen); der Service-Key kommt nie ins Repo. Das Repo bleibt frei von Schülerdaten.

## Datenschutz (vor Inbetriebnahme)

- Mit Schule/Bildungsdirektion klären, ob Schülerdaten (inkl. Legasthenie/Förderung) in einem Cloud-Dienst verarbeitet werden dürfen.
- Supabase-Projekt in Frankfurt; Auftragsverarbeitungsvertrag (DPA) von Supabase abschließen.
- Vercel erhält keine Schülerdaten.

## Einrichtung durch den Nutzer

1. Datenschutz klären.
2. Konto auf supabase.com, Projekt in Region Frankfurt, SQL (Tabellen + RLS) ausführen, Selbstregistrierung deaktivieren.
3. Konto auf vercel.com, Repo importieren (kein Build-Schritt).
4. Personen in Supabase einladen.
5. Optional: bestehende `data.json` per Import hochladen.

## Bekannte Einschränkungen

- Supabase-Gratisprojekte pausieren nach 1 Woche ohne Nutzung (Daten bleiben, Reaktivierung per Klick im Dashboard).
- Vercel-Gratis-Tarif ist für private, nicht-kommerzielle Nutzung.

## Test-Checkliste (manuell)

- Lokaler Modus: Laden, Speichern, Updates wie bisher.
- Online: Login, Abmelden, Laden, Speichern.
- Zwei Testkonten: keines sieht die Daten des anderen.
- Export online → Import in Mac-App und umgekehrt, Daten identisch.
- Speichern ohne Internet → Fehlermeldung, nach Wiederverbindung gespeichert.
- Zwei Tabs gleichzeitig → Konfliktwarnung.
- Tägliche Sicherung wird angelegt.

## Später

Weitere Tools: je ein eigenes Vercel-Projekt mit eigener Adresse; können dasselbe Supabase-Konto mit eigenen Tabellen nutzen.
