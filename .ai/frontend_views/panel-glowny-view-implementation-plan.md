# Plan implementacji widoku: Panel Główny (Dzisiaj)

## 1. Przegląd

Panel Główny (Dzisiaj) to główny widok aplikacji po zalogowaniu, dostępny pod głównym adresem URL (`/`). Jego celem jest dostarczenie użytkownikowi szybkiego podsumowania aktywności żywieniowej z bieżącego dnia. Widok prezentuje kluczowe wskaźniki, takie jak postęp w realizacji dziennego celu kalorycznego, podsumowanie makroskładników oraz trend spożycia kalorii z ostatniego tygodnia. Umożliwia również szybki przegląd posiłków dodanych w danym dniu.

## 2. Routing widoku

Widok Panelu Głównego będzie dostępny pod główną ścieżką aplikacji:

- **Ścieżka:** `/`

## 3. Struktura komponentów

Komponenty zostaną zorganizowane w hierarchiczną strukturę, aby zapewnić reużywalność i czytelność kodu. Głównym kontenerem będzie `DashboardPage`.

```
DashboardPage
├── DailyProgressChart
├── MacroDisplay
├── WeeklyTrendChart
└── (Renderowanie warunkowe)
    ├── if meals.length > 0: MealList
    │   └── MealListItem (wewnętrzny komponent listy)
    └── if meals.length === 0: EmptyState
```

## 4. Szczegóły komponentów

### `DashboardPage` (Kontener widoku)

- **Opis komponentu:** Główny komponent strony, odpowiedzialny za orkiestrację danych, zarządzanie stanami ładowania i błędów oraz renderowanie odpowiednich komponentów podrzędnych.
- **Główne elementy:** `div` jako główny kontener z siatką (grid) do ułożenia komponentów `DailyProgressChart`, `MacroDisplay`, `WeeklyTrendChart` i `MealList`/`EmptyState`.
- **Obsługiwane interakcje:** Brak bezpośrednich interakcji. Inicjuje pobieranie danych przy montowaniu.
- **Obsługiwana walidacja:** Sprawdza, czy dane są w trakcie ładowania lub czy wystąpił błąd, aby wyświetlić odpowiedni interfejs (np. loader, komunikat o błędzie).
- **Typy:** `DailySummaryReportDTO`, `WeeklyTrendReportDTO`.
- **Propsy:** Brak.

### `DailyProgressChart`

- **Opis komponentu:** Wizualizuje postęp dziennego spożycia kalorii w stosunku do celu użytkownika. Zostanie zaimplementowany przy użyciu biblioteki `shadcn/charts` (np. `ChartContainer` z `RadialChart`).
- **Główne elementy:** Komponent wykresu (np. `<RadialChart />`), który wyświetla procentowy postęp. Będzie zawierał etykietę z bieżącą liczbą spożytych kalorii.
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Poprawnie obsługuje przypadek, gdy cel kaloryczny wynosi 0 (wyświetla 0% lub odpowiedni komunikat).
- **Typy:** `number`.
- **Propsy:**
  - `currentCalories: number`
  - `goalCalories: number | null | undefined`

### `MacroDisplay`

- **Opis komponentu:** Wyświetla sumaryczne wartości spożytych makroskładników (białko, tłuszcze, węglowodany) w ciągu dnia.
- **Główne elementy:** Komponent `Card` z `shadcn/ui`, zawierający trzy oddzielne sekcje, każda z ikoną, etykietą (np. "Białko") i wartością (np. "120g").
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Wyświetla `0g` dla każdej wartości, jeśli dane nie są dostępne.
- **Typy:** `DailySummaryReportDTO['totals']`.
- **Propsy:**
  - `macros: { protein: number, fat: number, carbs: number }`

### `WeeklyTrendChart`

- **Opis komponentu:** Prezentuje wykres słupkowy lub liniowy pokazujący trend spożycia kalorii w ciągu ostatnich 7 dni. Zostanie zaimplementowany przy użyciu `shadcn/charts` (np. `BarChart`).
- **Główne elementy:** Komponent `<BarChart />` z osiami X (daty) i Y (kalorie). Wykres powinien zawierać linię referencyjną wskazującą dzienny cel kaloryczny.
- **Obsługiwane interakcje:** Hover nad słupkiem może wyświetlać tooltip ze szczegółowymi danymi (data, kalorie, cel).
- **Obsługiwana walidacja:** Poprawnie renderuje dni z zerowym spożyciem kalorii.
- **Typy:** `WeeklyTrendReportPointDTO[]`.
- **Propsy:**
  - `data: WeeklyTrendReportPointDTO[]`

### `MealList`

- **Opis komponentu:** Renderuje listę posiłków dodanych w bieżącym dniu. Każdy element listy jest klikalny i prowadzi do szczegółów posiłku.
- **Główne elementy:** Uporządkowana lista (`<ol>` lub `<ul>`), gdzie każdy element (`<li>`) jest komponentem `Card` z `shadcn/ui` i zawiera nazwę kategorii, godzinę spożycia oraz liczbę kalorii.
- **Obsługiwane interakcje:** Kliknięcie elementu listy.
- **Obsługiwana walidacja:** Komponent jest renderowany tylko wtedy, gdy lista posiłków nie jest pusta.
- **Typy:** `Array<Pick<MealRow, "id" | "category" | "calories" | "eaten_at">>`
- **Propsy:**
  - `meals: Array<Pick<MealRow, "id" | "category" | "calories" | "eaten_at">>`

### `EmptyState`

- **Opis komponentu:** Komponent wyświetlany, gdy użytkownik nie dodał jeszcze żadnego posiłku w danym dniu.
- **Główne elementy:** Kontener z grafiką lub ikoną, nagłówkiem (np. "Nie dodałeś jeszcze posiłku") oraz przyciskiem `Button` z `shadcn/ui` z wezwaniem do działania (np. "Dodaj pierwszy posiłek").
- **Obsługiwane interakcje:** Kliknięcie przycisku "Dodaj posiłek".
- **Obsługiwana walidacja:** Renderowany tylko wtedy, gdy lista posiłków jest pusta.
- **Typy:** Brak.
- **Propsy:** Brak.

## 5. Typy

Implementacja będzie bazować na istniejących typach DTO zdefiniowanych w `apps/frontend/src/types.ts`. Nie przewiduje się tworzenia złożonych, nowych typów ViewModel, ponieważ DTO dobrze mapują się na potrzeby widoku.

- **`DailySummaryReportDTO`**: Główny typ danych dla podsumowania dnia, używany przez `DailyProgressChart`, `MacroDisplay` i `MealList`.
- **`WeeklyTrendReportDTO`**: Główny typ danych dla wykresu trendu tygodniowego, używany przez `WeeklyTrendChart`.
- **`WeeklyTrendReportPointDTO`**: Typ pojedynczego punktu danych na wykresie tygodniowym.
- **`MealRow`**: Typ posiłku. Podzbiór pól tego typu będzie używany w liście posiłków.

## 6. Zarządzanie stanem

Stan widoku będzie zarządzany lokalnie w komponencie `DashboardPage` przy użyciu hooków `useState` i `useEffect`. Aby usprawnić logikę i oddzielić ją od prezentacji, zostanie stworzony customowy hook `useDashboardData`.

- **`useDashboardData` Hook:**
  - **Cel:** Zamknięcie w jednym miejscu logiki pobierania danych dla panelu, obsługi stanu ładowania oraz błędów.
  - **Stany wewnętrzne:**
    - `dailySummary: DailySummaryReportDTO | null`
    - `weeklyTrend: WeeklyTrendReportDTO | null`
    - `isLoading: boolean`
    - `error: Error | null`
  - **Zwracane wartości:** Obiekt zawierający powyższe stany oraz wartości pochodne, np. `hasMeals: boolean`.
  - **Działanie:** W `useEffect` (uruchamianym jednorazowo) będzie równolegle pobierał dane z obu wymaganych endpointów za pomocą `Promise.all`.

## 7. Integracja API

Widok będzie korzystał z dwóch endpointów API:

1.  **Podsumowanie dzienne:**

    - **Endpoint:** `GET /api/v1/reports/daily-summary`
    - **Opis:** Pobiera zagregowane dane o posiłkach, makroskładnikach i celu kalorycznym na dany dzień (domyślnie dzisiaj).
    - **Typ odpowiedzi:** `DailySummaryReportDTO`

2.  **Trend tygodniowy:**
    - **Endpoint:** `GET /api/v1/reports/weekly-trend`
    - **Uwaga:** Ten endpoint jest **zakładany** na podstawie typu `WeeklyTrendReportDTO` i wymagań. Należy go zaimplementować w backendzie.
    - **Opis:** Pobiera dane o spożyciu kalorii z ostatnich 7 dni.
    - **Typ odpowiedzi:** `WeeklyTrendReportDTO`

Wszystkie wywołania API będą realizowane przez klienta API (`apps/frontend/src/lib/api.ts`), który powinien automatycznie dołączać nagłówki autoryzacyjne.

## 8. Interakcje użytkownika

- **Ładowanie widoku:** Użytkownik wchodzi na stronę (`/`). Wyświetlany jest wskaźnik ładowania. Po pobraniu danych, renderowany jest pełny panel.
- **Kliknięcie na posiłek:** Użytkownik klika element na liście posiłków. Aplikacja przechodzi do widoku szczegółów tego posiłku (np. `/meals/{mealId}`).
- **Dodanie posiłku (ze stanu pustego):** Użytkownik klika przycisk "Dodaj posiłek". Aplikacja przechodzi do formularza dodawania nowego posiłku.

## 9. Warunki i walidacja

- **Uwierzytelnienie:** Widok jest dostępny tylko dla zalogowanych użytkowników. Globalna obsługa autoryzacji powinna przekierować niezalogowanego użytkownika na stronę logowania.
- **Brak posiłków:** Jeśli API zwróci pustą tablicę `meals` w `DailySummaryReportDTO`, komponent `DashboardPage` warunkowo wyrenderuje komponent `EmptyState` zamiast `MealList`.
- **Brak celu kalorycznego:** Jeśli `calorie_goal` w odpowiedzi API ma wartość `null` lub `0`, `DailyProgressChart` powinien wyświetlić 0% postępu.

## 10. Obsługa błędów

- **Błąd pobierania danych (np. błąd serwera 500):** Hook `useDashboardData` przechwyci błąd i ustawi stan `error`. Komponent `DashboardPage` wyświetli ogólny komunikat o błędzie (np. "Nie udało się załadować danych. Spróbuj odświeżyć stronę.") oraz przycisk do ponowienia próby.
- **Brak profilu użytkownika (błąd 404):** Jeśli API zwróci błąd 404 (np. użytkownik nie ukończył onboardingu), widok powinien wyświetlić dedykowany komunikat z wezwaniem do uzupełnienia profilu i linkiem do odpowiedniej strony.

## 11. Kroki implementacji

1.  **Przygotowanie środowiska:**
    - Zainstaluj bibliotekę do wykresów: `npx shadcn-ui@latest add charts`.
2.  **Stworzenie customowego hooka `useDashboardData`:**
    - Zaimplementuj logikę pobierania danych z `/api/v1/reports/daily-summary` oraz (zakładanego) `/api/v1/reports/weekly-trend`.
    - Dodaj zarządzanie stanami `isLoading` i `error`.
3.  **Implementacja komponentów-liści:**
    - Stwórz komponent `DailyProgressChart` używając `RadialChart` z `shadcn/charts`.
    - Stwórz komponent `MacroDisplay` używając `Card` z `shadcn/ui`.
    - Stwórz komponent `WeeklyTrendChart` używając `BarChart` z `shadcn/charts`.
    - Stwórz komponent `MealList` oraz jego wewnętrzny element `MealListItem`.
    - Stwórz komponent `EmptyState` z przyciskiem nawigującym do dodawania posiłku.
4.  **Implementacja kontenera `DashboardPage`:**
    - Użyj hooka `useDashboardData` do pobrania danych i stanów.
    - Zaimplementuj logikę renderowania warunkowego (loader, komunikat o błędzie, `MealList` vs `EmptyState`).
    - Złóż layout strony, przekazując dane do odpowiednich komponentów podrzędnych.
5.  **Routing:**
    - Upewnij się, że komponent `DashboardPage` jest renderowany dla ścieżki `/` w głównym pliku routingu aplikacji.
6.  **Stylowanie i responsywność:**
    - Użyj klas Tailwind CSS, aby zapewnić responsywność layoutu na różnych urządzeniach (mobile, tablet, desktop).
