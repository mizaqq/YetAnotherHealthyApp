-- ============================================================================
-- migration: create enums and helper functions
-- purpose: set up reusable domain enums and helper triggers/functions for
--          auditing within yet another healthy app mvp.
-- affected objects: extension pgcrypto, enums public.meal_source,
--                   public.analysis_run_status, functions
--                   public.set_updated_at(), public.prevent_user_id_change().
-- notes: lower-case sql aligns with house style.
-- ============================================================================

-- ensure uuid generation support is available for default values.
create extension if not exists pgcrypto with schema public;

-- --------------------------------------------------------------------------
-- enum types required by the domain model.
-- --------------------------------------------------------------------------

create type public.meal_source as enum ('ai', 'edited', 'manual');

create type public.analysis_run_status as enum ('queued', 'running', 'succeeded', 'failed', 'cancelled');

-- --------------------------------------------------------------------------
-- helper functions supporting auditing and integrity guarantees.
-- --------------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.prevent_user_id_change()
returns trigger
language plpgsql
as $$
begin
  if old.user_id is distinct from new.user_id then
    raise exception 'changing user_id is not allowed once set';
  end if;
  return new;
end;
$$;

