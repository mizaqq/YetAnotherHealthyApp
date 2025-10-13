-- ============================================================================
-- migration: create dictionary tables
-- purpose: add shared lookup tables for meal categories and units, including
--          necessary indexes, integrity constraints, and grants. rls will be
--          enabled later.
-- affected objects: tables public.meal_categories, public.unit_definitions,
--                   public.unit_aliases, triggers, indexes, policies.
-- ============================================================================

create table public.meal_categories (
  code text primary key,
  label text not null unique,
  sort_order smallint not null unique check (sort_order > 0),
  created_at timestamptz not null default now()
);

create table public.unit_definitions (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  unit_type text not null,
  grams_per_unit numeric(12, 4) not null check (grams_per_unit > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index unit_definitions_lower_code_key
  on public.unit_definitions (lower(code));

create trigger trg_unit_definitions_set_updated_at
before update on public.unit_definitions
for each row
execute function public.set_updated_at();

create table public.unit_aliases (
  unit_definition_id uuid not null references public.unit_definitions (id) on delete cascade,
  alias text not null,
  locale text not null default 'pl-PL',
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (unit_definition_id, alias, locale),
  check (is_primary = false or alias is not null)
);

create unique index unit_aliases_primary_locale_idx
  on public.unit_aliases (unit_definition_id, locale)
  where is_primary;

grant select on public.meal_categories to authenticated;
grant select on public.unit_definitions to authenticated;
grant select on public.unit_aliases to authenticated;

