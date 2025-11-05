# Plan implementacji widoku Onboarding

## 1. Przegląd

Widok Onboarding jest pierwszym ekranem, który widzi nowy użytkownik po pomyślnej rejestracji i zalogowaniu. Jego głównym celem jest zebranie od użytkownika informacji o dziennym celu kalorycznym, co jest niezbędne do korzystania z podstawowych funkcji aplikacji, takich jak śledzenie postępów. Widok składa się z prostego formularza z jednym polem i jest krokiem obowiązkowym. Po jego pomyślnym ukończeniu użytkownik jest przekierowywany do głównego panelu aplikacji.

## 2. Routing widoku

Widok powinien być dostępny pod chronioną ścieżką `/onboarding`. Dostęp do tej ścieżki powinien być ograniczony do uwierzytelnionych użytkowników, którzy nie ukończyli jeszcze procesu onboardingu (tj. ich profil w bazie danych nie ma ustawionej daty w `onboarding_completed_at`). Próba dostępu do innych części aplikacji przez takiego użytkownika powinna skutkować przekierowaniem na `/onboarding`. Użytkownik, który ukończył onboarding i próbuje wejść na `/onboarding`, powinien zostać przekierowany do panelu głównego (np. `/`).

## 3. Struktura komponentów

Hierarchia komponentów dla widoku Onboarding będzie wyglądać następująco:

```
<OnboardingView>
  ├── <h1> (np. "Ustaw swój dzienny cel")
  ├── <p> (np. "Podaj swój cel kaloryczny, abyśmy mogli...")
  └── <OnboardingForm>
      ├── <CalorieGoalInput>
      │   ├── <Label>
      │   ├── <Input type="number">
      │   └── <ErrorMessage>
      └── <Button type="submit"> ("Zapisz i kontynuuj")
```

- **`OnboardingView`**: Główny komponent strony, odpowiedzialny za ogólny układ i orkiestrację stanu.
- **`OnboardingForm`**: Komponent formularza, który zarządza wprowadzaniem danych, walidacją i procesem wysyłki.
- **`CalorieGoalInput`**: Komponent wejściowy dla celu kalorycznego, opakowujący standardowy input z `shadcn/ui` z etykietą i obsługą błędów.
- **`Button`**: Przycisk `shadcn/ui` do wysłania formularza, obsługujący stan ładowania.

## 4. Szczegóły komponentów

### `OnboardingView`

- **Opis komponentu**: Strona kontenera, która centruje zawartość i zarządza logiką wywołania API poprzez niestandardowy hook `useOnboarding`.
- **Główne elementy**: Nagłówki `h1`, `p` oraz komponent `OnboardingForm`.
- **Obsługiwane interakcje**: Brak bezpośrednich interakcji, deleguje logikę do `OnboardingForm`.
- **Obsługiwana walidacja**: Brak.
- **Typy**: `OnboardingViewModel`.
- **Propsy**: Brak.

### `OnboardingForm`

- **Opis komponentu**: Formularz do wprowadzania celu kalorycznego. Używa biblioteki `react-hook-form` do zarządzania stanem, walidacji i wysyłki.
- **Główne elementy**: Komponenty `CalorieGoalInput` i `Button`.
- **Obsługiwane interakcje**: Wprowadzanie wartości w polu, wysłanie formularza.
- **Obsługiwana walidacja**:
  - Pole jest wymagane.
  - Wartość musi być liczbą całkowitą.
  - Wartość musi być większa od 0 (rekomendowana walidacja: `> 500` dla lepszego UX).
- **Typy**: `CreateOnboardingCommand` (dla danych formularza), `OnboardingFormProps`.
- **Propsy**:
  - `onSubmit: (data: CreateOnboardingCommand) => void`: Funkcja wywoływana po pomyślnej walidacji i wysłaniu formularza.
  - `isLoading: boolean`: Informuje, czy trwa proces wysyłania danych do API.
  - `apiError: string | null`: Przechowuje błędy zwrócone przez API.

## 5. Typy

Do implementacji widoku wymagane są następujące typy, z których większość jest już zdefiniowana w `apps/frontend/src/types.ts`.

- **`CreateOnboardingCommand`**: Typ danych wysyłanych do API.

  ```typescript
  // Obiekt wysyłany w ciele żądania POST /api/v1/profile/onboarding
  export type CreateOnboardingCommand = {
    daily_calorie_goal: number;
  };
  ```

- **`ProfileDTO`**: Typ danych otrzymywanych z API po pomyślnym utworzeniu profilu.

  ```typescript
  export type ProfileDTO = {
    user_id: string; // UUID
    daily_calorie_goal: number | null;
    onboarding_completed_at: string | null; // ISODateTimeString
    created_at: string; // ISODateTimeString
    updated_at: string; // ISODateTimeString
  };
  ```

- **`OnboardingViewModel`**: Nowy typ (ViewModel) do zarządzania stanem widoku.
  ```typescript
  export type OnboardingViewModel = {
    isLoading: boolean;
    error: string | null;
  };
  ```

## 6. Zarządzanie stanem

Zarządzanie stanem zostanie zrealizowane za pomocą kombinacji lokalnego stanu komponentu i niestandardowego hooka.

- **`react-hook-form`**: Będzie użyty w komponencie `OnboardingForm` do zarządzania stanem pól formularza, walidacji i statusu wysyłki.

- **`useOnboarding` (custom hook)**: Ten hook będzie zawierał całą logikę związaną z komunikacją z API.
  - **Cel**: Abstrahuje logikę wysyłania danych, obsługi stanu ładowania i błędów.
  - **Stan**:
    - `isLoading: boolean`: Zarządza stanem ładowania podczas wywołania API.
    - `error: string | null`: Przechowuje komunikaty o błędach z API.
  - **Funkcje**:
    - `completeOnboarding(data: CreateOnboardingCommand)`: Asynchroniczna funkcja, która wysyła dane do API, zarządza stanem `isLoading` i `error`, a po sukcesie przekierowuje użytkownika.

## 7. Integracja API

Integracja z backendem będzie polegać na wywołaniu jednego endpointu.

- **Endpoint**: `POST /api/v1/profile/onboarding`
- **Klient API**: Wywołanie zostanie zrealizowane za pomocą istniejącego klienta API (prawdopodobnie w `apps/frontend/src/lib/api.ts`).
- **Typ żądania**: `CreateOnboardingCommand`.
- **Typ odpowiedzi (sukces)**: `ProfileDTO`.
- **Obsługa sukcesu (status 201)**: Użytkownik jest przekierowywany do panelu głównego (`/`). Stan globalny (np. w kontekście użytkownika) powinien zostać zaktualizowany, aby odzwierciedlić ukończenie onboardingu.
- **Obsługa błędów**: Szczegółowo opisana w sekcji "Obsługa błędów".

## 8. Interakcje użytkownika

1.  **Wejście na stronę**: Użytkownik widzi formularz z prośbą o podanie dziennego celu kalorycznego.
2.  **Wprowadzanie danych**: Użytkownik wpisuje wartość liczbową w polu formularza.
3.  **Walidacja w czasie rzeczywistym**: Po utracie fokusu z pola (onBlur), jeśli dane są nieprawidłowe (np. puste, tekst, liczba ujemna), wyświetlany jest komunikat o błędzie.
4.  **Wysłanie formularza**: Użytkownik klika przycisk "Zapisz i kontynuuj".
    - **Wynik**: Przycisk jest blokowany, a na nim pojawia się wskaźnik ładowania. Rozpoczyna się wywołanie API.
    - **Po sukcesie**: Użytkownik jest przekierowywany na stronę główną.
    - **Po porażce**: Wskaźnik ładowania znika, przycisk jest odblokowywany, a pod formularzem wyświetlany jest komunikat o błędzie.

## 9. Warunki i walidacja

- **`daily_calorie_goal`**:
  - **Miejsce**: Komponent `OnboardingForm`, z użyciem `react-hook-form`.
  - **Warunki**:
    - `required`: Pole nie może być puste. Komunikat: "To pole jest wymagane."
    - `isNumber`: Wartość musi być liczbą. Komunikat: "Wartość musi być liczbą."
    - `min`: Wartość musi być dodatnia. Sugerowana reguła: `value > 500`. Komunikat: "Wartość musi być większa niż 500."
  - **Wpływ na interfejs**: Przycisk "Zapisz i kontynuuj" jest nieaktywny (`disabled`), dopóki wszystkie warunki walidacji nie zostaną spełnione.

## 10. Obsługa błędów

- **Błąd walidacji po stronie klienta**: Komunikaty o błędach są wyświetlane bezpośrednio pod odpowiednim polem formularza.
- **Błąd sieci lub serwera (np. 500)**: Hook `useOnboarding` przechwytuje błąd, ustawia stan `error` na ogólny komunikat (np. "Wystąpił błąd serwera. Spróbuj ponownie później.") i wyświetla go w widoku, np. pod przyciskiem wysyłania.
- **Użytkownik już ukończył onboarding (API zwraca 409 Conflict)**: Hook `useOnboarding` powinien wykryć ten konkretny status błędu i zamiast wyświetlać błąd, po cichu przekierować użytkownika do panelu głównego (`/`). Jest to scenariusz naprawczy, a nie błąd z perspektywy użytkownika.
- **Brak uwierzytelnienia (API zwraca 401 Unauthorized)**: Ten błąd powinien być obsługiwany globalnie przez klienta API, który powinien przekierować użytkownika na stronę logowania.

## 11. Kroki implementacji

1.  **Utworzenie plików**: Stworzyć nowe pliki dla komponentów: `apps/frontend/src/views/OnboardingView.tsx` oraz `apps/frontend/src/components/onboarding/OnboardingForm.tsx`.
2.  **Konfiguracja routingu**: W głównym pliku routingu aplikacji dodać nową, chronioną trasę `/onboarding`, która będzie renderować `OnboardingView`. Zaimplementować logikę w komponencie chroniącym trasy, aby przekierowywać użytkowników na podstawie statusu `onboarding_completed_at`.
3.  **Implementacja `OnboardingView`**: Zbudować szkielet widoku, wstawić nagłówki i zintegrować komponent `OnboardingForm`.
4.  **Implementacja `OnboardingForm`**: Zintegrować `react-hook-form`, zdefiniować pole `daily_calorie_goal` z odpowiednimi regułami walidacji, używając komponentów `Input` i `Button` z `shadcn/ui`.
5.  **Stworzenie hooka `useOnboarding`**: Zaimplementować logikę komunikacji z endpointem `POST /api/v1/profile/onboarding`, włączając zarządzanie stanem ładowania, obsługę błędów i przekierowania po sukcesie.
6.  **Integracja hooka z widokiem**: Połączyć `useOnboarding` z `OnboardingView` i przekazać odpowiednie `propsy` (np. `isLoading`, `apiError`, `onSubmit`) do `OnboardingForm`.
7.  **Stylizowanie**: Dodać klasy Tailwind CSS do wszystkich komponentów, aby zapewnić spójny i estetyczny wygląd, zgodny z resztą aplikacji.
8.  **Testowanie**: Manualnie przetestować wszystkie ścieżki użytkownika: pomyślne ukończenie, błędy walidacji, błędy serwera oraz scenariusz z kodem 409.
