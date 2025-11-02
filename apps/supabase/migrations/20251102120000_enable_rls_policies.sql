-- ============================================================================
-- migration: enable row level security policies
-- purpose: enable rls on all tables and create granular access policies for
--          user-owned tables and read-only dictionary tables. this ensures
--          data isolation per user and controlled access to shared reference
--          data.
-- affected objects: tables public.profiles, public.meals, public.analysis_runs,
--                   public.analysis_run_items, public.meal_categories,
--                   public.unit_definitions, public.unit_aliases,
--                   public.products, public.product_portions; rls policies
--                   for authenticated role.
-- ============================================================================

-- ============================================================================
-- user-owned tables: profiles, meals, analysis_runs, analysis_run_items
-- access pattern: users can only access their own data (user_id = auth.uid())
-- operations: select, insert, update, delete with user_id isolation
-- ============================================================================

-- enable rls on profiles table
alter table public.profiles enable row level security;

-- profiles: authenticated users can select their own profile
create policy profiles_authenticated_select_policy
  on public.profiles
  for select
  to authenticated
  using (user_id = auth.uid());

-- profiles: authenticated users can insert their own profile
create policy profiles_authenticated_insert_policy
  on public.profiles
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- profiles: authenticated users can update their own profile
create policy profiles_authenticated_update_policy
  on public.profiles
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- profiles: authenticated users can delete their own profile
create policy profiles_authenticated_delete_policy
  on public.profiles
  for delete
  to authenticated
  using (user_id = auth.uid());

-- enable rls on meals table
alter table public.meals enable row level security;

-- meals: authenticated users can select their own meals
create policy meals_authenticated_select_policy
  on public.meals
  for select
  to authenticated
  using (user_id = auth.uid());

-- meals: authenticated users can insert their own meals
create policy meals_authenticated_insert_policy
  on public.meals
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- meals: authenticated users can update their own meals
create policy meals_authenticated_update_policy
  on public.meals
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- meals: authenticated users can delete their own meals
create policy meals_authenticated_delete_policy
  on public.meals
  for delete
  to authenticated
  using (user_id = auth.uid());

-- enable rls on analysis_runs table
alter table public.analysis_runs enable row level security;

-- analysis_runs: authenticated users can select their own analysis runs
create policy analysis_runs_authenticated_select_policy
  on public.analysis_runs
  for select
  to authenticated
  using (user_id = auth.uid());

-- analysis_runs: authenticated users can insert their own analysis runs
create policy analysis_runs_authenticated_insert_policy
  on public.analysis_runs
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- analysis_runs: authenticated users can update their own analysis runs
create policy analysis_runs_authenticated_update_policy
  on public.analysis_runs
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- analysis_runs: authenticated users can delete their own analysis runs
create policy analysis_runs_authenticated_delete_policy
  on public.analysis_runs
  for delete
  to authenticated
  using (user_id = auth.uid());

-- enable rls on analysis_run_items table
alter table public.analysis_run_items enable row level security;

-- analysis_run_items: authenticated users can select their own analysis run items
create policy analysis_run_items_authenticated_select_policy
  on public.analysis_run_items
  for select
  to authenticated
  using (user_id = auth.uid());

-- analysis_run_items: authenticated users can insert their own analysis run items
create policy analysis_run_items_authenticated_insert_policy
  on public.analysis_run_items
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- analysis_run_items: authenticated users can update their own analysis run items
create policy analysis_run_items_authenticated_update_policy
  on public.analysis_run_items
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- analysis_run_items: authenticated users can delete their own analysis run items
create policy analysis_run_items_authenticated_delete_policy
  on public.analysis_run_items
  for delete
  to authenticated
  using (user_id = auth.uid());

-- ============================================================================
-- read-only dictionary tables: meal_categories, unit_definitions,
-- unit_aliases, products, product_portions
-- access pattern: authenticated users can read all records, no write access
-- operations: select only (write operations blocked by rls)
-- ============================================================================

-- enable rls on meal_categories table
alter table public.meal_categories enable row level security;

-- meal_categories: authenticated users can select all meal categories
-- rationale: meal categories are shared reference data used for categorizing
--            meals across all users
create policy meal_categories_authenticated_select_policy
  on public.meal_categories
  for select
  to authenticated
  using (true);

-- enable rls on unit_definitions table
alter table public.unit_definitions enable row level security;

-- unit_definitions: authenticated users can select all unit definitions
-- rationale: unit definitions are shared reference data for measurement units
--            used in meal analysis across all users
create policy unit_definitions_authenticated_select_policy
  on public.unit_definitions
  for select
  to authenticated
  using (true);

-- enable rls on unit_aliases table
alter table public.unit_aliases enable row level security;

-- unit_aliases: authenticated users can select all unit aliases
-- rationale: unit aliases are shared reference data providing localized names
--            for unit definitions used across all users
create policy unit_aliases_authenticated_select_policy
  on public.unit_aliases
  for select
  to authenticated
  using (true);

-- enable rls on products table
alter table public.products enable row level security;

-- products: authenticated users can select all products
-- rationale: products are shared reference data containing nutritional
--            information used in meal analysis across all users
create policy products_authenticated_select_policy
  on public.products
  for select
  to authenticated
  using (true);

-- enable rls on product_portions table
alter table public.product_portions enable row level security;

-- product_portions: authenticated users can select all product portions
-- rationale: product portions are shared reference data defining standard
--            serving sizes used in meal analysis across all users
create policy product_portions_authenticated_select_policy
  on public.product_portions
  for select
  to authenticated
  using (true);

