-- ============================================================================
-- migration: create analysis tables
-- purpose: store ai analysis runs and ingredient line items linked to meals,
--          with ownership protections, triggers, and indexes. rls policies
--          will be addressed later.
-- affected objects: tables public.analysis_runs, public.analysis_run_items,
--                   related constraints and indexes, policies, grants;
--                   fk from meals to accepted analysis run.
-- ============================================================================

create table public.analysis_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (user_id) on delete cascade,
  meal_id uuid references public.meals (id) on delete cascade,
  run_no integer not null check (run_no > 0),
  status public.analysis_run_status not null,
  model text not null,
  latency_ms integer check (latency_ms >= 0),
  tokens integer check (tokens >= 0),
  cost_minor_units integer check (cost_minor_units >= 0),
  cost_currency char(3) not null default 'USD',
  threshold_used numeric(3, 2) check (threshold_used >= 0 and threshold_used <= 1),
  retry_of_run_id uuid,
  error_code text,
  error_message text,
  raw_input jsonb not null,
  raw_output jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  unique (user_id, id),
  check (retry_of_run_id is null or retry_of_run_id <> id)
);

create trigger trg_analysis_runs_prevent_user_id_change
before update on public.analysis_runs
for each row
execute function public.prevent_user_id_change();

create unique index analysis_runs_meal_id_run_no_key
  on public.analysis_runs (meal_id, run_no)
  where meal_id is not null;

create index analysis_runs_user_id_created_at_idx
  on public.analysis_runs (user_id, created_at desc);

create index analysis_runs_retry_of_run_id_idx
  on public.analysis_runs (retry_of_run_id);

alter table public.analysis_runs
  add constraint analysis_runs_meal_user_fk
  foreign key (meal_id, user_id)
  references public.meals (id, user_id)
  on delete cascade;

alter table public.analysis_runs
  add constraint analysis_runs_retry_user_fk
  foreign key (retry_of_run_id, user_id)
  references public.analysis_runs (id, user_id)
  on delete set null;

create table public.analysis_run_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (user_id) on delete cascade,
  run_id uuid not null references public.analysis_runs (id) on delete cascade,
  ordinal integer not null check (ordinal > 0),
  raw_name text not null,
  raw_unit text,
  product_id uuid references public.products (id),
  quantity numeric(10, 3) not null check (quantity > 0),
  unit_definition_id uuid references public.unit_definitions (id),
  product_portion_id uuid references public.product_portions (id),
  weight_grams numeric(12, 4) check (weight_grams is null or weight_grams >= 0),
  confidence numeric(3, 2) check (confidence >= 0 and confidence <= 1),
  calories numeric(10, 2) check (calories >= 0),
  protein numeric(10, 2) check (protein >= 0),
  fat numeric(10, 2) check (fat >= 0),
  carbs numeric(10, 2) check (carbs >= 0),
  created_at timestamptz not null default now(),
  unique (run_id, ordinal),
  check (product_portion_id is null or unit_definition_id is not null),
  check (weight_grams is not null or product_portion_id is not null or unit_definition_id is not null)
);

create trigger trg_analysis_run_items_prevent_user_id_change
before update on public.analysis_run_items
for each row
execute function public.prevent_user_id_change();

create index analysis_run_items_run_id_idx
  on public.analysis_run_items (run_id);

create index analysis_run_items_product_id_idx
  on public.analysis_run_items (product_id);

alter table public.analysis_run_items
  add constraint analysis_run_items_run_user_fk
  foreign key (run_id, user_id)
  references public.analysis_runs (id, user_id)
  on delete cascade;

alter table public.meals
  add constraint meals_accepted_analysis_run_fk
  foreign key (accepted_analysis_run_id)
  references public.analysis_runs (id)
  on delete set null
  deferrable initially deferred;

grant select, insert, update, delete on public.analysis_runs to authenticated;
grant select, insert, update, delete on public.analysis_run_items to authenticated;

