-- ============================================================================
-- migration: populate meal categories
-- purpose: insert standard meal categories into the meal_categories table
--          without affecting existing data. safe to run multiple times.
-- affected objects: table public.meal_categories (insert operations only)
-- notes: uses on conflict do nothing to prevent duplicate key errors
-- ============================================================================

-- Insert standard meal categories with proper sort order
-- These are the categories referenced by the meals table and used in the UI

insert into public.meal_categories (code, label, sort_order)
values
  ('breakfast', 'Śniadanie', 1),
  ('lunch', 'Obiad', 2),
  ('dinner', 'Kolacja', 3),
  ('snack', 'Przekąska', 4)
on conflict (code) do nothing;

-- Optional: Insert English translations for future localization support
-- Note: The current implementation doesn't use these yet, but they're ready
-- insert into public.meal_categories (code, label, sort_order)
-- values
--   ('breakfast', 'Breakfast', 1),
--   ('lunch', 'Lunch', 2),
--   ('dinner', 'Dinner', 3),
--   ('snack', 'Snack', 4)
-- on conflict (code) do nothing;
