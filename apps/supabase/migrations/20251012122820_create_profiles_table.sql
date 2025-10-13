-- ============================================================================
-- migration: create profiles table
-- purpose: add user profile metadata linked to supabase auth with auditing
--          triggers. rls will be introduced in a later iteration.
-- affected objects: table public.profiles, triggers for updated_at enforcement,
--                   rls policies and grants.
-- ============================================================================

create table public.profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  daily_calorie_goal numeric(10, 2) not null check (daily_calorie_goal >= 0),
  timezone text not null default 'UTC',
  onboarding_completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger trg_profiles_set_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

create trigger trg_profiles_prevent_user_id_change
before update on public.profiles
for each row
execute function public.prevent_user_id_change();

grant select, insert, update, delete on public.profiles to authenticated;

