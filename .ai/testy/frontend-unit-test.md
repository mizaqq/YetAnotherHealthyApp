### Plan testów jednostkowych — frontend

#### Cel i zakres

- **Cel**: pokryć kluczową logikę Add Meal flow oraz warstwę `lib/api.ts` testami jednostkowymi, aby szybko wykrywać regresje w walidacjach, obliczeniach i kontraktach wywołań.
- **Zakres**: `useAddMealStepper`, `MealInputStep`, `AnalysisResultsStep`, `IngredientsTable`, `MacroDisplay`, lekko `AddMealDialog`, wybrane funkcje z `lib/api.ts`.

#### Narzędzia i konwencje

- **Framework**: Vitest + @testing-library/react (+ @testing-library/user-event) + @testing-library/react-hooks (renderHook) lub test przez komponent pomocniczy.
- **Mocki**: globalny `fetch`, `supabase.auth.getSession`, metody z `lib/api` (przy testach hooka), `sonner` (wyciszenie/toasty), `Date` (deterministyczny `eaten_at`).
- **Struktura plików**: testy obok kodu lub w `apps/frontend/src/__tests__` z mirroringiem ścieżek.
- **Nazewnictwo**: `*.test.ts(x)`; układ: Arrange–Act–Assert; given/when/then w opisach.

---

### Matryca testów

#### 1) Hook `useAddMealStepper`

- Inicjalizacja: `step=input`, `isSubmitting=false`, `isCategoriesLoading=true`, puste wyniki.
- `loadCategories()`
  - Sukces: ustawia `categories`, `isCategoriesLoading=false`.
  - Błąd: `error` ustawione, `toast.error` wywołany, `isCategoriesLoading=false`.
- `handleStartAnalysis(data)` (tryb AI)
  - Woła `createAnalysisRun` z `input_text=description` i `meal_id=null`.
  - Woła `getAnalysisRunItems(run.id)` i sumuje makra; zaokrągla do 2 miejsc.
  - Przechodzi do `step=results`, ustawia `analysisRunId`, `analysisResults`, `isSubmitting=false`.
  - Błąd: powrót do `step=input`, `error` ustawione, `isSubmitting=false`.
- `handleRetryAnalysis()`
  - Gdy brak `analysisRunId`: `toast.error` i brak zmian stanu.
  - Z `analysisRunId`: `step=loading` → po sukcesie `results` z przeliczonymi i zaokrąglonymi makrami.
- `handleAcceptResults()`
  - Gdy brak `analysisResults/runId`: `toast.error` i `false`.
  - Sukces: woła `createMeal` z `source=ai`, makrami (2 miejsca), `analysis_run_id`, datą ISO; reset stanu; zwraca `true`.
  - Błąd: ustawia `error`, `isSubmitting=false`, zwraca `false`.
- `handleCreateManualMeal(data)`
  - Walidacja: `manualCalories>0` – inaczej `toast.error`, `false`.
  - Sukces: `createMeal` z `source=manual`, reset, `true`.
  - Błąd: `error` i `false`.
- `handleCancel()`
  - W `step=loading` i z `analysisRunId`: woła `cancelAnalysisRun`; końcowy stan `step=input` i czyszczenie wyników.
- `handleReset()`
  - Przywraca stan wejściowy, zachowuje `categories` i `isCategoriesLoading=false`.

Przykładowy szkielet (Vitest):

```ts
import { renderHook, act } from "@testing-library/react";
import { useAddMealStepper } from "@/hooks/useAddMealStepper";

it("sumuje i zaokrągla makra po starcie analizy", async () => {
  // mock createAnalysisRun/getAnalysisRunItems → items z ułamkami
  const { result } = renderHook(() => useAddMealStepper());
  await act(async () => {
    await result.current.handleStartAnalysis({
      category: "breakfast",
      description: "jajka",
      isManualMode: false,
      manualCalories: null,
    });
  });
  expect(result.current.step).toBe("results");
  expect(result.current.analysisResults?.totals.calories).toBeCloseTo(
    123.45,
    2
  );
});
```

#### 2) `MealInputStep`

- Walidacja (AI mode): wymagany `category` i `description` (>=3 znaki); błędy w `Field.validationMessage`.
- Walidacja (manual): wymagany `category` i `manualCalories>0`.
- Przełączanie trybu: przełączenie na manual czyści `description`; powrót czyści `manualCalories`.
- Dropdown: wybranie opcji ustawia kod kategorii; poprawne `selectedOptions` i label.
- Submit: poprawny formularz wywołuje `onSubmit` z wartościami.

#### 3) `AnalysisResultsStep`

- Renderuje `MacroDisplay` z przekazanymi makrami.
- Pusty/ustawiony `isLoading` blokuje przyciski.
- Kliknięcia wywołują `onAccept` / `onRetry` / `onCancel`.

#### 4) `IngredientsTable`

- Pusta lista: render komunikatu „Brak składników…”.
- Formatowanie: `weight_grams→toFixed(1)`, `calories→toFixed(0)`, makra `toFixed(1)`.
- Progi pewności: `<0.5` low, `>=0.5 && <0.8` medium, `>=0.8` high – klasy CSS zgodne.

#### 5) `MacroDisplay`

- Gdy `calories` nie podane: oblicza z makr (4/9/4 kcal/g).
- Gdy `calories` podane: używa podanej wartości.
- Procenty makr (z zabezpieczeniem przed dzieleniem przez 0) i zaokrąglenia.

#### 6) `AddMealDialog` (wycinek)

- Tytuł zmienia się z `step`: "Dodaj posiłek"/"Analiza posiłku"/"Wyniki analizy".
- `onClick` zamknięcia: woła `handleReset` i `onOpenChange(false)`.
- Ścieżki sukcesu: po `handleCreateManualMeal`/`handleAcceptResults` → `onSuccess()` i zamknięcie.
- Pasek błędu widoczny tylko gdy `error` i odpowiedni `step`.

#### 7) `lib/api.ts` (wybrane funkcje)

- Nagłówki i autoryzacja: dodaje `Authorization: Bearer {token}` gdy sesja jest dostępna.
- Budowa URL i query params: `getDailySummary`, `getWeeklyTrend`, `getMeals` (paginacja), `getMealDetail` (include flag), `getMealCategories` (locale).
- Mapowanie błędów: 401/404/409 → komunikaty; fallback dla innych statusów zawiera `status` i `statusText`/body.
- Brak ciała dla 204 (`deleteMeal`).

---

### Struktura i setup testów

- Ścieżki przykładowe:
  - `apps/frontend/src/__tests__/hooks/useAddMealStepper.test.ts`
  - `apps/frontend/src/__tests__/components/add-meal/MealInputStep.test.tsx`
  - `apps/frontend/src/__tests__/components/add-meal/AnalysisResultsStep.test.tsx`
  - `apps/frontend/src/__tests__/components/add-meal/IngredientsTable.test.tsx`
  - `apps/frontend/src/__tests__/components/dashboard/MacroDisplay.test.tsx`
  - `apps/frontend/src/__tests__/components/add-meal/AddMealDialog.test.tsx`
  - `apps/frontend/src/__tests__/lib/api.test.ts`
- Wspólne utilsy mocków: `apps/frontend/src/__tests__/test-utils.ts` (render, userEvent, mock session, mock fetch).
- Global setup: `apps/frontend/src/setupTests.ts` – reset mocków, wyciszenie `console.error`/`sonner`.

---

### Kryteria akceptacji

- Deterministyczne testy (zamrożony `Date`, stabilne mocki response’ów).
- Pokrycie kluczowej logiki: min. 80% linii w `useAddMealStepper`, 100% gałęzi walidacji w `MealInputStep`, progi pewności w `IngredientsTable`, ścieżki kalorii i procentów w `MacroDisplay`.
- Każda funkcja w `lib/api.ts` sprawdzona pod kątem: metoda, URL, nagłówki, obsługa kodów błędów.

---

### Plan wdrożenia (krótko)

1. Testy `MacroDisplay`, `IngredientsTable` (szybkie, deterministyczne).
2. Testy `MealInputStep` (walidacje i tryby).
3. Testy `useAddMealStepper` (najwięcej mocków i ścieżek).
4. Testy `AnalysisResultsStep` i `AddMealDialog` (akcje / widoczność).
5. Testy `lib/api.ts` (kontrakty URL/metody/nagłówki + błędy).
