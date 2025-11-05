# Plan implementacji widoku: Szczegóły Posiłku

## 1. Przegląd

Widok "Szczegóły Posiłku" ma na celu prezentację kompletnych informacji o pojedynczym, zapisanym posiłku. Użytkownik zobaczy w nim podsumowanie makroskładników i kalorii, kategorię posiłku, datę jego spożycia oraz, w przypadku posiłków przetworzonych przez AI, szczegółową listę składników. Widok ten stanowi również punkt wyjścia do edycji lub usunięcia posiłku.

## 2. Routing widoku

Widok będzie dostępny pod dynamiczną ścieżką, która zawiera identyfikator konkretnego posiłku.

- **Ścieżka:** `/meals/{meal_id}`
- **Parametr:** `meal_id` (UUID posiłku)

## 3. Struktura komponentów

Komponenty zostaną zorganizowane w logiczną hierarchię, gdzie komponent kontenerowy zarządza danymi i stanem, a komponenty prezentacyjne odpowiadają za renderowanie poszczególnych części interfejsu.

```
- MealDetailsPage (strona, kontener)
  - (Logika warunkowa: LoadingSpinner, ErrorMessage)
  - MealHeader (wyświetla kategorię, datę i przyciski akcji)
    - Button ("Edytuj")
    - Button ("Usuń")
  - MacroDisplay (wyświetla kalorie i makroskładniki)
  - IngredientsTable (tabela ze składnikami z analizy AI)
  - ConfirmationModal (modal do potwierdzenia usunięcia)
```

## 4. Szczegóły komponentów

### `MealDetailsPage`

- **Opis komponentu:** Główny komponent kontenerowy strony. Odpowiada za pobranie `meal_id` z URL, wywołanie API w celu pobrania danych posiłku, zarządzanie stanem (ładowanie, błąd, dane) oraz kompozycję widoku z komponentów podrzędnych.
- **Główne elementy:** `div` jako główny kontener, renderuje warunkowo `LoadingSpinner`, `ErrorMessage` lub właściwą treść strony.
- **Obsługiwane interakcje:** Inicjuje pobieranie danych przy montowaniu. Obsługuje nawigację do edycji oraz inicjuje proces usuwania.
- **Obsługiwana walidacja:** Sprawdza, czy użytkownik jest zalogowany. Reaguje na stany ładowania i błędu z API.
- **Typy:** `MealDetailViewModel`
- **Propsy:** Brak (pobiera `meal_id` z React Router).

### `MealHeader`

- **Opis komponentu:** Komponent prezentacyjny wyświetlający nazwę kategorii posiłku, sformatowaną datę spożycia oraz przyciski akcji.
- **Główne elementy:** `header`, `h1` (kategoria), `p` (data), `div` (kontener na przyciski), komponenty `Button` z biblioteki `shadcn/ui`.
- **Obsługiwane interakcje:** Kliknięcie przycisku "Edytuj", kliknięcie przycisku "Usuń".
- **Obsługiwana walidacja:** Brak.
- **Typy:** `MealHeaderViewModel`
- **Propsy:**
  - `categoryDisplayName: string`
  - `eatenAtFormatted: string`
  - `onEdit: () => void`
  - `onDelete: () => void`

### `MacroDisplay`

- **Opis komponentu:** Wyświetla kluczowe makroskładniki (kalorie, białko, tłuszcz, węglowodany) w przejrzystym, wizualnym formacie, prawdopodobnie z użyciem komponentu `Card` z `shadcn/ui`.
- **Główne elementy:** Komponent `Card`, `CardHeader`, `CardContent`, elementy `p` lub `div` dla każdej wartości makro.
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Poprawnie wyświetla wartości `null` (np. jako "-") dla posiłków ręcznych.
- **Typy:** `MacroViewModel`
- **Propsy:**
  - `macros: MacroViewModel`

### `IngredientsTable`

- **Opis komponentu:** Tabela prezentująca listę składników posiłku wygenerowaną przez AI. Wyświetla nazwę składnika, jego wagę i kaloryczność. Obsługuje przypadek braku składników.
- **Główne elementy:** Komponent `Table` z `shadcn/ui` (`TableHeader`, `TableRow`, `TableHead`, `TableBody`, `TableCell`). Alternatywnie komunikat "Brak danych o składnikach".
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Jeśli tablica składników jest pusta lub `null`, wyświetla stosowny komunikat.
- **Typy:** `IngredientViewModel[] | null`
- **Propsy:**
  - `ingredients: IngredientViewModel[] | null`

### `ConfirmationModal`

- **Opis komponentu:** Modal (okno dialogowe) służący do potwierdzenia operacji usunięcia posiłku. Zostanie zaimplementowany przy użyciu komponentu `AlertDialog` z `shadcn/ui`.
- **Główne elementy:** `AlertDialog`, `AlertDialogTrigger`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogFooter`, `AlertDialogCancel`, `AlertDialogAction`.
- **Obsługiwane interakcje:** Potwierdzenie usunięcia, anulowanie usunięcia.
- **Obsługiwana walidacja:** Brak.
- **Propsy:**
  - `isOpen: boolean`
  - `onOpenChange: (isOpen: boolean) => void`
  - `onConfirm: () => void`
  - `isDeleting: boolean` (do wyświetlania stanu ładowania na przycisku potwierdzenia)

## 5. Typy

### DTO (Data Transfer Object - z `types.ts`)

- **`MealDetailDTO`**: Surowy obiekt danych otrzymywany z API.

### ViewModel (Typy na potrzeby widoku)

- **`MealDetailViewModel`**: Główny, przetworzony model danych dla całego widoku.
  ```typescript
  type MealDetailViewModel = {
    id: string;
    categoryDisplayName: string; // Przetłumaczona nazwa kategorii, np. "Śniadanie"
    eatenAtFormatted: string; // Sformatowana data, np. "18 października 2025, 08:30"
    source: "ai" | "edited" | "manual";
    macros: MacroViewModel;
    ingredients: IngredientViewModel[] | null; // null, jeśli posiłek jest ręczny
  };
  ```
- **`MacroViewModel`**: Obiekt przechowujący wartości makroskładników.
  ```typescript
  type MacroViewModel = {
    calories: number;
    protein: number | null;
    fat: number | null;
    carbs: number | null;
  };
  ```
- **`IngredientViewModel`**: Obiekt reprezentujący pojedynczy składnik w tabeli.
  ```typescript
  type IngredientViewModel = {
    id: string;
    name: string; // Nazwa składnika
    weight: string; // Waga jako string z jednostką, np. "100 g"
    calories: number;
  };
  ```

## 6. Zarządzanie stanem

Zarządzanie stanem zostanie scentralizowane w dedykowanym customowym hooku `useMealDetails` w celu hermetyzacji logiki, poprawy czytelności i reużywalności.

- **`useMealDetails(mealId: string)`**:
  - **Przeznaczenie:** Obsługa całego cyklu życia widoku: pobieranie danych, obsługa akcji użytkownika (edycja, usuwanie), zarządzanie stanami ładowania i błędów.
  - **Wewnętrzny stan:**
    - `meal: MealDetailViewModel | null`
    - `isLoading: boolean`
    - `error: Error | null`
    - `isDeleting: boolean`
    - `isDeleteModalOpen: boolean`
  - **Zwracane wartości i funkcje:**
    - `meal`, `isLoading`, `error`
    - `handleEdit`: funkcja do nawigacji
    - `handleDelete`: funkcja otwierająca modal
    - `handleConfirmDelete`: funkcja wywołująca API usuwania
    - `handleCancelDelete`: funkcja zamykająca modal

## 7. Integracja API

Integracja z backendem będzie realizowana poprzez klienta API (np. w `src/lib/api.ts`).

- **Pobieranie szczegółów posiłku:**

  - **Endpoint:** `GET /api/v1/meals/{meal_id}`
  - **Parametry zapytania:** `include_analysis_items=true` (kluczowe do pobrania składników)
  - **Typ odpowiedzi (DTO):** `MealDetailDTO`
  - **Akcja:** Wywoływane w `useEffect` w hooku `useMealDetails` przy pierwszym renderowaniu.

- **Usuwanie posiłku:**
  - **Endpoint:** `DELETE /api/v1/meals/{meal_id}`
  - **Typ odpowiedzi:** `204 No Content`
  - **Akcja:** Wywoływane przez `handleConfirmDelete` po potwierdzeniu przez użytkownika w modalu.

## 8. Interakcje użytkownika

- **Wejście na stronę:** Użytkownik widzi wskaźnik ładowania, a następnie szczegóły posiłku lub komunikat o błędzie.
- **Kliknięcie "Edytuj":** Użytkownik zostaje przekierowany na stronę edycji posiłku (np. `/meals/{meal_id}/edit`), gdzie formularz jest wstępnie wypełniony danymi.
- **Kliknięcie "Usuń":** Otwiera się modal `ConfirmationModal` z prośbą o potwierdzenie.
- **Kliknięcie "Potwierdź" w modalu:** Przycisk pokazuje stan ładowania, wywoływane jest API usuwania. Po sukcesie użytkownik jest przekierowywany na listę posiłków (np. `/dashboard`). W razie błędu wyświetlany jest toast.
- **Kliknięcie "Anuluj" w modalu:** Modal zostaje zamknięty, stan aplikacji wraca do wyświetlania szczegółów.

## 9. Warunki i walidacja

- Komponent `IngredientsTable` nie będzie renderowany, jeśli `meal.source` ma wartość `manual`. Zamiast tego może pojawić się informacja tekstowa.
- Jeśli pole `meal.ingredients` jest puste lub `null`, tabela również nie zostanie wyświetlona, a na jej miejscu pojawi się komunikat "Brak danych o składnikach".
- Przyciski akcji ("Edytuj", "Usuń") są nieaktywne (disabled) podczas początkowego ładowania danych.

## 10. Obsługa błędów

- **Błąd 404 (Not Found):** Gdy posiłek nie istnieje lub nie należy do użytkownika, strona wyświetli dedykowany komponent błędu z komunikatem "Nie znaleziono posiłku" i przyciskiem powrotu do strony głównej.
- **Błąd sieci lub 500 (Server Error) przy pobieraniu:** Widok wyświetli ogólny komunikat o błędzie z przyciskiem "Spróbuj ponownie", który ponownie uruchomi proces pobierania danych.
- **Błąd podczas usuwania:** Modal zostanie zamknięty, a użytkownikowi zostanie wyświetlony komunikat typu toast (np. "Nie udało się usunąć posiłku"), informujący o problemie bez przeładowywania strony.

## 11. Kroki implementacji

1.  **Utworzenie struktury plików:** Stworzenie folderu `src/pages/MealDetailsPage` i plików dla komponentów: `MealDetailsPage.tsx`, `MealHeader.tsx`, `MacroDisplay.tsx`, `IngredientsTable.tsx`. `ConfirmationModal` będzie implementowany bezpośrednio w `MealDetailsPage` z użyciem `AlertDialog` z `shadcn/ui`.
2.  **Implementacja routingu:** Dodanie nowej ścieżki `/meals/:meal_id` w głównym pliku routingowym aplikacji (np. `App.tsx`), wskazującej na komponent `MealDetailsPage`.
3.  **Stworzenie custom hooka `useMealDetails`:** Zaimplementowanie całej logiki zarządzania stanem, pobierania danych i obsługi akcji w pliku `useMealDetails.ts`.
4.  **Implementacja komponentu `MealDetailsPage`:** Stworzenie głównego kontenera, który użyje hooka `useMealDetails` i będzie renderował komponenty podrzędne oraz logikę warunkową (ładowanie, błędy).
5.  **Implementacja komponentów prezentacyjnych:** Stworzenie `MealHeader`, `MacroDisplay` i `IngredientsTable` zgodnie z ich opisem, dbając o przekazywanie propsów i obsługę zdarzeń.
6.  **Dodanie typów ViewModel:** Zdefiniowanie typów `MealDetailViewModel`, `MacroViewModel` i `IngredientViewModel` w pliku `src/types.ts` lub lokalnie w folderze widoku.
7.  **Implementacja transformacji danych:** Stworzenie funkcji pomocniczej `mapMealDetailDTOToViewModel` do konwersji DTO z API na ViewModel używany przez komponenty.
8.  **Styling:** Ostylowanie wszystkich komponentów za pomocą klas `Tailwind CSS` zgodnie z design systemem aplikacji.
9.  **Testowanie i obsługa przypadków brzegowych:** Sprawdzenie działania dla posiłków typu `ai` i `manual`, obsługa błędów API, poprawne działanie modala i nawigacji.
