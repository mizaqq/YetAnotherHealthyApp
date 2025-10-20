# API Endpoint Implementation Plan_3: PATCH /api/v1/meals/{meal_id}

## 1. Przegląd punktu końcowego

- Aktualizuje istniejący wpis posiłku użytkownika, umożliwiając zmianę kategorii, daty, makr oraz rekategoryzację źródła (np. konwersja manual → edited).
- Synchronizuje zmiany z powiązanymi analizami oraz wymusza constrainty tabeli `public.meals`.

## 2. Szczegóły żądania

- Metoda HTTP: PATCH
- Struktura URL: `/api/v1/meals/{meal_id}`
- Nagłówki: `Authorization: Bearer <JWT>`, `Content-Type: application/json`
- Parametry:
  - Path param: `meal_id` (UUID) – wymagany
  - Body: pola opcjonalne (`category`, `eaten_at`, `calories`, `protein`, `fat`, `carbs`, `source`, `analysis_run_id`, `notes`)
- Walidacje wejścia:
  - Spójność `source` z makrami i `analysis_run_id` jak przy tworzeniu
  - `source` nie może wrócić do `manual` jeśli makra/analiza już ustawione (zależne od reguł biznesowych)
  - `analysis_run_id` musi należeć do użytkownika i mieć status `succeeded`
  - `calories` i makra ≥ 0 (`Decimal`), `eaten_at` ISO8601
  - Weryfikacja, że co najmniej jedno pole ulega zmianie
- Modele wejściowe:
  - `MealUpdatePayload` (Pydantic) z walidatorami krzyżowymi
  - `UpdateMealCommand` przekazywana do serwisu (z `user_id`, `meal_id`, polami optional)

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `200 OK`
- Struktura body: pełny obiekt `MealResponse` odzwierciedlający stan po aktualizacji

## 4. Przepływ danych

- Autoryzacja JWT → `get_current_user` dostarcza `user_id`.
- FastAPI waliduje `MealUpdatePayload`; handler tworzy `UpdateMealCommand`.
- `MealService.update_meal` pobiera posiłek użytkownika, stosuje zmiany z uwzględnieniem constraintów (np. `analysis_run_id`, makra).
- Przy zmianie `analysis_run_id` wykonuje walidację i aktualizację powiązania (możliwy `SELECT FOR UPDATE`).
- Serwis aktualizuje rekord, odświeża encję i zwraca zmieniony posiłek.
- Handler serializuje do `MealResponse` i zwraca z kodem 200.

## 5. Względy bezpieczeństwa

- Tylko właściciel posiłku (sprawdzane przez `user_id`).
- Walidacja `analysis_run_id` i makr zapobiega obejściu reguł biznesowych.
- Logowanie zmian (np. audit log) może być wymagane dla zgodności.
- Parametryzowane zapytania repozytorium eliminują SQLi.

## 6. Obsługa błędów

- `400 Bad Request`: niespójne pola (np. brak makr przy `source=edited`), brak zmian w payloadzie.
- `401 Unauthorized`: brak/niepoprawny token.
- `404 Not Found`: posiłek nie istnieje lub nie należy do użytkownika.
- `409 Conflict`: `analysis_run_id` już zaakceptowany w innym posiłku.
- `500 Internal Server Error`: błędy repozytorium/serwisu; logowane centralnie.

## 7. Wydajność

- Użyć indeksów na `meals.id`, `meals.user_id` dla szybkiego wyszukiwania.
- Aktualizacje ograniczać do zmienionych pól (użycie `update` z `synchronize_session=False`).
- Zachować minimalną liczbę zapytań (np. jedno pobranie + jedna aktualizacja).

## 8. Kroki implementacji

1. Zdefiniować `MealUpdatePayload`, `UpdateMealCommand` w `schemas/meals.py`.
2. Dodać metodę `MealService.update_meal` obsługującą walidacje i aktualizacje.
3. Rozszerzyć repozytoria o pobieranie i aktualizację posiłku z kontrolą `user_id`.
4. Dodać handler FastAPI `update_meal` (PATCH) mapujący wyjątki na odpowiednie statusy.
5. Przygotować testy jednostkowe (walidacje, serwis) oraz integracyjne (scenariusze pozytywne i błędów).
6. Uaktualnić dokumentację OpenAPI i plany `.ai` dla modyfikacji posiłków.
