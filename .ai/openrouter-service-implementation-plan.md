## 1. Opis usługi
- Komponent 1 (OpenRouterService): koordynuje budowanie żądań, wywołanie API OpenRouter i walidację odpowiedzi przed zwróceniem ich do warstw domenowych; Wyzwanie 1: zachowanie spójności schematów niezależnie od wersji modeli; Rozwiązanie 1: kontrakty Pydantic oraz blokada `response_format` na `strict: true`; Wyzwanie 2: kontrola czasu odpowiedzi; Rozwiązanie 2: limit czasu na kliencie HTTP i retry z wykładniczym backoffem.
- Komponent 2 (OpenRouterClient): cienka warstwa nad `httpx.AsyncClient` konfigurująca nagłówki `HTTP-Referer`, `X-Title`, API key i retry polityki; Wyzwanie 1: poprawna obsługa 429/5xx; Rozwiązanie 1: `tenacity` z politką retry limitującą liczbę prób; Wyzwanie 2: egzekwowanie polityk sieciowych; Rozwiązanie 2: centralna konfiguracja proxy i blokada hosta docelowego.
- Komponent 3 (OpenRouterConfig): odczytuje wartości z `app/core/config.py` (`OPENROUTER_API_KEY`, `OPENROUTER_DEFAULT_MODEL`, limity tokenów); Wyzwanie 1: brak wartości na środowiskach; Rozwiązanie 1: walidacja startowa FastAPI i zdroworozsądkowe komunikaty; Wyzwanie 2: rotacja sekretów; Rozwiązanie 2: krótkie TTL kluczy i integracja z managerem tajemnic (np. Doppler).
- Komponent 4 (OpenRouterTelemetry): zbiera logi, metryki i ślady wokół wywołań; Wyzwanie 1: korelacja żądań z użytkownikami; Rozwiązanie 1: propagacja `user_id` w `extra` loggera i tagach APM; Wyzwanie 2: higiena danych; Rozwiązanie 2: anonimizacja treści przed zapisem i filtrowanie danych osobowych.
- Komponent 5 (ProductVerificationAdapter): korzysta z istniejącego repozytorium produktów w Supabase do potwierdzania kalorii i makroskładników dla składników zwracanych przez model; Wyzwanie 1: dopasowanie nazw składników między modelem a bazą; Rozwiązanie 1: normalizacja tekstu oraz fallback na wyszukiwanie pełnotekstowe; Wyzwanie 2: brak danych w bazie; Rozwiązanie 2: obsługa wyjątków i wzbogacenie odpowiedzi o flagi `requires_manual_review`.

## 2. Opis konstruktora
- Konstruktor `OpenRouterService` przyjmuje `settings: Settings`, `client: OpenRouterClient`, `products: ProductRepository | ProductService`, `logger: bound Logger`, opcjonalnie `metrics: MetricsRecorder` i `tracer: Tracer`. Zapewnia to wstrzykiwanie zależności przez FastAPI (`Depends`).
- W czasie inicjalizacji należy weryfikować obecność klucza API oraz ustawić domyślne parametry modeli (`default_model`, `default_temperature`, `max_output_tokens`).
- Zalecane jest przygotowanie metody fabrykującej w `app/core/dependencies.py`, aby kontekst żądania (np. `user_id`) był dostępny w logach i limitach.

## 3. Publiczne metody i pola
- `generate_chat_completion(messages, *, model, response_format, **params) -> OpenRouterChatResponse`: buduje payload, uwzględnia konfigurację systemową, waliduje odpowiedź względem schematu i zwraca dane gotowe dla usług domenowych.
- `stream_chat_completion(messages, *, model, response_format, **params) -> AsyncIterator[OpenRouterStreamChunk]`: dowolne strumieniowanie cząstek odpowiedzi; wymaga obsługi SSE z `httpx`.
- `available_models() -> list[str]`: czyta cache modeli z OpenRouter lub Supabase i pozwala na walidację nazwy modelu podczas walidacji wejścia.
- `default_params` (pole): słownik przechowujący domyślne parametry modeli wczytane z konfiguracji, możliwy do nadpisania per żądanie.
- `verify_ingredients_calories(analysis_items) -> IngredientVerificationResult`: porównuje makra wygenerowane przez model z danymi z tabel produktów (wykorzystuje `ProductRepository` lub widok analityczny) i uzupełnia wynik o odchylenia procentowe.
- Przykłady konfiguracji komunikatów i parametrów:
1. Komunikat systemowy: `{"role": "system", "content": "Jesteś dietetycznym asystentem YetAnotherHealthyApp, odpowiadasz po polsku i korzystasz ze schematu makroskładników."}`
2. Komunikat użytkownika: `{"role": "user", "content": "Przelicz makro dla 150 g piersi z kurczaka i 200 g ryżu basmati."}`
3. response_format: `{"type": "json_schema", "json_schema": {"name": "meal_macro_summary", "strict": true, "schema": {"type": "object", "properties": {"protein_g": {"type": "number"}, "carbs_g": {"type": "number"}, "fat_g": {"type": "number"}}, "required": ["protein_g", "carbs_g", "fat_g"]}}}`
4. Nazwa modelu: przykład `"openrouter/anthropic/claude-3.5-sonnet"` przechowywany w konfiguracji jako domyślna wartość z możliwością nadpisania w żądaniu.
5. Parametry modelu: `{"temperature": 0.2, "top_p": 0.95, "max_tokens": 600}` z walidacją zakresów w modelu Pydantic.
- Wzorcowe użycie w kodzie:
```python
payload = service.generate_chat_completion(
    messages=[
        {"role": "system", "content": "Jesteś asystentem do analizy posiłków."},
        {"role": "user", "content": "Stwórz makro dla owsianki z bananem i masłem orzechowym."},
    ],
    model="google/gemini-2.0-flash-exp:free",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "meal_macro_summary",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "protein_g": {"type": "number"},
                    "carbs_g": {"type": "number"},
                    "fat_g": {"type": "number"},
                },
                "required": ["protein_g", "carbs_g", "fat_g"],
            },
        },
    },
    temperature=0.2,
    top_p=0.95,
)

verification = service.verify_ingredients_calories(payload.items)
```

## 4. Prywatne metody i pola
- `_build_headers(user_id) -> dict[str, str]`: skleja nagłówki `Authorization`, `HTTP-Referer`, `X-Title`, `X-Session-Id`; przechowuje w polu `_base_headers` dla ponownego użycia.
- `_build_payload(messages, model, response_format, params) -> OpenRouterChatRequest`: łączy domyślne parametry, waliduje `response_format` i blokuje nieobsługiwane pola; korzysta z Pydantic do serializacji JSON.
- `_send(request_body) -> httpx.Response`: wykonuje wywołanie HTTP, obsługuje retry i limity czasu; trzyma `self._client` do wielokrotnego wykorzystywania połączeń.
- `_parse_response(response) -> OpenRouterChatResponse`: sprawdza status, logi, waliduje JSON schematem Pydantic, spłaszcza treść do formatów domenowych.
- `_map_openrouter_error(response) -> ServiceError`: tłumaczy kody błędów OpenRouter na wyjątki domenowe (`RateLimitError`, `InvalidRequestError`).
- `_match_products_by_name(items) -> list[ProductSummaryDTO]`: wykonuje wyszukiwanie w bazie produktów z wykorzystaniem istniejącego indeksu full-text lub trigramów i zwraca kandydatów do weryfikacji makro.
- `_compare_macros(model_item, product_record) -> MacroDelta`: oblicza różnice wartości odżywczych, flagując przekroczenia tolerancji.

## 5. Obsługa błędów
1. Błąd sieciowy (timeout, DNS): retry z `tenacity`, po przekroczeniu limitu rzucenie `ServiceUnavailableError` (HTTP 503).
2. HTTP 401/403 (klucz niepoprawny): natychmiastowe przerwanie z logiem ostrzegawczym i wyjątkiem `AuthorizationError` mapowanym na HTTP 500 z kodem `external_auth_error`.
3. HTTP 429 (rate limit): wykorzystanie nagłówków `Retry-After`, opóźnienie i rejestracja zdarzenia w metrykach.
4. HTTP 4xx (schemat, parametry): zwracanie `BadRequestError` z detlem otrzymanym od OpenRouter i instrukcją dla developera.
5. HTTP 5xx: ograniczona liczba retry, eskalacja do `ServiceUnavailableError` z logiem `error` i telemetryjnym alarmem.
6. Błędy walidacji JSON (niezgodny `response_format`): `ValidationError` z Pydantic, mapowany na `ServiceDataError` i logowany jako `warning`.
7. Przerwane strumieniowanie: zakończenie generatora z `StreamError` i zapis checkpointu, aby klienci mogli wznowić.
8. Brak dopasowania produktu w bazie: zwrócenie `HTTPException(status_code=404)` lub zwrócenie flagi `requires_manual_review`, logowanie ostrzeżenia oraz metryka brakujących danych.
9. Znacząca różnica kalorii: wyrzucenie `ServiceDataError` z informacją o odchyleniu, aby logika domenowa podjęła decyzję (np. ponowna analiza lub potwierdzenie użytkownika).

## 6. Kwestie bezpieczeństwa
- Przechowywanie `OPENROUTER_API_KEY` w zmiennych środowiskowych `apps/backend/.env`, brak logowania wartości i maskowanie w narzędziach APM.
- Wymuszenie TLS oraz walidacja certyfikatu po stronie `httpx`; zabronienie przekierowań na inne hosty.
- Limitowanie rozmiaru treści przekazywanej do modeli (np. 8 kB) w `_build_payload`, aby zapobiec wyciekom danych.
- Czyszczenie treści z danych osobowych użytkownika przed zapisem logów (np. regexy maskujące adresy e-mail, numery telefonu).
- Monitorowanie nadużyć poprzez korelację `user_id` w metrykach i wprowadzenie limitów użycia na poziomie użytkownika.
- Upewnienie się, że zapytania do bazy produktów są parametryzowane i logowane bez danych wrażliwych, a połączenia Supabase korzystają z odpowiednich ról RLS.

## 7. Plan wdrożenia krok po kroku
1. Rozszerz `apps/backend/app/core/config.py` o sekcję `openrouter` (klucz, domyślny model, parametry) i zaktualizuj `.env.example`.
2. Dodaj modele Pydantic `OpenRouterChatRequest`, `OpenRouterChatMessage`, `OpenRouterChatResponse` w `apps/backend/app/schemas/openrouter.py` z walidacją `response_format` i enumeracją ról.
3. Utwórz `apps/backend/app/services/openrouter_client.py` z konfiguracją `httpx.AsyncClient`, retry `tenacity` i nagłówkami.
4. Zaimplementuj `apps/backend/app/services/openrouter_service.py` zgodnie z opisanymi metodami, wstrzykuj `OpenRouterClient` i `Settings`.
5. Zarejestruj zależność `get_openrouter_service` w `apps/backend/app/core/dependencies.py`, zapewniając propagację `user_id` z kontekstu FastAPI.
6. Dodaj adapter w warstwie domeny (np. `AnalysisRunProcessor`) wywołujący nową usługę i mapujący wynik na modele istniejące (`AnalysisRunItemsRepository`).
7. Zaimplementuj `ProductVerificationAdapter` wykorzystujący `ProductRepository` (zob. `ProductService`) do wyszukiwania składników i obliczania odchyleń makro; przygotuj migracje lub indeksy niezbędne do wyszukiwania tekstowego.
8. Wprowadź walidację wyników analizy: po otrzymaniu danych z OpenRouter uruchom weryfikację makro i oznacz wyniki odbiegające od danych tabelarycznych; w razie potrzeby zapisz adnotacje w tabeli analiz.
