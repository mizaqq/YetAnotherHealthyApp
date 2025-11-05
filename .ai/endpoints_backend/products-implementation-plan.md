# API Endpoint Implementation Plan: Products Retrieval

## 1. Przegląd punktu końcowego

- Zapewnia odczyt katalogu produktów żywieniowych pod `/api/v1/products`, wspierając sugestie AI i ręczne wybory użytkowników.
- Udostępnia paginowane wyszukiwanie produktów, pobieranie szczegółów oraz listę porcji, korzystając z danych Supabase (`public.products`, `public.product_portions`).
- Punkt końcowy jest wyłącznie odczytowy i wymaga uwierzytelnienia użytkownika poprzez Supabase JWT.

## 2. Szczegóły żądania

- **GET `/api/v1/products`**
  - Cel: paginowane wyszukiwanie produktów.
  - Parametry wymagane: brak.
  - Parametry opcjonalne: `search` (str, ≥2 znaki), `off_id` (str), `source` (enum/whitelist), `page[size]` (int 1–50, domyślnie 20), `page[after]` (kursor), `include_macros` (bool, domyślnie false).
- **GET `/api/v1/products/{product_id}`**
  - Cel: zwrócenie pojedynczego produktu.
  - Parametry wymagane: `product_id` (UUID, path).
  - Parametry opcjonalne: `include_portions` (bool, domyślnie false).
- **GET `/api/v1/products/{product_id}/portions`**
  - Cel: lista porcji dla produktu.
  - Parametry wymagane: `product_id` (UUID).
- Treść żądania: brak (wyłącznie parametry zapytań).
- Nagłówki: `Authorization: Bearer <jwt>`, `Accept: application/json`.

## 3. Wykorzystywane typy

- **Schematy zapytań (Pydantic v2):**
  - `ProductListParams` – mapuje aliasy (`page[size]`, `page[after]`, `include_macros`), waliduje zakresy i długości.
  - `ProductDetailParams` – obsługuje flagę `include_portions` z wartościami domyślnymi.
- **Modele komend/domenowe:**
  - `ProductSearchFilter` – hermetyzuje kryteria wyszukiwania i paginacji.
  - `ProductLookupCommand` – przenosi `product_id` oraz flagę uwzględnienia porcji.
- **DTO odpowiedzi:**
  - `MacroBreakdownDTO` (`calories`, `protein`, `fat`, `carbs` jako `Decimal`/`float`).
  - `ProductSummaryDTO` (`id`, `name`, `source`, `macros_per_100g?`).
  - `ProductDetailDTO` (rozszerza summary o `off_id`, `created_at`, `updated_at`, `portions?`).
  - `ProductPortionDTO` (`id`, `unit_definition_id`, `grams_per_portion`, `is_default`, `source`).
  - `PaginationCursorDTO` (`size`, `after`).

## 4. Szczegóły odpowiedzi

- **GET lista:** `200 OK` z `{ "data": ProductSummaryDTO[], "page": PaginationCursorDTO }`; `macros_per_100g` obecne tylko przy `include_macros=true`.
- **GET szczegół:** `200 OK` z `ProductDetailDTO`; `portions` dołączone tylko przy `include_portions=true`.
- **GET portions:** `200 OK` z tablicą `ProductPortionDTO`.
- Kod błędów: `400` (walidacja/kursor), `401` (brak autoryzacji), `404` (produkt nie istnieje), `500` (nieoczekiwany błąd).

## 5. Przepływ danych

1. FastAPI router (`app/api/v1/endpoints/products.py`) wykorzystuje zależność `get_current_user` do uwierzytelnienia i pozyskania kontekstu użytkownika.
2. Parametry zapytań przetwarzane przez Pydantic, aliasy mapowane do nazw pól wewnętrznych (np. `page[size]` → `page_size`).
3. Router przekazuje sterowanie do `ProductService` (`app/services/products.py`).
4. Serwis buduje `ProductSearchFilter` / `ProductLookupCommand` i deleguje do repozytorium (`app/db/repositories/products.py`).
5. Repozytorium używa asynchronicznego klienta Supabase do odpytywania tabel (`public.products`, `public.product_portions`) z ograniczeniem kolumn zależnie od flag (`include_macros`).
6. Przy liście: stosuje `ILIKE` na `LOWER(name)` (lub trigram), filtruje po `off_id`, `source`, korzysta z keyset cursora (np. `created_at`, `id`) i limitu.
7. Zwrócone rekordy mapowane na DTO; serwis dołącza metadane paginacji, filtruje `macros` zgodnie z flagami.
8. FastAPI serializuje DTO do JSON, utrzymując aliasy nazw pól zgodne ze specyfikacją.

## 6. Względy bezpieczeństwa

- Uwierzytelnianie poprzez Supabase JWT; endpointy zabezpieczyć `Depends(get_current_user)` i zwracać `401` dla braku tokenu/nieprawidłowego profilu.
- Zapewnić, że konto serwisowe Supabase ma tylko uprawnienia do odczytu danych produktów; RLS powinien dopuszczać globalny odczyt jeśli produkty są publiczne.
- Walidować i normalizować parametry (`search` strip, `source` z whitelisty) aby uniknąć wstrzyknięć lub nadużyć.
- Monitorować wykorzystanie paginacji i limitować `page[size]` do 50.
- Rejestrować dostęp i błędy z identyfikatorami użytkowników w centralnym loggerze lub tabeli audytowej, przy zachowaniu danych osobowych.

## 7. Obsługa błędów

- Walidacja Pydantic zwraca `HTTPException(400)` z komunikatem o polu.
- `SupabaseNotFoundError` dla `product_id` mapować na `HTTPException(404, "Product not found")`.
- Błędy kursora (`page[after]`) traktować jako `400`.
- Problemy sieciowe / nieznane wyjątki logować (`logger.exception`) i zwracać `HTTPException(500, "Internal Server Error")`.
- Jeśli istnieje `app.services.error_log`, przekazywać tam wpisy z kontekstem (endpoint, user_id, payload hash, stacktrace); w przeciwnym razie zapewnić integrację z agregatorem logów.

## 8. Rozważania dotyczące wydajności

- Pobierać tylko wymagane kolumny (`select`) oraz unikać ładowania porcji/macros, gdy flagi są false.
- Dla `include_portions=true` pobierać porcje pojedynczym zapytaniem; przy endpointzie dedykowanym do porcji stosować limit/ordering stabilny (`is_default DESC`, `grams_per_portion`).

## 9. Etapy wdrożenia

1. Zweryfikować istniejące zależności auth/logging oraz zdecydować o lokalizacji nowych modułów (`schemas`, `services`, `repositories`).
2. Zdefiniować Pydantic schematy request/response wraz z aliasami i walidacją long/enum/UUID.
3. Utworzyć repozytorium Supabase z metodami: `list_products`, `get_product`, `list_portions`; zaimplementować keyset paginację oraz selekcje kolumn.
4. Zaimplementować `ProductService` koordynujący walidację biznesową, mapowanie DTO oraz obsługę flag `include_macros`/`include_portions`.
5. Dodać FastAPI router z trzema ścieżkami, zależnościami auth, mapowaniem parametrów na serwis.
