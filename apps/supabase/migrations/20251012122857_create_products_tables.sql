-- ============================================================================
-- migration: create products and portions tables
-- purpose: register canonical food products and their standard portions with
--          auditing, indexes, and grants. rls will be configured later.
-- affected objects: tables public.products, public.product_portions, related
--                   indexes and triggers, rls policies, grants.
-- ============================================================================

create table public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  off_id text unique,
  macros_per_100g jsonb not null check (
    macros_per_100g ? 'calories'
    and macros_per_100g ? 'protein'
    and macros_per_100g ? 'fat'
    and macros_per_100g ? 'carbs'
  ),
  source text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index products_lower_name_key
  on public.products (lower(name));

create trigger trg_products_set_updated_at
before update on public.products
for each row
execute function public.set_updated_at();

create table public.product_portions (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products (id) on delete cascade,
  unit_definition_id uuid not null references public.unit_definitions (id) on delete cascade,
  grams_per_portion numeric(12, 4) not null check (grams_per_portion > 0),
  is_default boolean not null default false,
  source text,
  created_at timestamptz not null default now(),
  unique (product_id, unit_definition_id),
  check (is_default = false or is_default is not null)
);

create unique index product_portions_default_idx
  on public.product_portions (product_id)
  where is_default;

grant select on public.products to authenticated;
grant select on public.product_portions to authenticated;

