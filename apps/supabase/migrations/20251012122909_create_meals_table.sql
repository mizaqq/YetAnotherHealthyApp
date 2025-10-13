-- ============================================================================
-- migration: create meals table
-- purpose: introduce user-owned meal entries capturing nutrition analysis
--          metadata with integrity constraints, indexes, and grants. rls will
--          be applied in a future migration.
-- affected objects: table public.meals, triggers, indexes, policies, grants.
-- ============================================================================

create table public.meals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (user_id) on delete cascade,
  category text not null references public.meal_categories (code),
  eaten_at timestamptz not null,
  source public.meal_source not null default 'ai',
  calories numeric(10, 2) not null check (calories >= 0),
  protein numeric(10, 2) check (protein >= 0),
  fat numeric(10, 2) check (fat >= 0),
  carbs numeric(10, 2) check (carbs >= 0),
  accepted_analysis_run_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (user_id, id),
  check (
    (source = 'manual' and accepted_analysis_run_id is null and protein is null and fat is null and carbs is null)
    or (source in ('ai', 'edited') and accepted_analysis_run_id is not null and protein is not null and fat is not null and carbs is not null)
  ),
  check (deleted_at is null or deleted_at >= created_at)
);

create trigger trg_meals_set_updated_at
before update on public.meals
for each row
execute function public.set_updated_at();

create trigger trg_meals_prevent_user_id_change
before update on public.meals
for each row
execute function public.prevent_user_id_change();

create index meals_user_id_eaten_at_idx
  on public.meals (user_id, eaten_at)
  where deleted_at is null;

create index meals_category_idx
  on public.meals (category)
  where deleted_at is null;

grant select, insert, update, delete on public.meals to authenticated;

