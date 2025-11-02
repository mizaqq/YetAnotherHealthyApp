import { test as baseTest } from '@playwright/test';
import { createClient } from '@supabase/supabase-js';
import type { Database } from '../src/db/database.types';

// Create a Supabase client for test cleanup (will be authenticated per test)
const createSupabaseClient = () => createClient<Database>(
  process.env.VITE_SUPABASE_URL || '',
  process.env.VITE_SUPABASE_ANON_KEY || ''
);

// Extend the base test with supawright-like functionality
export const test = baseTest.extend<{
  supawright: {
    supabase: () => ReturnType<typeof createSupabaseClient>;
  };
}>({
  supawright: async ({}, use) => {
    const supabase = createSupabaseClient();

    // Authenticate with test credentials
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: process.env.E2E_USERNAME || '',
      password: process.env.E2E_PASSWORD || '',
    });

    if (signInError) {
      console.error('Error signing in:', signInError);
      throw signInError;
    }

    await use({
      supabase: () => supabase,
    });

    // Sign out after test
    await supabase.auth.signOut();
  },
});

export { expect } from '@playwright/test';
