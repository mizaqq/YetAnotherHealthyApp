# Plan implementacji widoku Historia

## 1. Przegląd

Widok "Historia" (`/history`) stanowi centralne miejsce, w którym użytkownik może przeglądać pełną, chronologiczną listę swoich zapisanych posiłków. Głównym celem jest umożliwienie łatwego monitorowania przeszłej aktywności żywieniowej. Na górze widoku znajduje się wykres trendu spożycia kalorii z ostatnich 7 dni. Poniżej, główna część interfejsu to lista posiłków, grupowana według dat i ładowana dynamicznie za pomocą mechanizmu "infinite scroll", co zapewnia płynne i wydajne przeglądanie danych bez potrzeby paginacji.

## 2. Routing widoku

Widok będzie dostępny pod następującą ścieżką w aplikacji:

- **Ścieżka:** `/history`

## 3. Struktura komponentów

Komponenty zostaną zorganizowane w hierarchiczną strukturę, aby zapewnić reużywalność i czytelność kodu.

```
/src/pages/HistoryView.tsx
|
|-- /src/components/history/WeeklyTrendChart.tsx
|
`-- /src/components/history/MealHistoryList.tsx
    |
    |-- /src/components/history/DateGroupHeader.tsx
    |
    |-- /src/components/history/MealListItem.tsx
    |
    `-- /src/components/ui/InfiniteScrollLoader.tsx
```

## 4. Szczegóły komponentów

### `HistoryView`

- **Opis komponentu:** Główny komponent strony, odpowiedzialny za routing i ogólny układ. Inicjuje pobieranie danych dla wykresu trendu i renderuje komponenty podrzędne.
- **Główne elementy:** `div` jako kontener, komponent `WeeklyTrendChart`, komponent `MealHistoryList`.
- **Obsługiwane interakcje:** Brak bezpośrednich interakcji.
- **Obsługiwana walidacja:** Brak.
- **Typy:** `WeeklyTrendReportDTO`.
- **Propsy:** Brak.

### `WeeklyTrendChart`

- **Opis komponentu:** Wyświetla wizualizację trendu spożycia kalorii z ostatnich 7 dni. Użyje biblioteki do wykresów (np. Recharts) lub zostanie zaimplementowany jako prosty wykres słupkowy przy użyciu SVG i Tailwind CSS.
- **Główne elementy:** Komponenty z biblioteki do wykresów lub elementy `<svg>`, `<rect>`, `<text>`.
- **Obsługiwane interakcje:** Brak (tylko do odczytu).
- **Obsługiwana walidacja:** Komponent powinien poprawnie obsłużyć przypadek, gdy dane wejściowe są puste lub niekompletne (np. wyświetlić stan pusty).
- **Typy:** `WeeklyTrendReportDTO`, `WeeklyTrendReportPointDTO`.
- **Propsy:** `data: WeeklyTrendReportDTO`.

### `MealHistoryList`

- **Opis komponentu:** Zarządza logiką pobierania, grupowania i wyświetlania listy posiłków. Wykorzystuje customowy hook `useMealHistory` do zarządzania stanem i komunikacji z API. Renderuje grupy posiłków pod nagłówkami z datą.
- **Główne elementy:** `ul` jako kontener listy, mapowanie po `GroupedMealViewModel` do renderowania `DateGroupHeader` i `MealListItem`, komponent `InfiniteScrollLoader` na końcu listy.
- **Obsługiwane interakcje:** Scrollowanie, które inicjuje ładowanie kolejnych porcji danych.
- **Obsługiwana walidacja:** Brak.
- **Typy:** `MealListItemDTO`, `GroupedMealViewModel`.
- **Propsy:** Brak.

### `DateGroupHeader`

- **Opis komponentu:** Prosty komponent wyświetlający nagłówek dla grupy posiłków z danej daty (np. "Dzisiaj", "Wczoraj", "16 października 2025").
- **Główne elementy:** `li` z nagłówkiem `h2` lub `h3` dla semantyki.
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Brak.
- **Typy:** `string`.
- **Propsy:** `date: string`.

### `MealListItem`

- **Opis komponentu:** Reprezentuje pojedynczy posiłek na liście. Wyświetla kluczowe informacje: kategorię posiłku (np. "Śniadanie"), godzinę spożycia oraz liczbę kalorii. Cały element jest klikalny i prowadzi do strony szczegółów posiłku.
- **Główne elementy:** `li > Link` (z `react-router-dom`), zawierający `div` z informacjami (ikona kategorii, nazwa, czas) oraz osobny `div` z wartością kalorii.
- **Obsługiwane interakcje:** `onClick` (poprzez `Link`) nawiguje do `/meals/{meal.id}`.
- **Obsługiwana walidacja:** Brak.
- **Typy:** `MealListItemDTO`.
- **Propsy:** `meal: MealListItemDTO`.

### `InfiniteScrollLoader`

- **Opis komponentu:** Odpowiada za detekcję, kiedy użytkownik przewinie listę do końca. Po pojawieniu się w widoku, wywołuje funkcję zwrotną w celu załadowania kolejnej partii danych. Wyświetla również wskaźnik ładowania.
- **Główne elementy:** `div` z referencją (ref) do obserwacji przecięcia (Intersection Observer). Wewnątrz warunkowo renderowany komponent `Spinner` (wskaźnik ładowania).
- **Obsługiwane interakcje:** Wywołanie `onLoadMore` po wejściu w viewport.
- **Obsługiwana walidacja:** Brak.
- **Propsy:** `onLoadMore: () => void`, `isLoading: boolean`, `hasMore: boolean`.

## 5. Typy

Do implementacji widoku wykorzystane zostaną istniejące typy DTO z `types.ts` oraz zdefiniowany zostanie nowy typ `ViewModel` do obsługi grupowania danych w interfejsie.

- **`MealListItemDTO` (istniejący):** Obiekt transferu danych dla pojedynczego posiłku z API.
- **`PaginatedResponse<T>` (istniejący):** Ogólny typ dla odpowiedzi z paginacją.
- **`WeeklyTrendReportDTO` (istniejący):** DTO dla danych wykresu trendu.
- **`GroupedMealViewModel` (nowy):** Struktura używana po stronie klienta do renderowania listy posiłków pogrupowanych według daty.
  ```typescript
  // Ten typ zostanie zdefiniowany w pliku komponentu MealHistoryList lub w dedykowanym pliku z typami widoku.
  type GroupedMealViewModel = {
    // Data w formacie YYYY-MM-DD używana jako klucz grupy.
    date: string;
    // Lista posiłków należących do tej grupy.
    meals: MealListItemDTO[];
  };
  ```

## 6. Zarządzanie stanem

Zarządzanie stanem zostanie podzielone na dwie części: stan globalny widoku i stan lokalny listy posiłków, który zostanie wyabstrahowany do customowego hooka.

- **Stan w `HistoryView`:**

  - `weeklyTrendData: WeeklyTrendReportDTO | null`
  - `isLoadingTrend: boolean`
  - `trendError: Error | null`
    Zarządzane za pomocą `useState` i `useEffect` do jednorazowego pobrania danych wykresu.

- **Custom Hook `useMealHistory()`:**
  Hook ten będzie zarządzał całą logiką związaną z listą posiłków.
  - **Cel:** Hermetyzacja logiki pobierania, paginacji, grupowania, ładowania i obsługi błędów dla historii posiłków.
  - **Stan wewnętrzny:**
    - `groupedMeals: GroupedMealViewModel[]`
    - `isLoading: boolean`
    - `error: Error | null`
    - `hasMore: boolean`
    - `nextCursor: string | null`
  - **Zwracane wartości:** `groupedMeals`, `isLoading`, `error`, `loadMoreMeals` (funkcja).

## 7. Integracja API

Widok będzie korzystał z trzech endpointów API.

1.  **Pobieranie trendu tygodniowego:**

    - **Endpoint:** `GET /api/v1/reports/weekly-trend`
    - **Akcja:** Wywoływany raz przy montowaniu komponentu `HistoryView`.
    - **Typ odpowiedzi:** `WeeklyTrendReportDTO`.

2.  **Pobieranie listy posiłków (z paginacją):**

    - **Endpoint:** `GET /api/v1/meals`
    - **Akcja:** Wywoływany przy montowaniu `MealHistoryList` (pierwsza strona) oraz za każdym razem, gdy `InfiniteScrollLoader` wywoła `loadMoreMeals`.
    - **Parametry zapytania:**
      - `page[size]`: stała wartość, np. 20.
      - `page[after]`: kursor do następnej strony, pobrany z poprzedniej odpowiedzi.
    - **Typ odpowiedzi:** `PaginatedResponse<MealListItemDTO>`.

3.  **Pobieranie profilu użytkownika (opcjonalnie, jeśli cel kaloryczny nie jest w innych odpowiedziach):**
    - **Endpoint:** `GET /api/v1/profile`
    - **Akcja:** Może być potrzebne, jeśli `WeeklyTrendReportDTO` nie zawiera celu kalorycznego.
    - **Typ odpowiedzi:** `ProfileDTO`.

## 8. Interakcje użytkownika

- **Wejście na stronę `/history`:**
  - Aplikacja wyświetla szkielet interfejsu (loading skeleton).
  - Rozpoczyna się pobieranie danych dla wykresu trendu oraz pierwszej strony listy posiłków.
  - Po załadowaniu, dane są wyświetlane.
- **Przewijanie listy w dół:**
  - Gdy użytkownik dotrze do końca listy, komponent `InfiniteScrollLoader` staje się widoczny.
  - Wywoływana jest funkcja `loadMoreMeals`.
  - Na dole listy pojawia się wskaźnik ładowania.
  - Nowe posiłki są dołączane do listy, a wskaźnik ładowania znika.
- **Kliknięcie na element posiłku:**
  - Użytkownik zostaje przekierowany na stronę szczegółów danego posiłku, np. `/meals/123e4567-e89b-12d3-a456-426614174000`.

## 9. Warunki i walidacja

Interfejs będzie weryfikował stan aplikacji i danych, aby dostosować widok:

- **Stan ładowania (początkowy):** Komponent `HistoryView` wyświetla szkielet ładowania (placeholdery) dla wykresu i listy.
- **Stan ładowania (kolejne strony):** `InfiniteScrollLoader` wyświetla wskaźnik ładowania.
- **Stan pusty:** Jeśli API zwróci pustą listę posiłków, `MealHistoryList` wyświetli komunikat "Nie masz jeszcze żadnych zapisanych posiłków."
- **Koniec listy:** Gdy API zwróci odpowiedź bez kursora `page.after`, `hasMore` jest ustawiane na `false`, a `InfiniteScrollLoader` przestaje być aktywny i wyświetlać wskaźnik ładowania.

## 10. Obsługa błędów

- **Błąd pobierania danych wykresu:** W miejscu komponentu `WeeklyTrendChart` wyświetlany jest komunikat o błędzie, np. "Nie udało się załadować trendu." z przyciskiem "Spróbuj ponownie".
- **Błąd początkowego pobierania listy posiłków:** W miejscu `MealHistoryList` wyświetlany jest komunikat o błędzie z przyciskiem "Spróbuj ponownie".
- **Błąd podczas doładowywania kolejnych posiłków:** `InfiniteScrollLoader` wyświetla komunikat o błędzie i przycisk "Spróbuj ponownie", który ponownie wywołuje `loadMoreMeals`.
- **Błąd 401 Unauthorized:** Globalna obsługa błędów (np. w interceptorze `axios` lub kliencie API) powinna przechwycić ten błąd i przekierować użytkownika na stronę logowania.

## 11. Kroki implementacji

1.  **Utworzenie struktury plików:** Stworzenie plików dla komponentów: `HistoryView.tsx`, `WeeklyTrendChart.tsx`, `MealHistoryList.tsx`, `DateGroupHeader.tsx`, `MealListItem.tsx` oraz `InfiniteScrollLoader.tsx`.
2.  **Implementacja `HistoryView`:** Dodanie routingu i podstawowego układu. Implementacja logiki pobierania danych dla `WeeklyTrendChart`.
3.  **Implementacja `WeeklyTrendChart`:** Stworzenie komponentu wizualizującego dane z propsów.
4.  **Stworzenie `useMealHistory` hook:** Zaimplementowanie całej logiki stanu dla listy posiłków: pobieranie danych, paginacja, obsługa stanu ładowania i błędów.
5.  **Stworzenie funkcji grupującej:** Implementacja czystej funkcji `groupMealsByDate(meals: MealListItemDTO[]): GroupedMealViewModel[]` używanej wewnątrz hooka.
6.  **Implementacja `MealHistoryList`:** Użycie hooka `useMealHistory` i renderowanie listy na podstawie `groupedMeals`, włączając `DateGroupHeader` i `MealListItem`.
7.  **Implementacja `MealListItem` i `DateGroupHeader`:** Stworzenie komponentów wizualnych zgodnie z projektem.
8.  **Implementacja `InfiniteScrollLoader`:** Stworzenie komponentu z użyciem `IntersectionObserver API` (lub biblioteki, np. `react-intersection-observer`).
9.  **Obsługa stanów:** Dodanie obsługi stanów ładowania, pustego i błędów we wszystkich odpowiednich komponentach.
10. **Stylowanie:** Zastosowanie Tailwind CSS i komponentów `shadcn/ui` do ostylowania wszystkich elementów widoku.
11. **Testowanie manualne:** Sprawdzenie wszystkich interakcji, obsługi błędów i przypadków brzegowych.
