# Aktualizacja wymagań - Potwierdzenie emaila przy rejestracji

Data aktualizacji: 2025-10-24

## Zmiana w PRD

### Przed zmianą (US-001)

> Po poprawnej rejestracji użytkownik jest automatycznie zalogowany i przekierowany do ustawienia celu kalorycznego.

### Po zmianie (US-001)

> Po poprawnej rejestracji użytkownik otrzymuje email z linkiem potwierdzającym, który musi kliknąć aby aktywować konto. Po potwierdzeniu emaila użytkownik może się zalogować i jest przekierowany do ustawienia celu kalorycznego.

## Zaktualizowane dokumenty

### 1. `.ai/prd.md`

- Zaktualizowano US-001: dodano wymóg potwierdzenia emaila
- Usunięto "automatyczne zalogowanie po rejestracji"

### 2. `.ai/auth-spec.md`

Zaktualizowano sekcje:

- **Kontekst i założenia** - nowy opis US-001
- **1.4. Scenariusze kluczowe** - dodano flow potwierdzenia emaila
- **3.1. Rejestracja, logowanie, wylogowanie** - wymóg `enable_confirmations = true`
- **8. Zależności konfiguracyjne Supabase** - wymaganie włączenia potwierdzenia emaila
- **10. Testowalność i kryteria akceptacji** - nowe scenariusze testowe

### 3. `apps/supabase/config.toml`

Zmieniono ustawienie:

```toml
[auth.email]
enable_confirmations = true  # było: false
```

## Wpływ na UX

### Nowy flow rejestracji:

1. **Użytkownik wypełnia formularz rejestracji** (`/register`)

   - Email (unikalny)
   - Hasło (min. 8 znaków, 1 litera, 1 cyfra)

2. **Po kliknięciu "Zarejestruj się"**

   - System wywołuje `supabase.auth.signUp()`
   - Użytkownik widzi komunikat: "Sprawdź swoją skrzynkę pocztową"
   - Email z linkiem potwierdzającym jest wysyłany

3. **Lokalnie (development)**

   - Email pojawia się w InBucket: `http://localhost:54324`
   - Zawiera link potwierdzający do kliknięcia

4. **Po kliknięciu linku w emailu**

   - Konto zostaje aktywowane
   - Użytkownik może się zalogować

5. **Pierwsze logowanie**
   - Przekierowanie do `/onboarding`
   - Ustawienie dziennego celu kalorycznego

## Wymagane zmiany w UI (TODO - w kolejnym etapie)

### Nowa strona: `EmailConfirmationPendingPage`

Powinna zawierać:

- Komunikat: "Sprawdź swoją skrzynkę pocztową"
- Informację o kliknięciu linku potwierdzającego
- Link "Nie otrzymałeś emaila?" (opcjonalnie - resend)
- Link powrotny do logowania

### Aktualizacja `RegisterPage`

Po sukcesie rejestracji:

- Pokazać komunikat "Sprawdź skrzynkę pocztową" (inline lub przekierowanie)
- Alternatywnie: przekierować na `/email-confirmation-pending`

### Obsługa błędów logowania

Dodać specjalny komunikat dla przypadku:

- Użytkownik próbuje się zalogować przed potwierdzeniem emaila
- Komunikat: "Potwierdź swój adres email przed zalogowaniem. Sprawdź skrzynkę pocztową."

## Konfiguracja lokalna (już zrobione)

### `config.toml`

```toml
[auth]
site_url = "http://127.0.0.1:3000"
additional_redirect_urls = [
  "https://127.0.0.1:3000",
  "http://127.0.0.1:3000/reset-password/confirm",
  "http://localhost:5173/reset-password/confirm"  # Vite dev server
]

[auth.email]
enable_confirmations = true  # ✅ Włączone
```

### InBucket

- URL: `http://localhost:54324`
- Automatycznie przechwytuje wszystkie emaile w local dev
- Nie wymaga dodatkowej konfiguracji

## Restart Supabase (wymagany!)

Po zmianie `config.toml` należy zrestartować Supabase:

```bash
cd apps/supabase
supabase stop
supabase start
```

## Metryki sukcesu (zaktualizowane w PRD)

Bez zmian w tej aktualizacji, ale warto monitorować:

- % użytkowników, którzy potwierdzają email w ciągu 24h
- % użytkowników, którzy kończą onboarding po potwierdzeniu emaila
- Czas od rejestracji do pierwszego zalogowania

## Bezpieczeństwo

### Zalety email confirmation:

✅ Weryfikacja prawdziwości adresu email
✅ Ochrona przed spam/fake accounts
✅ Możliwość komunikacji z użytkownikiem
✅ Standard w aplikacjach produkcyjnych

### Uwagi:

- Email confirmation nie chroni przed botnets (do tego potrzebne CAPTCHA)
- Rate limiting już skonfigurowane w config.toml: `email_sent = 2` (na godzinę)

## Następne kroki

1. ✅ Zaktualizować PRD i auth-spec.md
2. ✅ Włączyć `enable_confirmations = true` w config.toml
3. ✅ Zrestartować Supabase local
4. ⏳ Stworzyć stronę/komponent dla "Sprawdź email"
5. ⏳ Zaktualizować `RegisterPage` - obsługa sukcesu rejestracji
6. ⏳ Dodać mapowanie błędów dla niepotwierdzonych kont w `useAuth`
7. ⏳ Dodać opcję "Wyślij ponownie email" (resend)
8. ⏳ Przetestować cały flow lokalnie z InBucket

## Testing checklist

- [ ] Rejestracja wysyła email do InBucket
- [ ] Email zawiera działający link potwierdzający
- [ ] Kliknięcie linku aktywuje konto
- [ ] Logowanie przed potwierdzeniem pokazuje odpowiedni błąd
- [ ] Logowanie po potwierdzeniu działa i przekierowuje do `/onboarding`
- [ ] Próba rejestracji z tym samym emailem przed potwierdzeniem
- [ ] Próba rejestracji z tym samym emailem po potwierdzeniu

---

**Uwaga:** Zmiana ta może wpłynąć na istniejące testy integracyjne i E2E, które zakładały automatyczne logowanie po rejestracji.
