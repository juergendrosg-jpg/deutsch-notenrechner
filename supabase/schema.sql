-- Notenbuch – Supabase-Schema. Im Supabase-Dashboard unter "SQL Editor" einmal ausführen.
-- Enthält weder Schlüssel noch Daten (das Repo ist öffentlich).

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

-- Gezielte Freigabe nur für angemeldete Personen (nötig, wenn
-- "Automatically expose new tables" beim Projekt ausgeschaltet ist).
revoke all on public.notenbuch_data, public.notenbuch_backups from anon;
grant select, insert, update, delete on public.notenbuch_data, public.notenbuch_backups to authenticated;
grant usage, select on sequence public.notenbuch_backups_id_seq to authenticated;

-- Jede Person sieht/ändert nur die eigene Zeile.
drop policy if exists "own data" on public.notenbuch_data;
create policy "own data" on public.notenbuch_data
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());
drop policy if exists "own backups" on public.notenbuch_backups;
create policy "own backups" on public.notenbuch_backups
    for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Speichern mit Konfliktschutz + täglicher Sicherung (läuft als aufrufende Person → RLS gilt).
-- p_expected = Version, die der Browser geladen hat. Passt sie nicht → Fehler 'conflict'
-- und die ganze Transaktion (samt Sicherung) wird zurückgerollt.
create or replace function public.save_notenbuch(p_data jsonb, p_expected int)
returns int language plpgsql security invoker set search_path = public as $$
declare v int;
begin
    -- erster Speichervorgang des Tages: alten Stand sichern
    insert into notenbuch_backups (user_id, data)
        select user_id, data from notenbuch_data
        where user_id = auth.uid() and version = p_expected
          and updated_at::date < current_date;
    delete from notenbuch_backups
        where user_id = auth.uid() and created_at < now() - interval '30 days';

    insert into notenbuch_data (user_id, data, version)
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

revoke execute on function public.save_notenbuch(jsonb, int) from public, anon;
grant execute on function public.save_notenbuch(jsonb, int) to authenticated;
