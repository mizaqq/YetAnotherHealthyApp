# Plan implementacji widoku: Dodawanie/Edycja Posiłku

> **Uwaga:** Plan został zaktualizowany do używania `@fluentui/react-components` (v9) zamiast `shadcn/ui`.

## 1. Przegląd

Celem tego widoku jest umożliwienie użytkownikowi dodania nowego posiłku poprzez wieloetapowy proces (stepper). Użytkownik może wprowadzić opis posiłku w formie tekstowej, który następnie jest analizowany przez AI w celu obliczenia wartości odżywczych. Alternatywnie, użytkownik może pominąć analizę AI i wprowadzić jedynie wartość kaloryczną ręcznie. Widok obsługuje również weryfikację, edycję i ponowne przeliczenie wyników analizy przed ostatecznym zapisaniem posiłku w systemie.

## 2. Routing widoku

Widok powinien być dostępny pod ścieżką `/add-meal`. Może być zaimplementowany jako osobna strona lub jako komponent modalny uruchamiany z panelu głównego.

## 3. Struktura komponentów

Komponenty zostaną zbudowane z użyciem biblioteki `@fluentui/react-components` (v9) w celu zapewnienia spójności wizualnej i dostępności.

```
AddMealStepper (Komponent kontenerowy)
├── MealInputStep (Krok 1: Wprowadzanie danych)
│   ├── Dropdown (dla kategorii posiłku)
│   ├── Textarea (dla opisu posiłku)
│   ├── Switch (do przełączania na tryb ręczny)
│   ├── Input (dla kalorii w trybie ręcznym)
│   └── Button ("Analizuj" / "Zapisz")
├── AnalysisLoadingStep (Krok 2: Analiza AI)
│   ├── Spinner (wskaźnik ładowania)
│   └── Button ("Anuluj")
└── AnalysisResultsStep (Krok 3: Wyniki i akceptacja)
    ├── MacroDisplay (prezentacja sumy makroskładników)
    ├── IngredientsTable (tabela ze składnikami)
    └── Field group (zawierająca przyciski akcji)
        ├── Button ("Akceptuj i zapisz")
        ├── Button ("Popraw i przelicz ponownie")
        └── Button ("Anuluj")
```

## 4. Szczegóły komponentów

### `AddMealStepper`

- **Opis komponentu:** Główny kontener zarządzający logiką steppera. Przechowuje globalny stan całego procesu, zarządza aktywnym krokiem i obsługuje komunikację z API.
- **Główne elementy:** Renderuje warunkowo komponenty kroków (`MealInputStep`, `AnalysisLoadingStep`, `AnalysisResultsStep`) na podstawie aktualnego stanu.
- **Obsługiwane interakcje:** Inicjuje proces analizy, zapisu, ponowienia i anulowania.
- **Obsługiwana walidacja:** Brak – walidacja delegowana jest do komponentów podrzędnych.
- **Typy:** `AddMealViewModel`.
- **Propsy:** Brak.

### `MealInputStep`

- **Opis komponentu:** Formularz do zbierania danych wejściowych od użytkownika.
- **Główne elementy:**
  - `Field` + `Dropdown` (`@fluentui/react-components`) do wyboru kategorii posiłku (dane pobierane z API).
  - `Field` + `Textarea` (`@fluentui/react-components`) na opis posiłku.
  - `Field` + `Switch` (`@fluentui/react-components`) do przełączania między trybem AI a ręcznym.
  - `Field` + `Input` (`@fluentui/react-components`) widoczny tylko w trybie ręcznym do wprowadzenia kalorii.
  - `Button` (`@fluentui/react-components`) do wysłania formularza z `appearance="primary"`.
- **Obsługiwane interakcje:** `onSubmit`, `onModeChange`.
- **Obsługiwana walidacja:**
  - Pole `category` jest wymagane.
  - W trybie AI, pole `description` jest wymagane i nie może być puste.
  - W trybie ręcznym, pole `manualCalories` jest wymagane i musi być liczbą dodatnią.
  - Komunikaty walidacji wyświetlane za pomocą `validationMessage` w komponencie `Field`.
- **Typy:** `MealCategoryDTO[]`, `MealInputFormViewModel`.
- **Propsy:**
  - `initialData: Partial<MealInputFormViewModel>`
  - `isLoading: boolean`
  - `onSubmit: (data: MealInputFormViewModel) => void`

### `AnalysisLoadingStep`

- **Opis komponentu:** Informuje użytkownika o trwającym procesie analizy AI.
- **Główne elementy:**
  - `Spinner` (`@fluentui/react-components`) jako wizualny wskaźnik postępu z etykietą.
  - Tekst informacyjny, np. "Analizujemy Twój posiłek..." jako `label` dla `Spinner`.
  - `Button` (`@fluentui/react-components`) z `appearance="secondary"` pozwalający anulować operację.
- **Obsługiwane interakcje:** `onCancel`.
- **Obsługiwana walidacja:** Brak.
- **Typy:** Brak.
- **Propsy:**
  - `onCancel: () => void`

### `AnalysisResultsStep`

- **Opis komponentu:** Prezentuje wyniki analizy AI do weryfikacji przez użytkownika.
- **Główne elementy:**
  - `MacroDisplay`: Komponent wyświetlający sumaryczne wartości kalorii, białka, tłuszczu i węglowodanów (może użyć `Card` z `@fluentui/react-components`).
  - `IngredientsTable`: Komponent oparty na `Table`, `TableHeader`, `TableRow`, `TableCell` z `@fluentui/react-components` do wyświetlania listy składników.
  - Przyciski akcji w grupie:
    - `Button` z `appearance="primary"` dla "Akceptuj i zapisz"
    - `Button` z `appearance="secondary"` dla "Popraw i przelicz ponownie"
    - `Button` z `appearance="subtle"` dla "Anuluj"
- **Obsługiwane interakcje:** `onAccept`, `onRetry`, `onCancel`.
- **Obsługiwana walidacja:** Brak.
- **Typy:** `AnalysisResultsViewModel`.
- **Propsy:**
  - `results: AnalysisResultsViewModel`
  - `isLoading: boolean`
  - `onAccept: () => void`
  - `onRetry: () => void`
  - `onCancel: () => void`

## 5. Typy

Oprócz istniejących typów DTO z `types.ts`, potrzebne będą następujące typy ViewModel do zarządzania stanem widoku.

```typescript
// Gówny stan zarządzany przez hook useAddMealStepper
type AddMealViewModel = {
  step: "input" | "loading" | "results";
  inputData: MealInputFormViewModel;
  analysisRunId: string | null; // UUID przebiegu analizy
  analysisResults: AnalysisResultsViewModel | null;
  error: string | null;
};

// Stan formularza w pierwszym kroku
type MealInputFormViewModel = {
  category: string; // Kod kategorii, np. 'breakfast'
  description: string;
  isManualMode: boolean;
  manualCalories: number | null;
};

// Model danych dla widoku wyników
type AnalysisResultsViewModel = {
  runId: string; // UUID
  totals: {
    calories: number;
    protein: number;
    fat: number;
    carbs: number;
  };
  items: AnalysisRunItemDTO[];
};
```

## 6. Zarządzanie stanem

Logika i stan całego procesu zostaną zamknięte w customowym hooku `useAddMealStepper`.

- **`useAddMealStepper()`**
  - **Cel:** Abstrakcja logiki biznesowej, zarządzanie stanem steppera, obsługa wywołań API i błędów.
  - **Zarządzany stan:**
    - `step`: Aktualny krok (`'input'`, `'loading'`, `'results'`).
    - `formData`: Dane z formularza wejściowego.
    - `analysisRun`, `analysisItems`: Dane zwrócone przez API analizy.
    - `error`: Komunikat o błędzie do wyświetlenia użytkownikowi.
  - **Udostępniane funkcje:**
    - `handleStartAnalysis(data: MealInputFormViewModel)`: Uruchamia analizę AI.
    - `handleAcceptResults()`: Zapisuje zaakceptowany posiłek.
    - `handleRetryAnalysis()`: Wraca do kroku edycji, aby umożliwić ponowne przeliczenie.
    - `handleCreateManualMeal(data: MealInputFormViewModel)`: Zapisuje posiłek w trybie ręcznym.
    - `handleCancel()`: Anuluje proces i resetuje stan.

## 7. Integracja API

1.  **Pobranie kategorii:**
    - **Endpoint:** `GET /api/v1/meal-categories`
    - **Akcja:** Przy pierwszym renderowaniu `MealInputStep`.
    - **Cel:** Wypełnienie listy wyboru kategorii.
2.  **Rozpoczęcie analizy AI:**
    - **Endpoint:** `POST /api/v1/analysis-runs`
    - **Typ żądania:** `CreateAnalysisRunCommand` (`{ input_text: string }`)
    - **Akcja:** Po walidacji i wysłaniu formularza w `MealInputStep`.
    - **Cel:** Uruchomienie analizy. W MVP żądanie jest synchroniczne i długotrwałe.
3.  **Pobranie składników analizy:**
    - **Endpoint:** `GET /api/v1/analysis-runs/{run_id}/items`
    - **Akcja:** Po pomyślnym zakończeniu analizy.
    - **Cel:** Pobranie listy składników do wyświetlenia w `AnalysisResultsStep`.
4.  **Zapisanie posiłku (po analizie AI):**
    - **Endpoint:** `POST /api/v1/meals`
    - **Typ żądania:** `CreateMealCommand`
    - **Akcja:** Po kliknięciu "Akceptuj i zapisz" w `AnalysisResultsStep`.
    - **Cel:** Utrwalenie posiłku w bazie danych.
5.  **Zapisanie posiłku (ręcznie):**
    - **Endpoint:** `POST /api/v1/meals`
    - **Typ żądania:** `CreateMealCommand` (z `source: 'manual'`)
    - **Akcja:** Po wysłaniu formularza w trybie ręcznym.
    - **Cel:** Utrwalenie posiłku w bazie danych.
6.  **Ponowienie analizy:**
    - **Endpoint:** `POST /api/v1/analysis-runs/{run_id}/retry`
    - **Typ żądania:** `RetryAnalysisRunCommand`
    - **Akcja:** Po kliknięciu "Popraw i przelicz ponownie".
    - **Cel:** Uruchomienie nowej analizy z poprawionymi danymi.

## 8. Interakcje użytkownika

- **Krok 1:** Użytkownik wybiera kategorię, wpisuje opis, klika "Analizuj".
- **Krok 2 (przejściowy):** Interfejs jest blokowany, wyświetlany jest wskaźnik postępu. Użytkownik może anulować operację.
- **Krok 3:** Użytkownik widzi wyniki.
  - Jeśli klika "Akceptuj i zapisz", dane są wysyłane do API, a stepper jest zamykany.
  - Jeśli klika "Popraw i przelicz ponownie", jest cofany do kroku 1 z zachowaniem wprowadzonych danych do edycji.
  - Jeśli klika "Anuluj", stan jest resetowany, a stepper zamykany.
- **Tryb ręczny:** Użytkownik przełącza `Switch`, pole opisu jest zastępowane polem kalorii. Kliknięcie "Zapisz" od razu wysyła dane do API.

## 8a. Stylowanie i tematyzacja

Wszystkie komponenty powinny używać `makeStyles` z `@fluentui/react-components` do tworzenia niestandardowych stylów. Hook ten zapewnia dostęp do tokenów motywu (`tokens`), co gwarantuje spójność z motywem aplikacji.

**Przykład użycia:**

```typescript
import { makeStyles, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacingVerticalL,
    padding: tokens.spacingVerticalXL,
  },
  buttonGroup: {
    display: "flex",
    gap: tokens.spacingHorizontalM,
    justifyContent: "flex-end",
  },
});
```

**Zalecenia:**

- Używaj tokenów motywu (`tokens.colorNeutralBackground1`, `tokens.spacingVerticalM`, itp.) zamiast wartości hardkodowanych.
- Komponent `FluentProvider` powinien być już skonfigurowany w głównym pliku aplikacji (`main.tsx`) z odpowiednim motywem (`webLightTheme` lub `webDarkTheme`).
- Dla responsywności używaj media queries w `makeStyles` z dostępem do breakpointów z tokenów.

## 9. Warunki i walidacja

- **Przycisk "Analizuj" / "Zapisz" w `MealInputStep`** jest nieaktywny, dopóki:
  - Nie wybrano kategorii.
  - W trybie AI, pole opisu jest puste.
  - W trybie ręcznym, pole kalorii jest puste lub wartość jest niepoprawna (≤ 0).
- Błędy walidacji są wyświetlane pod odpowiednimi polami formularza po próbie wysłania.

## 10. Obsługa błędów

- **Błąd pobierania kategorii:** Wyświetl komunikat o błędzie za pomocą `MessageBar` z `intent="error"` z `@fluentui/react-components` i zablokuj formularz.
- **Błąd analizy AI (`POST /analysis-runs`):** Przerwij stan ładowania, cofnij do kroku 1 i wyświetl komunikat błędu zwrócony przez API za pomocą `MessageBar`.
- **Analiza zakończona statusem `failed`:** W kroku 3 wyświetl stosowną informację (`error_message` z DTO) zamiast wyników za pomocą `MessageBar` z `intent="warning"`, dając możliwość poprawy danych.
- **Błąd zapisu posiłku (`POST /meals`):** Pozostań w kroku 3 (lub 1 dla trybu ręcznego) i wyświetl komunikat o błędzie za pomocą `MessageBar`, pozwalając użytkownikowi spróbować ponownie.
- **Błędy sieciowe:** Należy obsłużyć globalnie, wyświetlając komunikat o problemie z połączeniem za pomocą `MessageBar` lub `Toast` z Fluent UI.
- **Walidacja formularza:** Błędy walidacji wyświetlane za pomocą właściwości `validationMessage` i `validationState="error"` w komponencie `Field`.

## 11. Kroki implementacji

1.  **Instalacja zależności:** Upewnij się, że w projekcie zainstalowany jest pakiet `@fluentui/react-components` w najnowszej wersji v9.
2.  **Struktura plików:** Utwórz nowy folder `src/features/add-meal/` i umieść w nim wszystkie nowe komponenty oraz hook `useAddMealStepper`.
3.  **Komponenty UI:** Zaimplementuj komponenty `MacroDisplay` i `IngredientsTable` jako komponenty reużywalne, wykorzystując komponenty z `@fluentui/react-components` (`Card`, `Table`, itp.).
4.  **Hook `useAddMealStepper`:** Zaimplementuj logikę zarządzania stanem i szkielet funkcji obsługujących interakcje (na razie bez logiki API).
5.  **Komponenty kroków:** Zbuduj `MealInputStep`, `AnalysisLoadingStep` i `AnalysisResultsStep` używając komponentów z `@fluentui/react-components` (`Field`, `Dropdown`, `Textarea`, `Switch`, `Input`, `Button`, `Spinner`, `Table`). Połącz je z propami dostarczanymi przez hook.
6.  **Stylowanie:** Użyj hooka `makeStyles` z `@fluentui/react-components` do tworzenia niestandardowych stylów z dostępem do tokenów motywu.
7.  **Integracja API:** Zaimplementuj wywołania API wewnątrz hooka `useAddMealStepper` za pomocą istniejącego klienta API (`src/lib/api.ts`).
8.  **Routing:** Dodaj nową ścieżkę `/add-meal` w głównym routerze aplikacji, która będzie renderować kontener `AddMealStepper`.
9.  **Obsługa błędów i stanów końcowych:** Upewnij się, że wszystkie możliwe błędy API są poprawnie obsługiwane i komunikowane użytkownikowi za pomocą `MessageBar` lub `Toast` z Fluent UI, a stany ładowania blokują interfejs.
10. **Testowanie:** Przetestuj manualnie cały przepływ, włączając w to ścieżkę sukcesu, ścieżkę z ponowieniem analizy, tryb ręczny oraz obsługę błędów API.
