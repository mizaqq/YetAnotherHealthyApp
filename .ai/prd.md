# Dokument wymagań produktu (PRD) - YetAnotherHealthyApp

## 1. Przegląd produktu

YetAnotherHealthyApp to webowa aplikacja pomagająca osobom świadomie zarządzającym dietą w szybkim zapisywaniu posiłków oraz monitorowaniu spożycia kalorii i makroskładników. MVP kładzie nacisk na prosty interfejs pozwalający wprowadzić opis posiłku w wolnym tekście, wykorzystanie modeli AI do przeliczenia składników na makroelementy oraz czytelne raportowanie postępów względem ustalonych celów.

Aplikacja przechowuje dane użytkowników w Supabase, zapewniając izolację wpisów dzięki RLS. System bazuje na ograniczonej, kanonicznej liście produktów wspieranej danymi Open Food Facts i uzupełnianej wiedzą modelu językowego. Priorytetem MVP jest wiarygodność wyliczeń.

## 2. Problem użytkownika

Świadome osoby dbające o dietę mają trudność w szybkim dopasowaniu istniejących w sieci przepisów do własnych potrzeb żywieniowych. Ręczne liczenie kalorii i makroskładników z opisów dań jest czasochłonne, wymaga wiedzy o składnikach i często prowadzi do błędów. Dostępne narzędzia rzadko wspierają specyficzne jednostki i lokalne zwyczaje kulinarne, a zestawienia makroskładników są trudno dostępne. Użytkownicy potrzebują rozwiązania, które od razu po wpisaniu posiłku podpowie możliwe makroskładniki i kalorie, pozwoli je dopracować oraz zapewni historię i raporty postępów.

## 3. Wymagania funkcjonalne

3.1 Autentykacja i bezpieczeństwo

- Rejestracja oraz logowanie z wykorzystaniem supabase, z uwierzytelnianiem na podstawie loginu i hasła.
- Wymuszenie polityki haseł (minimum długości i złożoności) oraz obsługa resetu hasła przez e-mail.
- Separacja danych użytkowników za pomocą RLS, tak aby każdy widział tylko własne wpisy.
- Obsługa utrzymywania sesji i bezpiecznego wylogowania.

  3.2 Dodawanie posiłków

- Formularz dodawania posiłków wymaga wyboru kategorii z listy: śniadanie, drugie śniadanie, obiad, podwieczorek, kolacja.
- Użytkownik wpisuje opis posiłku w wolnym tekście, z obsługą jednostek g, ml, szt, kromka, łyżka, szklanka.
- System oznacza, kiedy zastosowano domyślne wagi jednostek oraz pozwala użytkownikowi je nadpisać.

  3.3 Analiza AI

- Opis posiłku trafia do pipeline’u AI, który parsuje składniki, mapuje je na kanoniczną listę produktów i ocenia pewność dopasowania.
- Dla dopasowań z progiem pewności ≥0,8 wynik zawiera identyfikator produktu z listy; poniżej progu model korzysta z własnej wiedzy i oznacza brak dopasowania.
- Wynik analizy jest zwracany w ustrukturyzowanym JSON zawierającym sumę makroskładników i kalorii dla posiłku oraz listę składników z wagami i makrami cząstkowymi.

  3.4 Edycja i akceptacja wyników

- Użytkownik otrzymuje wizualizację wyniku (totals i lista składników), może wprowadzać poprawki w opisach, wagach i jednostkach.
- Aplikacja umożliwia ponowne wywołanie modelu AI po edycji.
- Użytkownik akceptuje finalny wynik, co skutkuje utrwaleniem wpisu wraz z metadanymi (kategoria, kaloria, makroskładniki i półproduktu).
- System przechowuje historię poprawek i oznacza, które półprodukty korzystają z domyślnych wag.

  3.5 Tryb ręczny

- W przypadku błędu modelu lub decyzji użytkownika formularz pozwala wprowadzić makra (kalorie, białko, tłuszcz, węglowodany) bez udziału AI.
- Ręczne wpisy są wyraźnie oznaczone i mogą zostać później edytowane lub ponownie przeliczone przez AI.

  3.6 Historia i raportowanie

- Widok historii prezentuje listę posiłków z możliwością filtrowania po dacie oraz przeglądu składników.
- Dashboard pokazuje dzienny pasek progresu względem celu kalorycznego oraz trend 7-dniowy.
- Wszystkie daty i agregacje bazują na lokalnej strefie czasowej serwera.

  3.7 Ustawienia i cele użytkownika

- Podczas onboarding’u użytkownik definiuje dzienny cel kaloryczny.
- Użytkownik może aktualizować cel oraz preferencje jednostek w ustawieniach.
- Zmiany celu aktualizują bieżące raporty.

  3.8 Stabilność, koszty i obserwowalność

- System loguje wszystkie wywołania AI (wraz ze stanem sukces/błąd) oraz retrysy.
- Manualne korekty są znakowane i dostępne do dalszej analizy jakościowej.

## 4. Granice produktu

4.1 Poza zakresem MVP

- Brak obsługi multimediów (np. zdjęć dań).
- Brak udostępniania posiłków innym użytkownikom i funkcji społecznościowych.
- Brak aplikacji mobilnej; MVP obejmuje wyłącznie aplikację webową.
- Brak aktualizacji bazy produktów (Open Food Facts) w czasie rzeczywistym; aktualizacje po MVP.
- Brak cache’owania odpowiedzi modelu i brak RAG.

  4.2 Założenia i obszary do doprecyzowania

- Określenie, czy w trybie ręcznym dopuszczamy wprowadzanie tylko kalorii, czy również makr oraz jakie walidacje stosować.
- Zasady retencji logów, w tym przechowywania promptów i odpowiedzi LLM oraz anonimizacji danych.
- Strategia rozbudowy kanonicznej listy produktów i wykorzystania korekt użytkownika po MVP.
- Ewentualne zasady wyliczania makr na podstawie kalorii (lub odwrotnie) w sytuacjach braków danych.

## 5. Historyjki użytkowników

### US-001

ID: US-001
Tytuł: Rejestracja konta użytkownika
Opis: Jako nowy użytkownik chcę utworzyć konto, aby przechowywać własne dane dotyczące posiłków.
Kryteria akceptacji:

- System wymaga unikalnego adresu e-mail oraz hasła o długości co najmniej 8 znaków z cyfrą i literą.
- Jeśli adres e-mail jest już zajęty, użytkownik otrzymuje komunikat i rejestracja nie dochodzi do skutku.
- Po poprawnej rejestracji użytkownik jest automatycznie zalogowany i przekierowany do ustawienia celu kalorycznego.

### US-002

ID: US-002
Tytuł: Logowanie i bezpieczny dostęp
Opis: Jako powracający użytkownik chcę się zalogować, aby uzyskać dostęp do własnych danych.
Kryteria akceptacji:

- Prawidłowe dane logowania zapewniają dostęp do panelu głównego.
- Nieprawidłowe dane powodują komunikat o błędzie bez ujawniania, które pole jest niepoprawne.
- Po zalogowaniu użytkownik widzi wyłącznie własne posiłki dzięki polityce RLS.

### US-003

ID: US-003
Tytuł: Dodanie posiłku do analizy AI
Opis: Jako użytkownik chcę dodać opis posiłku i kategorię, aby system wyliczył makroelementy.
Kryteria akceptacji:

- Formularz wymaga wyboru kategorii z listy śniadanie, drugie śniadanie, obiad, podwieczorek, kolacja oraz nie pozwala wysłać pustego opisu.
- System rozpoznaje jednostki g, ml, szt, kromka, łyżka, szklanka i stosuje domyślne wagi, gdy brak danych liczbowych.
- Analiza AI zwraca wynik w formacie JSON z sumą dla posiłku i listą składników z wagami i makrami. Wynik jest prezentowany uzytkownikowi w formie tabeli.
- Składniki z dopasowaniem ≥0,8 są oznaczone identyfikatorem z listy kanonicznej; w przeciwnym razie wynik sygnalizuje fallback do wiedzy modelu.

### US-004

ID: US-004
Tytuł: Korekta i ponowne przeliczenie posiłku
Opis: Jako użytkownik chcę edytować wynik AI i ponownie go przeliczyć, aby uzyskać dokładniejsze makra.
Kryteria akceptacji:

- Użytkownik może edytować listę składników, ich wagi oraz jednostki przed ponownym przeliczeniem.
- Ponowne wywołanie analizy kończy się w czasie ≤12 s i generuje zaktualizowany JSON.
- System wyraźnie oznacza składniki korzystające z domyślnych wag po edycji.
- Historia analizy zachowuje informację o liczbie przeliczeń i ich statusie.

### US-005

ID: US-005
Tytuł: Akceptacja i zapis przeliczonego posiłku
Opis: Jako użytkownik chcę zaakceptować wynik, aby dodać posiłek do swojej historii.
Kryteria akceptacji:

- Przycisk akceptacji jest dostępny dopiero po obejrzeniu sumy i listy składników.
- Akceptacja zapisuje posiłek wraz z kategorią, datą i godziną w strefie serwera oraz źródłem danych (AI lub ręczne).
- Zapisany posiłek natychmiast pojawia się w historii dnia i w dziennym podsumowaniu makr.
- System przechowuje informację o tym, czy wpis pochodzi z pierwszej czy kolejnej iteracji analizy.

### US-006

ID: US-006
Tytuł: Ręczne wprowadzenie makroelementów
Opis: Jako użytkownik chcę ręcznie wprowadzić makra, gdy analiza AI zawodzi lub gdy wolę szybki wpis.
Kryteria akceptacji:

- Użytkownik może przełączyć się do trybu ręcznego zarówno po błędzie modelu, jak i przed wysłaniem analizy.
- Formularz wymaga wypełnienia tylko kalorii.
- Ręczny wpis jest oznaczony jako manualny i może zostać później edytowany lub przekonwertowany na wynik AI.

### US-007

ID: US-007
Tytuł: Przegląd dziennej historii
Opis: Jako użytkownik chcę przeglądać listę posiłków z danego dnia, aby monitorować dzienne spożycie.
Kryteria akceptacji:

- Widok historii prezentuje posiłki w kolejności chronologicznej wraz z kategorią i krótkim podsumowaniem makr.
- Dzienny pasek progresu pokazuje procent realizacji celu kalorycznego na podstawie wszystkich zapisanych posiłków.
- Użytkownik może wybrać dowolną datę do przeglądu oraz otworzyć szczegóły poszczególnych posiłków.

### US-008

ID: US-008
Tytuł: Analiza trendu 7-dniowego
Opis: Jako użytkownik chcę obserwować trend spożycia kalorii z ostatnich 7 dni, aby ocenić konsekwencję w działaniu.
Kryteria akceptacji:

- Dashboard prezentuje wykres lub analogiczną wizualizację 7-dniowego trendu.
- Trend aktualizuje się po każdym nowym, edytowanym lub usuniętym wpisie.
- Dni bez posiłków są prezentowane z wartością zero i odpowiednią etykietą.

### US-009

ID: US-009
Tytuł: Konfiguracja i zmiana celu kalorycznego
Opis: Jako użytkownik chcę ustawić i modyfikować dzienny cel kalorii, aby odzwierciedlał mój plan żywieniowy.
Kryteria akceptacji:

- Pierwsze logowanie wymaga podania dziennego celu kalorycznego.
- Użytkownik może w dowolnym momencie zaktualizować cel z poziomu ustawień.
- Po zmianie celu procent realizacji i raporty dzienne aktualizują się przy następnym obliczeniu.

## 6. Metryki sukcesu

- Co najmniej 75% propozycji AI zaakceptowanych (po ewentualnej edycji) w próbie 200 analiz.
- 95% odpowiedzi AI dostarczonych w czasie ≤12 s.
- 90% nowo zarejestrowanych użytkowników kończy onboarding z ustawieniem celu kalorycznego w ciągu pierwszej sesji.
- 99% prób dostępu do danych innego użytkownika blokowanych dzięki RLS (brak incydentów naruszających izolację danych).
