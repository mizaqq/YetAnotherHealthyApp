1. Lista tabel z ich kolumnami, typami danych i ograniczeniami

#### auth.users _(zarządzana przez Supabase Auth)_

| Kolumna            | Typ         | Ograniczenia                     | Opis                                                                   |
| ------------------ | ----------- | -------------------------------- | ---------------------------------------------------------------------- |
| id                 | uuid        | PRIMARY KEY                      | Globalny identyfikator użytkownika; wykorzystywany w tabelach domeny.  |
| email              | text        | NOT NULL UNIQUE                  | Główny adres e-mail użytkownika.                                       |
| email_confirmed_at | timestamptz |                                  | Moment potwierdzenia adresu e-mail.                                    |
| encrypted_password | text        |                                  | Hasło przechowywane w formie zaszyfrowanej; zarządzane przez Supabase. |
| raw_app_meta_data  | jsonb       | NOT NULL DEFAULT '{}'::jsonb     | Metadane aplikacji (np. role) przechowywane przez Supabase.            |
| raw_user_meta_data | jsonb       | NOT NULL DEFAULT '{}'::jsonb     | Metadane użytkownika dostarczone podczas rejestracji.                  |
| last_sign_in_at    | timestamptz |                                  | Ostatnie logowanie użytkownika.                                        |
| created_at         | timestamptz | NOT NULL DEFAULT now()           | Czas utworzenia konta.                                                 |
| updated_at         | timestamptz | NOT NULL DEFAULT now()           | Czas ostatniej modyfikacji rekordu.                                    |
| banned_until       | timestamptz |                                  | Blokada logowania (NULL gdy brak).                                     |
| aud                | text        | NOT NULL DEFAULT 'authenticated' | Typ odbiorcy tokena (audience).                                        |
| role               | text        | NOT NULL DEFAULT 'authenticated' | Rola logiczna w Supabase.                                              |

#### public.profiles

| Kolumna                 | Typ           | Ograniczenia                                            | Opis                                                                                      |
| ----------------------- | ------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| user_id                 | uuid          | PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE | Identyfikator użytkownika z Supabase Auth; kaskadowe usuwanie utrzymuje spójność profilu. |
| daily_calorie_goal      | numeric(10,2) | NOT NULL, CHECK (daily_calorie_goal >= 0)               | Dzienny cel kaloryczny użytkownika.                                                       |
| timezone                | text          | NOT NULL DEFAULT 'UTC'                                  | Strefa czasowa w formacie IANA.                                                           |
| onboarding_completed_at | timestamptz   |                                                         | Moment ukończenia onboardingu (NULL w trakcie).                                           |
| created_at              | timestamptz   | NOT NULL DEFAULT now()                                  | Data utworzenia profilu.                                                                  |
| updated_at              | timestamptz   | NOT NULL DEFAULT now()                                  | Data ostatniej aktualizacji (utrzymywana triggerem).                                      |

#### public.meal_categories

| Kolumna    | Typ         | Ograniczenia                             | Opis                                                  |
| ---------- | ----------- | ---------------------------------------- | ----------------------------------------------------- |
| code       | text        | PRIMARY KEY                              | Techniczny identyfikator kategorii (np. 'breakfast'). |
| label      | text        | NOT NULL, UNIQUE                         | Nazwa kategorii prezentowana w UI.                    |
| sort_order | smallint    | NOT NULL, UNIQUE, CHECK (sort_order > 0) | Kolejność wyświetlania kategorii.                     |
| created_at | timestamptz | NOT NULL DEFAULT now()                   | Data utworzenia wpisu słownika.                       |

#### public.unit_definitions

| Kolumna        | Typ           | Ograniczenia                          | Opis                                                                |
| -------------- | ------------- | ------------------------------------- | ------------------------------------------------------------------- |
| id             | uuid          | PRIMARY KEY DEFAULT gen_random_uuid() | Techniczny identyfikator jednostki.                                 |
| code           | text          | NOT NULL, UNIQUE                      | Kanoniczny kod jednostki (np. 'g', 'łyżka', 'szt').                 |
| unit_type      | text          | NOT NULL                              | Klasyfikacja jednostki (mass, piece, portion, utensil).             |
| grams_per_unit | numeric(12,4) | NOT NULL CHECK (grams_per_unit > 0)   | Jednoznaczna konwersja do gramów (MVP operuje wyłącznie w gramach). |
| created_at     | timestamptz   | NOT NULL DEFAULT now()                | Data utworzenia wpisu słownika.                                     |
| updated_at     | timestamptz   | NOT NULL DEFAULT now()                | Data aktualizacji (utrzymywana triggerem).                          |

Ograniczenia specjalne:

- UNIQUE (LOWER(code)).

#### public.unit_aliases

| Kolumna            | Typ         | Ograniczenia                                                      | Opis                                                         |
| ------------------ | ----------- | ----------------------------------------------------------------- | ------------------------------------------------------------ |
| unit_definition_id | uuid        | NOT NULL REFERENCES public.unit_definitions(id) ON DELETE CASCADE | Odwołanie do kanonicznej jednostki.                          |
| alias              | text        | NOT NULL                                                          | Wariant nazwy jednostki (np. 'łyżka', 'Tbsp', 'tablespoon'). |
| locale             | text        | NOT NULL DEFAULT 'pl-PL'                                          | Kontekst językowy aliasu.                                    |
| is_primary         | boolean     | NOT NULL DEFAULT false                                            | Czy alias jest podstawową etykietą w danym locale.           |
| created_at         | timestamptz | NOT NULL DEFAULT now()                                            | Data utworzenia.                                             |

Ograniczenia specjalne:

- PRIMARY KEY (unit_definition_id, alias, locale).
- Unikalny alias per locale oznaczony jako primary (CHECK (is_primary = false OR alias IS NOT NULL)).

#### public.products

| Kolumna         | Typ         | Ograniczenia                                                                                                                             | Opis                                        |
| --------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| id              | uuid        | PRIMARY KEY DEFAULT gen_random_uuid()                                                                                                    | Identyfikator produktu.                     |
| name            | text        | NOT NULL                                                                                                                                 | Nazwa produktu.                             |
| off_id          | text        | UNIQUE                                                                                                                                   | Identyfikator Open Food Facts (opcjonalny). |
| macros_per_100g | jsonb       | NOT NULL, CHECK (macros_per_100g ? 'calories' AND macros_per_100g ? 'protein' AND macros_per_100g ? 'fat' AND macros_per_100g ? 'carbs') | Makra na 100 g w formacie JSON.             |
| source          | text        | NOT NULL                                                                                                                                 | Pochodzenie danych (np. 'open_food_facts'). |
| created_at      | timestamptz | NOT NULL DEFAULT now()                                                                                                                   | Data utworzenia wpisu.                      |
| updated_at      | timestamptz | NOT NULL DEFAULT now()                                                                                                                   | Data aktualizacji (utrzymywana triggerem).  |

Ograniczenia specjalne:

- UNIQUE (LOWER(name)).

#### public.product_portions

| Kolumna            | Typ           | Ograniczenia                                                      | Opis                                      |
| ------------------ | ------------- | ----------------------------------------------------------------- | ----------------------------------------- |
| id                 | uuid          | PRIMARY KEY DEFAULT gen_random_uuid()                             | Identyfikator porcji produktu.            |
| product_id         | uuid          | NOT NULL REFERENCES public.products(id) ON DELETE CASCADE         | Produkt, którego dotyczy porcja.          |
| unit_definition_id | uuid          | NOT NULL REFERENCES public.unit_definitions(id) ON DELETE CASCADE | Jednostka, w której zdefiniowano porcję.  |
| grams_per_portion  | numeric(12,4) | NOT NULL CHECK (grams_per_portion > 0)                            | Masa pojedynczej porcji w gramach.        |
| is_default         | boolean       | NOT NULL DEFAULT false                                            | Czy porcja jest domyślna dla produktu.    |
| source             | text          |                                                                   | Źródło danych (np. producent, baza USDA). |
| created_at         | timestamptz   | NOT NULL DEFAULT now()                                            | Data utworzenia wpisu.                    |

Ograniczenia specjalne:

- UNIQUE (product_id, unit_definition_id).
- CHECK (is_default = false OR is_default IS NOT NULL).

#### public.meals

| Kolumna                  | Typ           | Ograniczenia                                                                         | Opis                                       |
| ------------------------ | ------------- | ------------------------------------------------------------------------------------ | ------------------------------------------ |
| id                       | uuid          | PRIMARY KEY DEFAULT gen_random_uuid()                                                | Identyfikator posiłku.                     |
| user_id                  | uuid          | NOT NULL REFERENCES public.profiles(user_id) ON DELETE CASCADE                       | Właściciel wpisu (profil użytkownika).     |
| category                 | text          | NOT NULL REFERENCES public.meal_categories(code)                                     | Kategoria posiłku.                         |
| eaten_at                 | timestamptz   | NOT NULL                                                                             | Czas spożycia posiłku w czasie serwera.    |
| source                   | meal_source   | NOT NULL DEFAULT 'ai'::meal_source                                                   | Źródło danych (ai, edited, manual).        |
| calories                 | numeric(10,2) | NOT NULL, CHECK (calories >= 0)                                                      | Kalorie posiłku.                           |
| protein                  | numeric(10,2) | CHECK (protein >= 0)                                                                 | Białko (g).                                |
| fat                      | numeric(10,2) | CHECK (fat >= 0)                                                                     | Tłuszcz (g).                               |
| carbs                    | numeric(10,2) | CHECK (carbs >= 0)                                                                   | Węglowodany (g).                           |
| accepted_analysis_run_id | uuid          | REFERENCES public.analysis_runs(id) DEFERRABLE INITIALLY DEFERRED ON DELETE SET NULL | Akceptowana analiza AI.                    |
| created_at               | timestamptz   | NOT NULL DEFAULT now()                                                               | Data utworzenia.                           |
| updated_at               | timestamptz   | NOT NULL DEFAULT now()                                                               | Data aktualizacji (utrzymywana triggerem). |
| deleted_at               | timestamptz   |                                                                                      | Znacznik miękkiego usunięcia.              |

Ograniczenia specjalne:

- FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE.
- UNIQUE (user_id, id) w celu wspierania kluczy złożonych w dzieciach.
- CHECK ((source = 'manual' AND accepted_analysis_run_id IS NULL AND protein IS NULL AND fat IS NULL AND carbs IS NULL) OR (source IN ('ai', 'edited') AND accepted_analysis_run_id IS NOT NULL AND protein IS NOT NULL AND fat IS NOT NULL AND carbs IS NOT NULL)).
- CHECK (deleted_at IS NULL OR deleted_at >= created_at).

#### public.analysis_runs

| Kolumna          | Typ                 | Ograniczenia                                                   | Opis                                                              |
| ---------------- | ------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------- |
| id               | uuid                | PRIMARY KEY DEFAULT gen_random_uuid()                          | Identyfikator przebiegu analizy.                                  |
| user_id          | uuid                | NOT NULL REFERENCES public.profiles(user_id) ON DELETE CASCADE | Właściciel wpisu (profil użytkownika, dla RLS).                   |
| meal_id          | uuid                | NOT NULL REFERENCES public.meals(id) ON DELETE CASCADE         | Posiłek, którego dotyczy analiza.                                 |
| run_no           | integer             | NOT NULL, CHECK (run_no > 0)                                   | Numer iteracji analizy dla danego posiłku.                        |
| status           | analysis_run_status | NOT NULL                                                       | Status przebiegu (queued, running, succeeded, failed, cancelled). |
| model            | text                | NOT NULL                                                       | Model użyty w analizie.                                           |
| latency_ms       | integer             | CHECK (latency_ms >= 0)                                        | Czas trwania w milisekundach.                                     |
| tokens           | integer             | CHECK (tokens >= 0)                                            | Łączna liczba tokenów.                                            |
| cost_minor_units | integer             | CHECK (cost_minor_units >= 0)                                  | Koszt w najmniejszych jednostkach waluty.                         |
| cost_currency    | char(3)             | NOT NULL DEFAULT 'USD'                                         | Kod waluty ISO 4217.                                              |
| threshold_used   | numeric(3,2)        | CHECK (threshold_used >= 0 AND threshold_used <= 1)            | Próg pewności użyty przy dopasowaniach.                           |
| retry_of_run_id  | uuid                | REFERENCES public.analysis_runs(id) ON DELETE SET NULL         | Poprzedni przebieg, który retry'ujemy (opcjonalnie).              |
| error_code       | text                |                                                                | Kod błędu (gdy status = failed).                                  |
| error_message    | text                |                                                                | Komunikat błędu.                                                  |
| raw_input        | jsonb               | NOT NULL                                                       | Surowe dane wejściowe przekazane do modelu.                       |
| raw_output       | jsonb               |                                                                | Surowe dane wyjściowe modelu.                                     |
| created_at       | timestamptz         | NOT NULL DEFAULT now()                                         | Znacznik utworzenia.                                              |
| completed_at     | timestamptz         |                                                                | Znacznik zakończenia przebiegu (NULL gdy trwa).                   |

Ograniczenia specjalne:

- FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE.
- FOREIGN KEY (meal_id, user_id) REFERENCES public.meals(id, user_id) ON DELETE CASCADE.
- FOREIGN KEY (retry_of_run_id, user_id) REFERENCES public.analysis_runs(id, user_id) ON DELETE SET NULL.
- UNIQUE (meal_id, run_no).
- UNIQUE (user_id, id).
- CHECK (retry_of_run_id IS NULL OR retry_of_run_id <> id).

#### public.analysis_run_items

| Kolumna            | Typ           | Ograniczenia                                                   | Opis                                                 |
| ------------------ | ------------- | -------------------------------------------------------------- | ---------------------------------------------------- |
| id                 | uuid          | PRIMARY KEY DEFAULT gen_random_uuid()                          | Identyfikator wiersza składnika.                     |
| user_id            | uuid          | NOT NULL REFERENCES public.profiles(user_id) ON DELETE CASCADE | Właściciel wpisu (profil użytkownika, dla RLS).      |
| run_id             | uuid          | NOT NULL REFERENCES public.analysis_runs(id) ON DELETE CASCADE | Przebieg analizy nadrzędny.                          |
| ordinal            | integer       | NOT NULL, CHECK (ordinal > 0)                                  | Kolejność składnika w analizie.                      |
| raw_name           | text          | NOT NULL                                                       | Nazwa składnika zwrócona przez model.                |
| raw_unit           | text          |                                                                | Jednostka w postaci surowego tekstu (np. 'łyżka').   |
| product_id         | uuid          | REFERENCES public.products(id)                                 | Dopasowany produkt z listy kanonicznej (opcjonalny). |
| quantity           | numeric(10,3) | NOT NULL, CHECK (quantity > 0)                                 | Ilość w jednostce źródłowej.                         |
| unit_definition_id | uuid          | REFERENCES public.unit_definitions(id)                         | Znormalizowana jednostka po dopasowaniu.             |
| product_portion_id | uuid          | REFERENCES public.product_portions(id)                         | Użyta porcja produktu (jeśli dostępna).              |
| weight_grams       | numeric(12,4) | CHECK (weight_grams IS NULL OR weight_grams >= 0)              | Masa przeliczona na gramy.                           |
| confidence         | numeric(3,2)  | CHECK (confidence >= 0 AND confidence <= 1)                    | Pewność dopasowania.                                 |
| calories           | numeric(10,2) | CHECK (calories >= 0)                                          | Kalorie składnika.                                   |
| protein            | numeric(10,2) | CHECK (protein >= 0)                                           | Białko w gramach.                                    |
| fat                | numeric(10,2) | CHECK (fat >= 0)                                               | Tłuszcz w gramach.                                   |
| carbs              | numeric(10,2) | CHECK (carbs >= 0)                                             | Węglowodany w gramach.                               |
| created_at         | timestamptz   | NOT NULL DEFAULT now()                                         | Data utworzenia wpisu.                               |

Ograniczenia specjalne:

- FOREIGN KEY (user_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE.
- FOREIGN KEY (run_id, user_id) REFERENCES public.analysis_runs(id, user_id) ON DELETE CASCADE.
- CHECK (product_portion_id IS NULL OR unit_definition_id IS NOT NULL).
- UNIQUE (run_id, ordinal).
- CHECK (weight_grams IS NOT NULL OR product_portion_id IS NOT NULL OR unit_definition_id IS NOT NULL).

  1.2. Dodatkowe słowniki i sekwencje pomocnicze

- Słowniki `public.meal_categories`, `public.units`, `public.products`, `public.product_unit_defaults` utrzymywane centralnie; modyfikacje tylko przez rolę serwisową.

2. Relacje między tabelami

- `auth.users` (1:1) → `public.profiles` przez `profiles.user_id` (ON DELETE CASCADE).
- `public.profiles` (1:N) → `public.meals` przez `meals.user_id` (ON DELETE CASCADE).
- `public.profiles` (1:N) → `public.analysis_runs` przez `analysis_runs.user_id` (ON DELETE CASCADE).
- `public.profiles` (1:N) → `public.analysis_run_items` przez `analysis_run_items.user_id` (ON DELETE CASCADE).
- `public.meal_categories` (1:N) → `public.meals` przez `meals.category`.
- `public.meals` (1:N) → `public.analysis_runs` (FK `analysis_runs.meal_id`).
- `public.analysis_runs` (1:N) → `public.analysis_run_items` (FK `analysis_run_items.run_id`).
- `public.meals` (opcjonalne 1:1) ← `public.analysis_runs` poprzez `meals.accepted_analysis_run_id`.
- `public.unit_definitions` (1:N) → `public.unit_aliases`.
- `public.products` (1:N) → `public.product_portions` oraz opcjonalnie (1:N) → `public.analysis_run_items`.
- `public.unit_definitions` (1:N) → `public.product_portions` i (1:N) → `public.analysis_run_items`.
- `public.analysis_run_items` (opcjonalnie) → `public.product_portions` przez `product_portion_id`.
- `public.analysis_runs` (opcjonalne 1:1) → `public.analysis_runs` przez `retry_of_run_id`.

3. Indeksy

- CREATE UNIQUE INDEX products_lower_name_key ON public.products (LOWER(name));
- CREATE UNIQUE INDEX meals_user_id_id_key ON public.meals (user_id, id);
- CREATE INDEX meals_user_id_eaten_at_idx ON public.meals (user_id, eaten_at) WHERE deleted_at IS NULL;
- CREATE INDEX meals_category_idx ON public.meals (category) WHERE deleted_at IS NULL;
- CREATE UNIQUE INDEX analysis_runs_meal_id_run_no_key ON public.analysis_runs (meal_id, run_no);
- CREATE UNIQUE INDEX analysis_runs_user_id_id_key ON public.analysis_runs (user_id, id);
- CREATE INDEX analysis_runs_user_id_created_at_idx ON public.analysis_runs (user_id, created_at DESC);
- CREATE INDEX analysis_runs_retry_of_run_id_idx ON public.analysis_runs (retry_of_run_id);
- CREATE INDEX analysis_run_items_run_id_idx ON public.analysis_run_items (run_id);
- CREATE INDEX analysis_run_items_product_id_idx ON public.analysis_run_items (product_id);
- CREATE INDEX product_unit_defaults_unit_id_idx ON public.product_unit_defaults (unit_id);

4. Zasady PostgreSQL (RLS)

- ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
- CREATE POLICY profiles_owner_policy ON public.profiles USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
- ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;
- CREATE POLICY meals_select_policy ON public.meals FOR SELECT USING (user_id = auth.uid() AND deleted_at IS NULL);
- CREATE POLICY meals_mod_policy ON public.meals FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
- ALTER TABLE public.analysis_runs ENABLE ROW LEVEL SECURITY;
- CREATE POLICY analysis_runs_policy ON public.analysis_runs USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
- ALTER TABLE public.analysis_run_items ENABLE ROW LEVEL SECURITY;
- CREATE POLICY analysis_run_items_policy ON public.analysis_run_items USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
- Dla słowników (`public.meal_categories`, `public.units`, `public.products`, `public.product_unit_defaults`) pozostawić RLS wyłączone i nadać SELECT roli `authenticated`; modyfikacje wyłącznie przez rolę `service_role`.

5. Dodatkowe uwagi

- Utworzyć typy enum: `CREATE TYPE public.meal_source AS ENUM ('ai', 'edited', 'manual');` oraz `CREATE TYPE public.analysis_run_status AS ENUM ('queued', 'running', 'succeeded', 'failed', 'cancelled');`.
- Wymagane rozszerzenie `pgcrypto` (lub `uuid-ossp`) dla funkcji `gen_random_uuid()`.
- Zapewnić wyzwalacze `updated_at` na tabelach `public.profiles`, `public.units`, `public.products`, `public.meals` (np. trigger BEFORE UPDATE ustawiający kolumnę na `now()`).
- Rozważyć trigger blokujący zmianę `user_id` po utworzeniu rekordu w tabelach użytkownika (`profiles`, `meals`, `analysis_runs`, `analysis_run_items`).
- Zapisy manualne (`source = 'manual'`) przechowują wyłącznie kalorie; backend powinien weryfikować brak makr przy takich wpisach.
- Przy soft-delecie posiłku (`deleted_at` <> NULL) kaskadowe usuwanie w `analysis_runs`/`analysis_run_items` zapewnia spójność, ale RLS ukrywa wpis przed użytkownikiem bez fizycznego usuwania rekordu.
