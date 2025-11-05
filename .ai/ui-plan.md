# Architektura UI dla YetAnotherHealthyApp

## 1. Przegląd struktury UI

Architektura interfejsu użytkownika (UI) dla YetAnotherHealthyApp została zaprojektowana w oparciu o podejście **mobile-first**, koncentrując się na prostocie i intuicyjności. Celem jest umożliwienie użytkownikom szybkiego dodawania posiłków i monitorowania postępów w diecie przy minimalnym wysiłku.

Główne filary architektury to:

- **Nawigacja oparta na zakładkach:** Prosta i stała nawigacja z trzema głównymi widokami (Dzisiaj, Historia, Profil) zapewnia łatwy dostęp do kluczowych funkcji.
- **Centralny przepływ użytkownika:** Kluczowa akcja dodawania posiłku jest inicjowana przez globalnie dostępny przycisk Floating Action Button (FAB), co prowadzi użytkownika przez dedykowany, wieloetapowy proces (stepper).
- **Zarządzanie stanem serwera:** Wykorzystanie biblioteki React Query do obsługi danych z API, co zapewnia buforowanie (caching), automatyczną synchronizację i obsługę stanów ładowania oraz błędów w sposób deklaratywny.
- **Podejście "Optimistic UI":** Kluczowe operacje, takie jak dodawanie i usuwanie posiłków, będą natychmiast odzwierciedlane w interfejsie, poprawiając odczuwalną responsywność aplikacji.
- **Komponenty reużywalne:** Stworzenie spójnego systemu komponentów (np. do wyświetlania makroskładników) zapewni jednolity wygląd i działanie w całej aplikacji.

## 2. Lista widoków

### Widok: Uwierzytelnianie (Logowanie / Rejestracja)

- **Ścieżka:** `/login`, `/register`
- **Główny cel:** Umożliwienie użytkownikom bezpiecznego dostępu do aplikacji oraz tworzenia nowych kont.
- **Kluczowe informacje:** Pola na e-mail i hasło, komunikaty o błędach walidacji (np. "Hasło musi mieć 8 znaków"), linki do przełączania się między formularzami.
- **Kluczowe komponenty:** `InputField`, `Button`, `ErrorMessage`.
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Jasne komunikaty o błędach bez ujawniania, czy problem dotyczy loginu czy hasła. Automatyczne przekierowanie po pomyślnej akcji.
  - **Dostępność:** Poprawne etykiety dla pól formularza, obsługa walidacji za pomocą atrybutów `aria-invalid`.
  - **Bezpieczeństwo:** Komunikacja z API odbywa się przez HTTPS. Aplikacja nie przechowuje hasła.

### Widok: Onboarding

- **Ścieżka:** `/onboarding` (chroniona, dostępna tylko po pierwszej rejestracji)
- **Główny cel:** Zebranie od użytkownika informacji o dziennym celu kalorycznym, co jest warunkiem koniecznym do korzystania z aplikacji.
- **Kluczowe informacje:** Pole do wprowadzenia celu kalorycznego, krótki opis wyjaśniający znaczenie tego celu.
- **Kluczowe komponenty:** `NumberInput`, `Button`, `InfoTooltip`.
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Prosty, jednoetapowy proces, który jest obowiązkowy, ale szybki do ukończenia.
  - **Dostępność:** Pole formularza jest w pełni dostępne z klawiatury i dla czytników ekranu.
  - **Bezpieczeństwo:** Widok jest chroniony i dostępny tylko dla uwierzytelnionych użytkowników, którzy nie ukończyli jeszcze tego kroku.

### Widok: Panel Główny (Dzisiaj)

- **Ścieżka:** `/`
- **Główny cel:** Prezentacja podsumowania bieżącego dnia, motywowanie użytkownika do osiągania celów i szybki przegląd spożytych posiłków.
- **Kluczowe informacje:**
  - Progres realizacji dziennego celu kalorycznego (np. wykres kołowy).
  - Podsumowanie spożytych makroskładników (białko, tłuszcze, węglowodany).
  - Wykres trendu spożycia kalorii z ostatnich 7 dni.
  - Lista posiłków dodanych w bieżącym dniu.
  - Stan pusty (Empty State) z zachętą do działania, jeśli nie dodano jeszcze żadnego posiłku.
- **Kluczowe komponenty:** `DailyProgressChart`, `MacroDisplay`, `WeeklyTrendChart`, `MealList`, `EmptyState`.
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Wszystkie kluczowe informacje dostępne "na pierwszy rzut oka". Kliknięcie posiłku przenosi do jego szczegółów.
  - **Dostępność:** Wykresy i wizualizacje posiadają tekstowe alternatywy i etykiety ARIA.
  - **Bezpieczeństwo:** Dane pobierane z API są specyficzne dla zalogowanego użytkownika dzięki RLS w Supabase.

### Widok: Historia

- **Ścieżka:** `/history`
- **Główny cel:** Umożliwienie przeglądania historii wszystkich zapisanych posiłków.
- **Kluczowe informacje:** Chronologiczna lista posiłków, pogrupowana według dat. Każdy element listy zawiera nazwę kategorii, czas spożycia i podsumowanie kaloryczne.
- **Kluczowe komponenty:** `MealList` (z grupowaniem), `InfiniteScrollLoader`.
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Zastosowanie "infinite scroll" do płynnego ładowania starszych danych bez konieczności przełączania stron.
  - **Dostępność:** Lista jest semantycznie poprawną strukturą (`<ul>`), a ładowanie nowych danych jest komunikowane czytnikom ekranu.
  - **Bezpieczeństwo:** Dostęp wyłącznie do danych zalogowanego użytkownika.

### Widok: Profil

- **Ścieżka:** `/profile`
- **Główny cel:** Zarządzanie ustawieniami konta użytkownika.
- **Kluczowe informacje:** Adres e-mail użytkownika (tylko do odczytu), pole do edycji dziennego celu kalorycznego, przycisk wylogowania.
- **Kluczowe komponenty:** `EditableField`, `Button`.
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Prosty i przejrzysty interfejs do zmiany kluczowego ustawienia. Wylogowanie jest operacją jednoznacznie opisaną.
  - **Dostępność:** Wszystkie interaktywne elementy są w pełni dostępne.
  - **Bezpieczeństwo:** Operacja wylogowania unieważnia lokalny token JWT.

### Przepływ: Dodawanie/Edycja Posiłku (Stepper)

- **Ścieżka:** `/add-meal` (lub jako modal)
- **Główny cel:** Prowadzenie użytkownika krok po kroku przez proces dodawania posiłku – od opisu, przez analizę AI, aż po akceptację wyników.
- **Kluczowe informacje i komponenty (według kroków):**
  1.  **Krok 1: Wprowadzanie danych**
      - **Cel:** Zebranie opisu posiłku.
      - **Komponenty:** `CategorySelect` (lista pobierana z API), `Textarea` na opis, `ToggleSwitch` do przełączenia na tryb ręczny (wprowadzanie samych kalorii).
  2.  **Krok 2: Analiza AI (Stan ładowania)**
      - **Cel:** Informowanie o trwającym przetwarzaniu.
      - **Komponenty:** `Spinner`, `ProgressBar`, tekst informujący o postępie.
  3.  **Krok 3: Wyniki i akceptacja**
      - **Cel:** Prezentacja wyników analizy do weryfikacji.
      - **Komponenty:** `MacroDisplay` (dla sumy), `IngredientsTable` (lista składników z wagami i makrami), `Button` ("Akceptuj"), `Button` ("Popraw i przelicz ponownie"), `Button` ("Anuluj").
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Podział na kroki upraszcza złożony proces. Jasne komunikaty o stanie analizy (w toku, błąd, sukces). Możliwość poprawienia danych wejściowych i ponowienia analizy daje użytkownikowi kontrolę.
  - **Dostępność:** Każdy krok jest logiczną całością. Stany ładowania są komunikowane przez `aria-live regions`.
  - **Bezpieczeństwo:** Wszystkie operacje są autoryzowane i powiązane z kontem użytkownika.

### Widok: Szczegóły Posiłku

- **Ścieżka:** `/meals/{meal_id}`
- **Główny cel:** Wyświetlenie pełnych informacji o zapisanym posiłku.
- **Kluczowe informacje:** Podsumowanie makroskładników i kalorii, kategoria, data spożycia, szczegółowa lista składników wygenerowana przez AI.
- **Kluczowe komponenty:** `MacroDisplay`, `IngredientsTable`, `Button` ("Edytuj"), `Button` ("Usuń"), `ConfirmationModal` (do potwierdzenia usunięcia).
- **UX, dostępność i bezpieczeństwo:**
  - **UX:** Edycja przenosi użytkownika z powrotem do przepływu dodawania posiłku, z wstępnie wypełnionymi danymi. Usunięcie jest zabezpieczone dodatkowym potwierdzeniem.
  - **Dostępność:** Wszystkie dane są prezentowane w czytelny, semantyczny sposób.
  - **Bezpieczeństwo:** Użytkownik ma dostęp tylko do posiłków, które sam utworzył.

## 3. Mapa podróży użytkownika

**Główny przepływ: Dodawanie posiłku przez nowego użytkownika**

1.  **Rejestracja:** Użytkownik tworzy konto w widoku `/register`.
2.  **Onboarding:** Po udanej rejestracji jest automatycznie przekierowywany do `/onboarding`, gdzie ustawia swój dzienny cel kaloryczny.
3.  **Panel Główny:** Po zakończeniu onboardingu ląduje w Panelu Głównym (`/`), który wyświetla "stan pusty".
4.  **Inicjacja dodawania:** Użytkownik klika globalny przycisk FAB, aby dodać nowy posiłek.
5.  **Krok 1 (Wprowadzanie):** Przechodzi do widoku dodawania posiłku. Wybiera kategorię (np. "Śniadanie") i wpisuje w polu tekstowym: "Owsianka z bananem i miodem". Klika "Analizuj".
6.  **Krok 2 (Analiza):** Interfejs przechodzi w stan ładowania, informując, że AI przetwarza dane. Aplikacja cyklicznie sprawdza status analizy w API.
7.  **Krok 3 (Wyniki):** Po pomyślnym zakończeniu analizy, widok wyświetla podsumowanie kalorii i makroskładników oraz listę rozpoznanych składników.
8.  **Akceptacja:** Użytkownik weryfikuje wyniki i klika "Akceptuj".
9.  **Zakończenie:** Aplikacja zapisuje posiłek przez API i przekierowuje użytkownika z powrotem do Panelu Głównego. Dzięki unieważnieniu zapytania w React Query, panel odświeża się i wyświetla nowo dodany posiłek oraz zaktualizowany wykres postępu.

## 4. Układ i struktura nawigacji

- **Główna nawigacja:** Umieszczona na dole ekranu (Bottom Tab Bar) zawiera trzy stałe linki:
  - **Dzisiaj** (`/`): Domyślny widok po zalogowaniu.
  - **Historia** (`/history`): Przegląd przeszłych wpisów.
  - **Profil** (`/profile`): Ustawienia konta.
- **Akcja globalna:** Przycisk **Floating Action Button (FAB)** jest widoczny nad główną nawigacją we wszystkich trzech głównych widokach i służy do inicjowania przepływu dodawania posiłku.
- **Nawigacja kontekstowa:**
  - Z listy posiłków (w widoku Dzisiaj lub Historia) użytkownik może przejść do widoku **Szczegółów Posiłku**.
  - Z widoku Szczegółów Posiłku może przejść do **trybu edycji**, który wykorzystuje ten sam wieloetapowy interfejs co dodawanie nowego posiłku.

## 5. Kluczowe komponenty

- **`MealList`:** Reużywalna lista do wyświetlania posiłków w Panelu Głównym i Historii. Potrafi grupować wpisy po dacie.
- **`MacroDisplay`:** Spójny wizualnie komponent do prezentacji wartości kalorycznej oraz makroskładników (białko, tłuszcze, węglowodany). Używany w Panelu Głównym, Szczegółach Posiłku i w wynikach analizy AI.
- **`DailyProgressChart`:** Komponent wizualizujący (np. jako wykres kołowy lub pasek postępu) postęp w realizacji dziennego celu kalorycznego.
- **`EmptyState`:** Komponent wyświetlany, gdy brakuje danych (np. brak posiłków w historii). Zawiera grafikę, komunikat i wezwanie do akcji (Call to Action).
- **`ConfirmationModal`:** Modal używany do uzyskania od użytkownika potwierdzenia wykonania destrukcyjnej akcji, np. usunięcia posiłku.
