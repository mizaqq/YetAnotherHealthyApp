# Plan implementacji widoku – Profil

## 1. Przegląd

Widok "Profil" (`/profile`) umożliwia zalogowanemu użytkownikowi zarządzanie podstawowymi ustawieniami swojego konta. Głównym celem jest zapewnienie prostego interfejsu do przeglądania swojego adresu e-mail, aktualizacji dziennego celu kalorycznego oraz wylogowania się z aplikacji. Widok ten jest kluczowy dla personalizacji doświadczenia użytkownika zgodnie z jego planem żywieniowym.

## 2. Routing widoku

Widok będzie dostępny pod następującą ścieżką:

- **Ścieżka:** `/profile`
- **Dostęp:** Wymaga uwierzytelnienia użytkownika. Niezalogowani użytkownicy próbujący uzyskać dostęp do tej ścieżki powinni zostać przekierowani na stronę logowania.

## 3. Struktura komponentów

Hierarchia komponentów dla widoku profilu będzie następująca:

```
- ProfileView (komponent strony, trasa: /profile)
  - UserProfileCard (komponent-kontener dla danych profilu)
    - StaticField (dla wyświetlania adresu e-mail)
    - EditableField (dla edycji dziennego celu kalorycznego)
    - Button (komponent shadcn/ui do wylogowania)
```

## 4. Szczegóły komponentów

### `ProfileView` (Komponent strony)

- **Opis:** Główny komponent renderowany dla ścieżki `/profile`. Odpowiada za integrację z hookiem `useProfile`, zarządzanie stanem ładowania i błędów na poziomie widoku oraz przekazywanie danych i akcji do komponentów podrzędnych.
- **Główne elementy:** Wykorzystuje `UserProfileCard` do prezentacji danych. Renderuje stany pośrednie, takie jak wskaźnik ładowania (spinner) lub komunikat o błędzie.
- **Obsługiwane zdarzenia:** Brak bezpośrednich interakcji. Logika jest delegowana do hooka `useProfile`.
- **Warunki walidacji:** Brak.
- **Typy:** `ProfileViewModel`.
- **Propsy:** Brak (jest to komponent-strona).

### `UserProfileCard`

- **Opis:** Wizualny kontener (karta) grupujący wszystkie informacje i akcje związane z profilem użytkownika.
- **Główne elementy:**
  - `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter` z `shadcn/ui`.
  - Komponent `StaticField` do wyświetlania statycznego adresu e-mail.
  - Komponent `EditableField` do zarządzania celem kalorycznym.
  - Komponent `Button` z `shadcn/ui` do akcji wylogowania.
- **Obsługiwane zdarzenia:** Przekazuje zdarzenia `onSaveGoal` i `onLogout` do komponentu `ProfileView`.
- **Warunki walidacji:** Brak.
- **Typy:** `ProfileViewModel`.
- **Propsy:**
  ```typescript
  interface UserProfileCardProps {
    profile: ProfileViewModel;
    onSaveGoal: (newGoal: number) => Promise<void>;
    onLogout: () => void;
  }
  ```

### `EditableField` (Komponent reużywalny)

- **Opis:** Komponent do wyświetlania wartości, która może być edytowana w miejscu. Zarządza swoim wewnętrznym stanem (tryb widoku / tryb edycji).
- **Główne elementy:**
  - **Tryb widoku:** `p` do wyświetlania wartości, `Button` (wariant "ghost" lub "link") z ikoną ołówka do włączenia edycji.
  - **Tryb edycji:** `Input type="number"`, `Button` "Zapisz" i `Button` "Anuluj".
- **Obsługiwane zdarzenia:**
  - `onSave(newValue: number)`: Wywoływane po kliknięciu "Zapisz" z nową, zwalidowaną wartością.
  - `onCancel()`: Wywoływane po kliknięciu "Anuluj".
- **Warunki walidacji:**
  - Wartość jest wymagana (nie może być pusta).
  - Wartość musi być liczbą całkowitą.
  - Wartość musi być większa od zera (`> 0`).
  - Przycisk "Zapisz" jest nieaktywny, jeśli walidacja się nie powiodła. Pod polem `Input` wyświetlany jest komunikat o błędzie.
- **Typy:** `number`.
- **Propsy:**
  ```typescript
  interface EditableFieldProps {
    label: string;
    initialValue: number;
    isUpdating: boolean;
    onSave: (newValue: number) => void;
  }
  ```

## 5. Typy

Do implementacji widoku wymagane będą następujące typy:

```typescript
// DTO (Data Transfer Object) - dane z API
import { ProfileDTO } from "./types"; // Zakładając, że ProfileDTO jest już zdefiniowane

// Typ dla ciała żądania PATCH
export type UpdateProfilePayload = {
  daily_calorie_goal: number;
};

// ViewModel - model stanu dla widoku
export type ProfileViewModel = {
  email: string;
  dailyCalorieGoal: number;
  isLoading: boolean; // Stan ładowania początkowych danych
  isUpdating: boolean; // Stan aktualizacji danych (np. celu kalorycznego)
  error: string | null; // Komunikat błędu
};
```

## 6. Zarządzanie stanem

Zarządzanie stanem będzie scentralizowane w dedykowanym customowym hooku `useProfile`.

- **Hook:** `useProfile`
- **Cel:** Abstrakcja logiki biznesowej związanej z profilem użytkownika, w tym pobieranie danych, aktualizacja i obsługa wylogowania.
- **Zarządzany stan:** Wewnętrznie będzie korzystał z `useState` do przechowywania obiektu `ProfileViewModel`.
- **Eksportowane funkcje i wartości:**
  - `profile: ProfileViewModel`: Aktualny stan widoku.
  - `updateCalorieGoal(newGoal: number): Promise<void>`: Funkcja do aktualizacji celu kalorycznego.
  - `logout(): void`: Funkcja do wylogowania użytkownika.
- **Logika:** Wewnątrz hooka zostanie użyty `useEffect` do pobrania danych profilu przy pierwszym załadowaniu. Funkcje `updateCalorieGoal` i `logout` będą asynchroniczne i będą zarządzać stanami `isUpdating` oraz `error`.

## 7. Integracja API

Integracja z backendem będzie realizowana poprzez wywołania do zdefiniowanych endpointów API.

- **Pobieranie danych profilu:**

  - **Endpoint:** `GET /api/v1/profile`
  - **Akcja:** Wywoływane przy montowaniu komponentu `ProfileView` przez hook `useProfile`.
  - **Typ odpowiedzi:** `ProfileDTO`.

- **Aktualizacja celu kalorycznego:**
  - **Endpoint:** `PATCH /api/v1/profile`
  - **Akcja:** Wywoływane po zapisaniu zmian w komponencie `EditableField`.
  - **Typ żądania:** `UpdateProfilePayload` (np. `{ "daily_calorie_goal": 2200 }`).
  - **Typ odpowiedzi:** `ProfileDTO` (zaktualizowane dane profilu).

## 8. Interakcje użytkownika

- **Wejście na stronę:** Użytkownik wchodzi na `/profile`. Aplikacja wyświetla spinner, wysyła żądanie `GET`, a po otrzymaniu danych wyświetla `UserProfileCard` z adresem e-mail i celem kalorycznym.
- **Edycja celu:** Użytkownik klika ikonę edycji przy celu kalorycznym. Komponent `EditableField` przechodzi w tryb edycji.
- **Zapis zmiany:** Użytkownik wprowadza nową wartość i klika "Zapisz". Aplikacja wysyła żądanie `PATCH`. Przycisk "Zapisz" jest nieaktywny i pokazuje spinner. Po sukcesie `EditableField` wraca do trybu widoku z nową wartością, a na ekranie pojawia się komunikat o sukcesie (toast).
- **Anulowanie edycji:** Użytkownik klika "Anuluj". `EditableField` wraca do trybu widoku, przywracając pierwotną wartość.
- **Wylogowanie:** Użytkownik klika "Wyloguj się". Sesja jest usuwana, a użytkownik jest przekierowywany na stronę logowania.

## 9. Warunki i walidacja

- **Cel kaloryczny (`EditableField`):**
  - **Warunek:** Wartość musi być liczbą całkowitą większą od 0.
  - **Weryfikacja:** Walidacja odbywa się po stronie klienta w czasie rzeczywistym (`onChange`).
  - **Stan interfejsu:** Jeśli wartość jest nieprawidłowa, przycisk "Zapisz" jest wyłączony, a pod polem `Input` pojawia się komunikat błędu, np. "Cel musi być liczbą większą od 0".

## 10. Obsługa błędów

- **Błąd pobierania danych (GET):** Jeśli żądanie `GET /api/v1/profile` zakończy się błędem, widok wyświetli komunikat błędu na całą stronę z informacją, np. "Nie udało się załadować profilu. Spróbuj ponownie później."
- **Błąd aktualizacji (PATCH):** Jeśli żądanie `PATCH /api/v1/profile` zwróci błąd, `EditableField` pozostanie w trybie edycji, a użytkownik zobaczy komunikat typu toast, np. "Błąd zapisu. Sprawdź wartość i spróbuj ponownie."
- **Błąd autoryzacji (401 Unauthorized):** W przypadku otrzymania statusu 401 z dowolnego endpointu, użytkownik powinien zostać automatycznie wylogowany i przekierowany na stronę logowania.

## 11. Kroki implementacji

1.  **Utworzenie struktury plików:** Stwórz nowy folder `src/views/Profile` i umieść w nim pliki: `ProfileView.tsx`, `UserProfileCard.tsx`, `EditableField.tsx` oraz `useProfile.ts`.
2.  **Implementacja hooka `useProfile`:** Zaimplementuj logikę pobierania i aktualizacji danych, w tym obsługę stanów `isLoading`, `isUpdating` i `error`. Zintegruj go z klientem API.
3.  **Implementacja `EditableField`:** Stwórz reużywalny komponent `EditableField` z logiką walidacji i przełączania między trybami widoku i edycji.
4.  **Implementacja `UserProfileCard`:** Zbuduj komponent karty, używając komponentów z `shadcn/ui`, i zintegruj w nim `EditableField` oraz przycisk wylogowania.
5.  **Implementacja `ProfileView`:** Złóż cały widok, używając hooka `useProfile` do pobrania danych i przekazania ich wraz z akcjami do `UserProfileCard`. Dodaj obsługę stanu ładowania i błędu.
6.  **Dodanie routingu:** W głównym pliku z routingiem aplikacji (`App.tsx` lub podobnym) dodaj nową, chronioną trasę dla ścieżki `/profile`, która będzie renderować `ProfileView`.
7.  **Stylowanie i testowanie:** Dopracuj wygląd widoku za pomocą Tailwind CSS, upewniając się, że jest responsywny. Przetestuj wszystkie interakcje użytkownika i scenariusze błędów.
