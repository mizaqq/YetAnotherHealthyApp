<conversation_summary>
<decisions>

1.  Przepływ dodawania posiłku zostanie zrealizowany jako wieloetapowy widok (stepper), obejmujący formularz, stan ładowania i ekran wyników z opcjami edycji i akceptacji.
2.  Użytkownik w widoku analizy będzie mógł dopracować prompt tekstowy dla AI i uruchomić ponowne przeliczenie, ale nie będzie mógł bezpośrednio modyfikować zmapowanych produktów.
3.  Przełączenie na tryb ręczny będzie dostępne na pierwszym kroku dodawania posiłku i uprości formularz do wyboru kategorii i wprowadzenia wyłącznie kalorii.
4.  Dashboard, oprócz postępu kalorycznego, będzie wizualizował cele makroskładników, które zostaną wyliczone na froncie na podstawie celu kalorycznego w proporcjach: 30% białko, 20% tłuszcz, 50% węglowodany jako stałe wartości wyliczane dla kadego uytkownika - białko ma 4 kalorie, tłuszcz 9, węglowodany 1 kalorie.
5.  Zostaną zaimplementowane dedykowane widoki "pustego stanu" (empty state) dla ekranu głównego i historii, z odpowiednimi komunikatami i wezwaniem do akcji.
6.  Szczegóły posiłku, w tym lista składników, będą ładowane z wykorzystaniem techniki "lazy loading" w celu optymalizacji wydajności.
7.  Edycja zapisanego posiłku będzie przenosić użytkownika do tego samego, dedykowanego widoku dodawania, wypełnionego istniejącymi danymi.
8.  Funkcja usuwania posiłku będzie zabezpieczona modalem potwierdzającym i wspierana przez komunikat "toast" po pomyślnym wykonaniu operacji.
9.  Ekran profilu w wersji MVP będzie zawierał funkcje edycji celu kalorycznego, wyświetlanie adresu e-mail użytkownika oraz przycisk wylogowania.
10. Zostanie zaimplementowane podejście "optimistic UI" dla operacji dodawania i usuwania posiłków w celu poprawy odczuwalnej wydajności aplikacji.
    </decisions>
    <matched_recommendations>
11. **Obsługa analizy AI:** Zaimplementowanie widoku typu "stepper" do zarządzania asynchronicznym procesem analizy, w tym stany ładowania i prezentacji wyników.
12. **Nawigacja i struktura:** Stworzenie stałej nawigacji z trzema głównymi widokami (Dzisiaj, Historia, Profil) oraz użycie globalnego przycisku FAB do inicjowania kluczowego przepływu dodawania posiłku.
13. **Zarządzanie stanem:** Wykorzystanie biblioteki React Query do zarządzania stanem serwera, cachowania danych, automatycznej synchronizacji i obsługi stanów ładowania/błędów.
14. **Bezpieczeństwo i sesja:** Stworzenie centralnego interceptora dla klienta API do obsługi błędów `401`, zarządzania tokenem JWT i przekierowywania do ekranu logowania.
15. **Onboarding:** Zaimplementowanie chronionej ścieżki (`/onboarding`) dla nowych użytkowników w celu obowiązkowego ustawienia celu kalorycznego przed uzyskaniem dostępu do aplikacji.
16. **Paginacja:** Wprowadzenie mechanizmu "infinite scroll" w widoku historii posiłków, bazującego na paginacji kursorowej dostępnej w API.
17. **Dostępność (a11y):** Konsekwentne używanie komponentów z biblioteki `shadcn/ui` i stosowanie standardów WAI-ARIA, w tym `aria-live regions` do komunikowania dynamicznych zmian stanu.
18. **Spójność UI:** Stworzenie reużywalnych komponentów (np. `MacroDisplay`) do ujednoliconej prezentacji danych o makroskładnikach w całej aplikacji.
19. **Wydajność:** Zastosowanie "optimistic UI" dla kluczowych operacji (dodawanie/usuwanie) w celu poprawy responsywności interfejsu.
20. **Obsługa błędów:** Zastosowanie zróżnicowanych wzorców prezentacji błędów: błąd serwera przy nieudanej analizie AI z opcją ponowienia, błędy walidacji przy logowaniu.
    </matched_recommendations>
    <ui_architecture_planning_summary>
    Na podstawie przeprowadzonej analizy i dyskusji, architektura UI dla MVP zostanie oparta o następujące filary:

**a. Główne wymagania dotyczące architektury UI**
Interfejs ma być prosty, intuicyjny i skoncentrowany na kluczowej funkcjonalności szybkiego dodawania posiłków za pomocą analizy AI oraz monitorowania postępów. Architektura musi wspierać asynchroniczne operacje, zapewniać spójność wizualną i być zoptymalizowana pod kątem wydajności.

**b. Kluczowe widoki, ekrany i przepływy użytkownika**

- **Onboarding:** Chroniona ścieżka dla nowych użytkowników w celu ustawienia celu kalorycznego (`POST /api/v1/profile/onboarding`).
- **Nawigacja Główna:** Oparta o 3 widoki:
  1.  **Dzisiaj (Dashboard):** Główny ekran z podsumowaniem dnia (`GET /reports/daily-summary`), wizualizacją postępu kalorii i makroskładników. Posiada "empty state" i jest punktem docelowym po dodaniu posiłku.
  2.  **Historia:** Lista historycznych posiłków (`GET /meals`) z zaimplementowanym "infinite scroll".
  3.  **Profil:** Ekran do zarządzania celem kalorycznym (`PATCH /api/v1/profile`) i wylogowania.
- **Przepływ Dodawania Posiłku:** Inicjowany przez globalny przycisk FAB, realizowany jako dedykowany ekran z krokami (stepper):
  1.  **Krok 1 (Input):** Wprowadzenie opisu posiłku i wybór kategorii, z opcją przełączenia na tryb ręczny (wpisanie tylko kalorii).
  2.  **Krok 2 (Analiza):** Stan ładowania z cyklicznym odpytywaniem statusu analizy (`GET /api/v1/analysis-runs/{run_id}`).
  3.  **Krok 3 (Wyniki):** Prezentacja wyników, z opcją dopracowania promptu i ponowienia analizy (`POST /.../retry`) lub akceptacji i zapisu posiłku (`POST /api/v1/meals`).
- **Szczegóły Posiłku:** Widok dostępny z historii, prezentujący pełne dane posiłku (`GET /meals/{meal_id}`) z leniwie ładowaną listą składników. Umożliwia edycję lub usunięcie wpisu.

**c. Strategia integracji z API i zarządzania stanem**

- **Zarządzanie stanem:** Aplikacja wykorzysta bibliotekę **React Query (TanStack Query)** do zarządzania stanem serwera. Zapewni to cachowanie, automatyczne unieważnianie danych po mutacjach (np. odświeżenie podsumowania dnia po dodaniu posiłku) oraz deklaratywną obsługę stanów ładowania i błędów.
- **Komunikacja z API:** Zostanie stworzony centralny wrapper/interceptor dla klienta API, który będzie zarządzał tokenem autoryzacyjnym JWT.
- **Optymalizacja:** Zastosowane zostanie **"optimistic UI"** dla operacji dodawania i usuwania posiłków, aby interfejs reagował natychmiastowo.

**d. Kwestie dotyczące responsywności, dostępności i bezpieczeństwa**

- **Responsywność (RWD):** Architektura będzie oparta o podejście **mobile-first**, z układami dostosowującymi się do większych ekranów.
- **Dostępność (a11y):** Wykorzystanie komponentów `shadcn/ui` opartych na Radix UI zapewni wysoki standard dostępności, w tym pełną obsługę z klawiatury i użycie regionów `aria-live` do komunikowania asynchronicznych zmian.
- **Bezpieczeństwo:** Aplikacja będzie polegać na mechanizmach autoryzacji API. Interceptor API obsłuży odpowiedzi `401 Unauthorized` poprzez wylogowanie użytkownika i przekierowanie go do strony logowania.
