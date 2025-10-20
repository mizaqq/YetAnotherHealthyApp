# Plan implementacji widoku Uwierzytelnianie

## 1. Przegląd

Widok uwierzytelniania jest kluczowym elementem aplikacji, umożliwiającym użytkownikom logowanie do istniejących kont oraz rejestrację nowych. Celem jest zapewnienie bezpiecznego, intuicyjnego i zgodnego z wymaganiami PRD procesu dostępu do aplikacji. Widok będzie obsługiwał dwie ścieżki (`/login` i `/register`), wykorzystując wspólny, rekonfigurowalny formularz w celu minimalizacji duplikacji kodu. Integracja z Supabase posłuży do obsługi procesów autentykacji, a po pomyślnej akcji użytkownik zostanie przekierowany do odpowiedniej części aplikacji (onboarding lub dashboard) na podstawie statusu swojego profilu.

## 2. Routing widoku

Widok będzie dostępny pod następującymi ścieżkami:

- `/login`: Wyświetla formularz logowania.
- `/register`: Wyświetla formularz rejestracji.

## 3. Struktura komponentów

Hierarchia komponentów zostanie zorganizowana w celu reużywalności i przejrzystości. Główne komponenty `LoginPage` i `RegisterPage` będą renderować komponent `AuthForm`, dostarczając mu odpowiednie konfiguracje.

```
<App>
  <Router>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    {/* ... inne trasy ... */}
  </Router>
</App>

// LoginPage.tsx / RegisterPage.tsx
<AuthPageLayout>
  <AuthForm
    mode={'login' | 'register'}
    onSubmit={...}
    isLoading={...}
    apiError={...}
  />
</AuthPageLayout>
```

## 4. Szczegóły komponentów

### `AuthPageLayout`

- **Opis komponentu:** Kontener wizualny dla stron logowania i rejestracji, zapewniający spójny wygląd, np. centrując formularz na stronie.
- **Główne elementy:** `div` lub `main` jako główny kontener.
- **Obsługiwane interakcje:** Brak.
- **Obsługiwana walidacja:** Brak.
- **Typy:** Brak.
- **Propsy:** `children: React.ReactNode`.

### `AuthForm`

- **Opis komponentu:** Reużywalny formularz do obsługi logowania i rejestracji. Składa się z pól na e-mail i hasło, przycisku do wysłania formularza, komunikatu o błędach API oraz linku do przełączania się między trybami.
- **Główne elementy:** Komponenty `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter`, `Input`, `Button`, `Label` z biblioteki `shadcn/ui`. Formularz będzie zarządzany przez `react-hook-form` w celu obsługi stanu i walidacji.
- **Obsługiwane interakcje:**
  - Wprowadzanie danych w polach `email` i `password`.
  - Kliknięcie przycisku "Zaloguj się" / "Zarejestruj się", co uruchamia walidację i wysłanie formularza.
- **Obsługiwana walidacja:**
  - **Email:** Pole wymagane, musi być w poprawnym formacie adresu e-mail.
  - **Hasło (Rejestracja):** Pole wymagane. Musi mieć co najmniej 8 znaków, zawierać co najmniej jedną literę i jedną cyfrę.
  - **Hasło (Logowanie):** Pole wymagane.
- **Typy:** `AuthFormProps`, `AuthFormData`.
- **Propsy:**
  - `mode: 'login' | 'register'`: Określa tryb formularza.
  - `onSubmit: (data: AuthFormData) => void`: Funkcja wywoływana po pomyślnej walidacji formularza.
  - `isLoading: boolean`: Informuje, czy operacja jest w toku (do blokowania przycisku i wyświetlania wskaźnika ładowania).
  - `apiError: string | null`: Komunikat o błędzie z API do wyświetlenia.

## 5. Typy

### `AuthMode`

Typ literalny określający tryb pracy formularza.

```typescript
export type AuthMode = "login" | "register";
```

### `AuthFormData`

Interfejs reprezentujący dane z formularza uwierzytelniania, używany do walidacji i przesyłania danych.

```typescript
export interface AuthFormData {
  email: string;
  password: string;
}
```

### `AuthFormProps`

Interfejs definiujący propsy dla komponentu `AuthForm`, zapewniający jego rekonfigurację.

```typescript
export interface AuthFormProps {
  mode: AuthMode;
  onSubmit: (data: AuthFormData) => void;
  isLoading: boolean;
  apiError: string | null;
}
```

## 6. Zarządzanie stanem

Zarządzanie stanem zostanie podzielone na dwie warstwy:

1.  **Stan lokalny formularza:** Będzie zarządzany przez bibliotekę `react-hook-form` z `zod` do walidacji schematu. To zapewni natychmiastową informację zwrotną dla użytkownika i czystą obsługę reguł walidacyjnych.

2.  **Stan globalny i logika biznesowa:** Zostanie stworzony customowy hook `useAuth`, który będzie enkapsulował logikę komunikacji z Supabase.
    - **Cel:** Abstrakcja operacji `login` i `register`, zarządzanie stanem ładowania (`isLoading`) oraz błędami pochodzącymi z API (`apiError`).
    - **Stany wewnętrzne:** `isLoading: boolean`, `apiError: string | null`.
    - **Eksponowane funkcje:** `login(data: AuthFormData)`, `register(data: AuthFormData)`.
    - **Użycie:** Komponenty `LoginPage` i `RegisterPage` będą używać tego hooka do implementacji logiki i przekazywania stanu w dół do `AuthForm`.

## 7. Integracja API

Integracja nie będzie opierać się na tradycyjnym REST API dla logowania/rejestracji, lecz na kliencie Supabase JS.

- **Rejestracja:**

  - **Wywołanie:** `supabase.auth.signUp({ email, password })`
  - **Typ żądania:** `{ email: string, password: string }`
  - **Typ odpowiedzi (sukces):** `{ data: { user, session }, error: null }`
  - **Typ odpowiedzi (błąd):** `{ data: { user: null, session: null }, error: AuthError }`

- **Logowanie:**
  - **Wywołanie:** `supabase.auth.signInWithPassword({ email, password })`
  - **Typ żądania:** `{ email: string, password: string }`
  - **Typ odpowiedzi (sukces):** `{ data: { user, session }, error: null }`
  - **Typ odpowiedzi (błąd):** `{ data: { user: null, session: null }, error: AuthError }`

Po udanym logowaniu lub rejestracji, aplikacja (prawdopodobnie w globalnym kontekście autentykacji) wywoła endpoint `GET /api/v1/profile` w celu pobrania danych profilowych i podjęcia decyzji o przekierowaniu.

- **Pobieranie profilu:**
  - **Endpoint:** `GET /api/v1/profile`
  - **Typ odpowiedzi:** `ProfileDTO`

## 8. Interakcje użytkownika

- **Wprowadzanie danych:** Użytkownik wpisuje e-mail i hasło. Walidacja on-the-fly (np. przy utracie fokusu) informuje o błędach formatowania.
- **Wysłanie formularza:** Użytkownik klika przycisk "Zaloguj się" lub "Zarejestruj się".
  - **Wynik:** Przycisk jest blokowany, pojawia się wskaźnik ładowania. Po zakończeniu operacji, w przypadku sukcesu następuje przekierowanie, a w przypadku błędu wyświetlany jest komunikat.
- **Przełączanie trybu:** Użytkownik klika link "Zarejestruj się" (na stronie logowania) lub "Zaloguj się" (na stronie rejestracji).
  - **Wynik:** Aplikacja nawiguje do odpowiedniej ścieżki (`/login` lub `/register`), resetując stan formularza.

## 9. Warunki i walidacja

Walidacja będzie realizowana po stronie klienta za pomocą `zod` i `react-hook-form` przed wysłaniem żądania do API.

- **Komponent:** `AuthForm`
- **Warunki:**
  - `email`: Musi być poprawnym adresem e-mail (np. `example@domain.com`).
  - `password` (rejestracja): Musi spełniać politykę haseł: min. 8 znaków, co najmniej jedna litera i jedna cyfra.
- **Wpływ na interfejs:**
  - Niespełnienie warunków walidacji uniemożliwia wysłanie formularza.
  - Komunikaty o błędach są wyświetlane pod odpowiednimi polami formularza, a atrybut `aria-invalid` jest ustawiany na `true` dla pól z błędami.

## 10. Obsługa błędów

- **Błędy walidacji klienta:** Obsługiwane przez `react-hook-form`, wyświetlane bezpośrednio przy polach.
- **Błędy API (Supabase):**
  - **Nieprawidłowe dane logowania:** Supabase zwróci błąd. Hook `useAuth` przechwyci go i wyświetli ogólny komunikat: "Nieprawidłowy e-mail lub hasło."
  - **Użytkownik już istnieje:** Supabase zwróci błąd. Hook `useAuth` wyświetli komunikat: "Użytkownik o tym adresie e-mail już istnieje."
- **Błędy sieciowe:** W przypadku problemów z połączeniem z Supabase lub backendem (podczas pobierania profilu), zostanie wyświetlony ogólny komunikat o błędzie sieciowym, np. "Wystąpił błąd. Spróbuj ponownie później."
- **Brak profilu po zalogowaniu:** Jeśli po udanej autentykacji w Supabase nie uda się pobrać profilu z backendu (błąd 404), użytkownik powinien zostać wylogowany z Supabase, a na ekranie powinien pojawić się komunikat o błędzie krytycznym.

## 11. Kroki implementacji

1.  **Stworzenie struktury plików:** Utworzenie plików dla komponentów `LoginPage.tsx`, `RegisterPage.tsx`, `AuthForm.tsx` oraz hooka `useAuth.ts` w odpowiednich katalogach (`src/pages`, `src/components/auth`, `src/hooks`).
2.  **Implementacja `AuthForm`:** Zbudowanie layoutu formularza przy użyciu komponentów `shadcn/ui`. Integracja z `react-hook-form` i zdefiniowanie schematów walidacji `zod` dla trybu logowania i rejestracji.
3.  **Implementacja hooka `useAuth`:** Stworzenie logiki do komunikacji z Supabase (`signUp`, `signInWithPassword`), zarządzanie stanami `isLoading` i `apiError`.
4.  **Implementacja `LoginPage` i `RegisterPage`:** Stworzenie komponentów stron, które będą używać hooka `useAuth` i renderować `AuthForm` z odpowiednimi propsami.
5.  **Dodanie routingu:** Zaktualizowanie głównego routera aplikacji o nowe ścieżki `/login` i `/register`.
6.  **Implementacja logiki przekierowania:** Zapewnienie, że po pomyślnym zalogowaniu/rejestracji aplikacja sprawdzi profil użytkownika i przekieruje go na `/onboarding` lub `/dashboard`. Logikę tę najlepiej umieścić w globalnym dostawcy kontekstu autentykacji.
7.  **Stylowanie i dostępność:** Dopracowanie stylów za pomocą Tailwind CSS i upewnienie się, że wszystkie elementy formularza są dostępne (etykiety, atrybuty ARIA).
8.  **Testowanie:** Przetestowanie wszystkich scenariuszy: pomyślne logowanie/rejestracja, błędy walidacji, błędy API, przekierowania.
