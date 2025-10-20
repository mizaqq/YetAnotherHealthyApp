# API Endpoint Implementation Plan: POST /api/v1/analysis-runs/{run_id}/cancel

## 1. Przegląd punktu końcowego

- Pozwala użytkownikowi natychmiast zakończyć analizę, wymuszając przejście w stan `cancelled` w ramach pojedynczego żądania.
- Zapewnia, że tylko właściciel przebiegu może wykonać anulowanie.
- Zwraca finalny stan przebiegu (po anulowaniu) bez użycia asynchronicznej kolejki.

## 2. Szczegóły żądania

- Metoda HTTP: POST
- Struktura URL: `/api/v1/analysis-runs/{run_id}/cancel`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Accept: application/json`
- Parametry:
  - Path (wymagane): `run_id` (`UUID4`)
- Body: brak (MVP nie wymaga dodatkowych danych)
- Walidacja wejścia:
  - `run_id` jako `UUID4`; błędny format → `400`.
  - Dependency auth zapewnia `user_id`; brak tokenu → `401`.
  - Serwis weryfikuje własność i aktualny status przebiegu.

## 3. Wykorzystywane typy

- `AnalysisRunCancelResponse` (`BaseModel`) z polami: `id`, `status`, `model`, `cancelled_at`, `error_code`, `error_message`.
- `AnalysisRunService.cancel_run(run_id: UUID, user_id: UUID) -> AnalysisRun`.
- `AnalysisRunRepository` metody: `get_run_by_id`, `update_status`, `replace_output`, `set_cancellation_marker` (opcjonalnie) umożliwiające synchronizację procesu.
- `CancellationNotAllowedError` (custom exception) gdy stan terminalny.

## 3. Szczegóły odpowiedzi

- Sukces: `200 OK`
- Struktura JSON:
  ```json
  {
    "id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2025-10-12T07:45:00Z",
    "error_code": "USER_CANCELLED",
    "error_message": null
  }
  ```
- Nagłówki: `Content-Type: application/json; charset=utf-8`
- Gdy przebieg już zakończony → `409 Conflict` (bez zmiany stanu).

## 4. Przepływ danych

- Handler waliduje `run_id`, pobiera `user_id` ze `get_current_user`.
- Wywołuje `AnalysisRunService.cancel_run(run_id, user_id)`.
- Serwis:
  1. Pobiera przebieg (`get_run_by_id`). Brak → `NotFound`.
  2. Weryfikuje status: jeżeli w stanie terminalnym (`succeeded`, `failed`, `cancelled`) → `CancellationNotAllowedError`.
  3. Wywołuje `update_status(run_id, user_id, status="cancelled", completed_at=now(), error_code="USER_CANCELLED")`.
  4. Jeżeli analiza jest aktualnie wykonywana (np. drugi wątek) – ustawia flagę anulacji (np. w pamięci / kolumnie) i czeka na zakończenie `AnalysisRunProcessor` (polling lub join) tak, aby odpowiedź odzwierciedlała stan końcowy.
  5. Loguje akcję (`logger.info("analysis_runs.cancel", extra={...})`).
- Handler mapuje wynik do `AnalysisRunCancelResponse` i zwraca `200` z finalnym stanem.

## 5. Względy bezpieczeństwa

- Autentykacja: Supabase JWT.
- Autoryzacja: tylko właściciel (`user_id`) może anulować; filtr w repo i RLS.
- Walidacja: wczesna weryfikacja UUID.
- Audit log: rejestrować `run_id`, `user_id`, poprzedni status, `request_id`.
- Rate limiting: globalny limit (np. 30 req/min) by uniknąć flood.

## 6. Obsługa błędów

- `400 Bad Request`: niepoprawny `run_id`.
- `401 Unauthorized`: brak/niepoprawny token.
- `404 Not Found`: przebieg nie istnieje lub nie należy do użytkownika.
- `409 Conflict`: przebieg już zakończony lub równolegle zmieniony w stan terminalny przed próbą anulacji.
- `500 Internal Server Error`: błędy Supabase lub inne nieoczekiwane wyjątki; loguj `exc_info` i `run_id`.
- Detale błędów powinny zawierać kody (`analysis_run_not_found`, `analysis_run_already_finished`).

## 7. Rozważania dotyczące wydajności

- Operacja to pojedyncza aktualizacja; korzysta z indeksu `(user_id, id)`.
- Minimalna logika – brak potrzeby dodatkowych optymalizacji.
- Monitoruj liczbę anulowań (`Counter`) i liczbę konfliktów (`Counter`), aby ocenić potrzebę usprawnień.

## 8. Kroki implementacji

1. Dodaj `AnalysisRunCancelResponse` w `app/api/v1/schemas/analysis_runs.py`.
2. Rozszerz `AnalysisRunRepository` o `update_status_if_active` (z warunkiem statusu) oraz reuse `get_run_by_id`.
3. Dodaj w `AnalysisRunService` metodę `cancel_run`, obsługującą walidację stanu.
4. Zaimplementuj endpoint w `app/api/v1/endpoints/analysis_runs.py` (`@router.post("/analysis-runs/{run_id}/cancel")`).
5. Zaktualizuj routing (`app/api/v1/router.py`) i dokumentację `responses`.
