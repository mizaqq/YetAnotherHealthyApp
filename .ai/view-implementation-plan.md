# API Endpoint Implementation Plan: GET /api/v1/reports/weekly-trend

## 1. Przegląd punktu końcowego

Celem tego punktu końcowego jest dostarczenie 7-dniowego, kroczącego trendu spożycia kalorii dla uwierzytelnionego użytkownika. Odpowiedź będzie zawierać dzienne podsumowanie kalorii w odniesieniu do dziennego celu użytkownika. Opcjonalnie, odpowiedź może również zawierać sumę makroskładników. Endpoint uwzględnia dni bez zarejestrowanych posiłków, zwracając dla nich wartość 0.

## 2. Szczegóły żądania

- **Metoda HTTP:** `GET`
- **Struktura URL:** `/api/v1/reports/weekly-trend`
- **Parametry:**
  - **Opcjonalne:**
    - `end_date` (string, format `YYYY-MM-DD`): Data końcowa 7-dniowego okresu. Domyślnie ustawiana na bieżącą datę po stronie serwera.
    - `include_macros` (boolean): Jeśli `true`, odpowiedź będzie zawierać sumaryczne wartości makroskładników (białko, tłuszcze, węglowodany) dla każdego dnia. Domyślnie `false`.

## 3. Wykorzystywane typy DTO

Zostaną zdefiniowane następujące modele Pydantic w `apps/backend/app/api/v1/schemas/reports.py`:

```python
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class ReportPointDTO(BaseModel):
    date: date
    calories: float
    goal: float
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None

    class Config:
        from_attributes = True

class WeeklyTrendReportDTO(BaseModel):
    start_date: date
    end_date: date
    points: List[ReportPointDTO]

    class Config:
        from_attributes = True
```

## 4. Szczegóły odpowiedzi

- **Sukces (200 OK):**

  - **Content-Type:** `application/json`
  - **Body:** Obiekt JSON zgodny ze schematem `WeeklyTrendReportDTO`.

  ```json
  {
    "start_date": "2025-10-06",
    "end_date": "2025-10-12",
    "points": [
      {
        "date": "2025-10-06",
        "calories": 1950.5,
        "goal": 2000.0,
        "protein": 150.0,
        "fat": 70.0,
        "carbs": 180.5
      },
      {
        "date": "2025-10-07",
        "calories": 0.0,
        "goal": 2000.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0
      }
    ]
  }
  ```

  _Pola `protein`, `fat`, `carbs` będą obecne tylko, gdy `include_macros=true`._

## 5. Przepływ danych

1.  Żądanie `GET` trafia do endpointu `/api/v1/reports/weekly-trend`.
2.  Zależność (dependency) `get_current_user` weryfikuje token JWT i pobiera `user_id` uwierzytelnionego użytkownika.
3.  Funkcja endpointu w `reports.py` wywołuje metodę `get_weekly_trend` z `ReportsService`, przekazując `user_id` oraz sparsowane parametry `end_date` i `include_macros`.
4.  `ReportsService` oblicza 7-dniowy zakres dat.
5.  Serwis wywołuje metodę w `ReportsRepository` w celu pobrania zagregowanych danych o posiłkach (`sum(calories)`, `sum(protein)` itd.) z tabeli `public.meals` dla danego `user_id` i zakresu dat.
6.  Serwis wywołuje również metodę w `ProfileRepository` w celu pobrania `daily_calorie_goal` z tabeli `public.profiles`.
7.  `ReportsService` przetwarza wyniki: tworzy listę 7 obiektów `ReportPointDTO`, po jednym dla każdego dnia w zakresie, uzupełniając dni bez posiłków wartościami zerowymi.
8.  Serwis zwraca obiekt `WeeklyTrendReportDTO` do funkcji endpointu.
9.  FastAPI serializuje obiekt DTO do formatu JSON i zwraca odpowiedź `200 OK` do klienta.

## 6. Względy bezpieczeństwa

- **Uwierzytelnianie:** Endpoint musi być chroniony. Dostęp będzie wymagał ważnego tokenu JWT Bearer, który zostanie zweryfikowany przez zależność `get_current_user`.
- **Autoryzacja:** Wszystkie zapytania do bazy danych muszą być filtrowane po `user_id` uzyskanym z tokenu. Uniemożliwi to dostęp do danych innych użytkowników. Mechanizmy Row Level Security w Supabase stanowią dodatkową warstwę ochrony na poziomie bazy danych.

## 7. Obsługa błędów

- **400 Bad Request:** Zwracany, gdy parametr `end_date` jest w nieprawidłowym formacie. Obsługiwane automatycznie przez FastAPI.
- **401 Unauthorized:** Zwracany, gdy token JWT jest nieobecny, nieważny lub wygasł. Obsługiwane przez zależność `get_current_user`.
- **500 Internal Server Error:** Zwracany w przypadku nieoczekiwanego błędu serwera, np. problemu z połączeniem z bazą danych.

## 8. Rozważania dotyczące wydajności

- **Indeksowanie bazy danych:** Zapytanie agregujące dane o posiłkach będzie filtrować po kolumnach `user_id` i `eaten_at`. Należy upewnić się, że istnieje złożony indeks na tych kolumnach w tabeli `meals`, aby zapewnić wysoką wydajność. Zgodnie z `@db-plan.md`, indeks `meals_user_id_eaten_at_idx` już istnieje.
- **Agregacja w bazie danych:** Obliczenia (sumowanie kalorii i makroskładników) powinny być wykonywane bezpośrednio w zapytaniu SQL (`SUM(...)` i `GROUP BY`), aby zminimalizować ilość danych przesyłanych między bazą a aplikacją oraz zmniejszyć obciążenie serwera aplikacyjnego.

## 9. Etapy wdrożenia

1.  **Model DTO:** Utworzyć plik `apps/backend/app/api/v1/schemas/reports.py` i zdefiniować w nim modele `ReportPointDTO` oraz `WeeklyTrendReportDTO`.
2.  **Repozytorium:** Utworzyć plik `apps/backend/app/db/repositories/reports_repository.py`. Dodać klasę `ReportsRepository` z metodą `get_aggregated_meals_for_date_range(user_id, start_date, end_date)`, która wykona zapytanie SQL agregujące dane z tabeli `meals`.
3.  **Serwis:** Utworzyć plik `apps/backend/app/services/reports_service.py`. Dodać klasę `ReportsService`, która będzie wstrzykiwać `ReportsRepository` i `ProfileRepository`. Zaimplementować metodę `get_weekly_trend(...)` realizującą logikę biznesową opisaną w sekcji "Przepływ danych".
4.  **Endpoint API:** Utworzyć plik `apps/backend/app/api/v1/endpoints/reports.py`. Dodać `APIRouter` i zdefiniować ścieżkę `GET /weekly-trend`, która wstrzykuje `ReportsService` i `get_current_user` jako zależności.
5.  **Integracja routera:** W pliku `apps/backend/app/api/v1/api.py` zaimportować i dołączyć router z `reports.py` do głównego routera API.
6.  **Testy:** Dodać testy jednostkowe dla `ReportsService` oraz testy integracyjne dla nowego punktu końcowego, aby zweryfikować poprawność działania, obsługę przypadków brzegowych (np. brak posiłków) i bezpieczeństwo.
