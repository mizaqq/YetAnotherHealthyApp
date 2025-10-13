import type { SupabaseClient } from "@supabase/supabase-js";

import type { Database } from "../db/database.types";
import { supabase as defaultClient } from "./supabaseClient";

export type Supabase = SupabaseClient<Database>;

export const getSupabase = (client: Supabase = defaultClient): Supabase =>
  client;

