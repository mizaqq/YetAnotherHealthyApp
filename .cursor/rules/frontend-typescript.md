## Cursor Rule: Frontend (Next.js, TypeScript, Tailwind, shadcn/ui)

Applies to all frontend code for the Calorie Intake Logger PoC. Aim for a minimal, clear UX with chat-like meal entry, inline clarifications, and daily summaries. Follow the rules below when generating or editing frontend code.

### Stack and Scope

- Next.js (App Router, Server Components where possible)
- TypeScript strict mode
- React 18+/19 APIs (hooks-first)
- Tailwind CSS + shadcn/ui
- Supabase Auth (hosted)
- API base: `/api/v1` (FastAPI backend)

### Top-Level Principles

- Keep client bundles small: prefer Server Components and server data fetching.
- Deterministic UI flows; one clarification question max when needed.
- Optimistic yet reversible edits for meal items.
- Accessibility first: keyboard and screen-reader friendly.

## Architecture & Conventions

### Routes

Pages (App Router):

- `/login` (client): Supabase Auth UI flow
- `/log` (client/server hybrid): text input → preview parsed items → clarify inline → confirm & save
- `/day/[date]` (server): server fetch daily summary; client widgets for edits/deletes
- `/history` (server): simple date picker; link to day pages

Use Server Components by default for data fetching pages. Use Client Components only where interactivity is required (text input, inline edits, dialogs).

### Data Access

- Create a thin `lib/api.ts` with fetch helpers typed to backend contracts.
- Always type responses with shared types in `types/api.ts` mirroring backend models.
- Handle errors centrally; surface user-friendly toasts/messages.

### State Management

- Prefer local component state + URL state. Avoid heavy global stores.
- Use React Query or simple SWR for cacheable GETs (`/summary`, `/foods/search`).
- For ephemeral parse/clarify preview, keep state local to the `/log` page.

### Auth

- Use Supabase Auth client on the frontend. Store session in memory; avoid localStorage for tokens.
- Gate pages requiring auth via server redirects in layouts or route handlers.

### UI/UX Details

- Chat-like input on `/log` with inline clarify panel when `needs_clarification`.
- Inline edit for item grams and swap matched food via `/foods/search` autocomplete.
- Show per-item and total kcal/macros as soon as data is available.
- Provide loading skeletons and error boundaries.
- Support dark mode via Tailwind `dark:` variant.

### Styling

- Use Tailwind utility classes; extract reusable components with `@apply` where appropriate.
- Organize styles with `@layer` base/components/utilities if custom CSS is needed.

### Accessibility

- Use semantic HTML, labels for inputs, and `aria-*` where needed.
- Generate stable IDs with `useId` for labeling.
- Ensure focus states and keyboard navigation for dialogs and menus.

## API Contracts Usage

Base path: `/api/v1`.

- `POST /parse`: send `{ text }` → render preview with confidences; cache by input locally to prevent repeated calls.
- `POST /match`: send `{ items: [{ label, grams }] }` when user confirms or edits labels.
- `POST /log`: send `{ eaten_at?, note?, items }` after confirmation; re-fetch day summary.
- `GET /summary?date=`: server-fetch for `/day/[date]` route; stream UI sections.
- `GET /foods/search?q=`: use for autocomplete; debounce queries.

## Error Handling & UX

- Distinguish between validation errors (show inline hints) and server errors (toast + retry).
- For LLM ambiguities, display one short clarify question with up to 3 options; allow manual input as fallback.
- For network failures, allow retry and preserve user input.

## Performance

- Use Next.js Image and dynamic import for heavy components.
- Employ Suspense and streaming for `/day/[date]` where appropriate.
- Memoize expensive components and computations (`React.memo`, `useMemo`, `useCallback`).

## Testing

- Unit tests with Jest + Testing Library for components and hooks.
- E2E tests with Playwright for core flows: login, log meal, clarify, edit, delete, day summary.
- Prefer resilient locators and Page Object Model for Playwright specs.

## Coding Standards

- Strict TypeScript types; no `any` in exported types.
- Functional components only; hooks-first design.
- Keep components small and focused; extract reusable parts.
- Avoid deep prop drilling; pass callbacks and typed models.
- Keep comments only for non-obvious rationale.

---

### 10x Rules Mapped (Next.js, React, Tailwind, Jest, Playwright)

- Next.js
  - App Router, Server Components for data fetching, streaming/Suspense; Metadata API; optimized `next/image`; use new `Link` API; route handlers if needed.
- React
  - Functional components, hooks, `useCallback`/`useMemo`, `React.memo`, `useId`; consider `useTransition`/optimistic updates for forms.
- Tailwind
  - Use `@layer`, JIT, responsive/state variants, `@apply`, component extraction, dark mode.
- Jest
  - Testing Library, minimal snapshots, organized `describe` blocks, coverage, async helpers.
- Playwright
  - Context isolation, POM, resilient locators, traces, parallel runs, API checks.

---

### Project-Specific Notes

- Polish text for user-visible prompts/questions; code in English.
- Keep `/log` fast: debounce parse; cache by text to avoid redundant calls.
- Respect backend thresholds: only ask clarifications when flagged or high-impact.
- Provide a manual correction path when retrieval scores are low.
