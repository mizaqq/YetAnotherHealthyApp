# API Endpoint Implementation Plan_4: DELETE /api/v1/meals/{meal_id}

## 1. Przegląd punktu końcowego

- Realizuje miękkie usunięcie posiłku ustawiając `deleted_at`, umożliwiając przywracanie w przyszłości.
- Wykorzystywany do zarządzania historią posiłków oraz utrzymania spójności raportów.

## 2. Szczegóły żądania

- Metoda HTTP: DELETE
- Struktura URL: `/api/v1/meals/{meal_id}`
- Nagłówki: `Authorization: Bearer <JWT>`
- Parametry: `meal_id` (UUID) w ścieżce
- Walidacje wejścia: poprawny UUID; brak dodatkowych parametrów

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `204 No Content` (brak body)

## 4. Przepływ danych

- Autoryzacja JWT → `get_current_user` dostarcza `user_id`.
- Handler przekazuje `meal_id` do `MealService.soft_delete_meal` wraz z sesją bazy.
- Serwis weryfikuje, że posiłek należy do użytkownika i nie jest już usunięty.
- Aktualizuje pole `deleted_at = now()`.
- Handler zwraca `204 No Content`.

## 5. Względy bezpieczeństwa

- Dostęp tylko dla właściciela posiłku (kontrola `user_id`).
- Logowanie operacji usunięcia (audit) może być wymagane.
- Brak ujawniania informacji o istnieniu posiłków innych użytkowników (404 dla cudzych rekordów).

## 6. Obsługa błędów

- `401 Unauthorized`: brak/niepoprawny token.
- `404 Not Found`: posiłek nie istnieje lub już usunięty (jeśli polityka tak definiuje).
- `500 Internal Server Error`: błędy repozytorium; logowane i obsługiwane przez globalny handler.

## 7. Wydajność

- Ograniczona operacja aktualizacji pojedynczego rekordu; korzysta z indeksu `meals.id`.
- Możliwość batchowania logowania usunięć jeśli wymagane.

## 8. Kroki implementacji

1. Dodać metodę `MealService.soft_delete_meal` z kontrolą `user_id`.
2. Rozszerzyć repozytorium o operację aktualizacji `deleted_at`.
3. Utworzyć handler FastAPI `delete_meal` (DELETE) zwracający `204`.
4. Dodać testy integracyjne potwierdzające miękkie usunięcie i brak dostępu do cudzych rekordów.
5. Zaktualizować dokumentację OpenAPI i plany `.ai` dla usuwania posiłków.
