# Mobile SaaS Plan — Net-Worth Tracker

Plan for spinning the `networth` app out of this personal repo into a standalone,
subscribable, mobile-only product: a FastAPI backend (Django ORM underneath, same
pattern as `main.py`/nwokoro-ai) plus a React Native app, no web client.

## Decisions locked in

- **Backend**: rewrite the API as FastAPI, importing Django models directly (same
  pattern already used by `main.py` for the AI advisor), not Django REST Framework.
- **Product scope**: net-worth/finance only — `Saving`, `Investment`, `Stock`,
  `Business`, `FixedAsset`, `Liability`, forecasting, reports. `chore`, `achieve`,
  and the portfolio/`core` pages stay behind in the personal site and are not part
  of the SaaS product.
- **Client**: React Native only. No web version of the new product.
- **Repo**: fresh workspace, forked from this one, not built in-place.

## Starting position (what's reusable)

- Every relevant model already has a per-user `owner`/`user` FK (`Saving`,
  `Investment`, `Stock`, `Business`, `FixedAsset`, `Liability`, and every
  `*Transaction` table) — the data layer is not hardcoded to a single user.
- ROI/valuation/forecast math already lives in `networth/tools.py` and is reusable
  as-is.
- Signup/activation flow already exists (`account/templates/account/sign_up_form.html`,
  `core/templates/core/activate_registration.html`).
- `main.py` already proves the "FastAPI service importing Django ORM models" pattern
  works and deploys to Heroku independently.
- A policy/markdown page renderer was just added (commit `dfd28e7`) — reusable for
  ToS/privacy pages.

## Phases

### Phase 0 — Repo split (2–3 days)
- Fork into a fresh workspace.
- Strip `chore`, `achieve`, and portfolio-only `core` views/templates.
- Keep `networth` models/migrations, `account` (auth/user), and enough of `core`
  for shared plumbing (context processors, base settings).

### Phase 1 — Multi-tenancy audit (1 week)
- Find and fix hardcoded single-user assumptions, e.g. `FinancialData.owner
  default=1`.
- Confirm scope of `ExchangeRate` (global reference data vs. per-user) and keep it
  global if so.
- Audit admin views and management commands for implicit single-owner assumptions.
- Enforce row-level filtering (by authenticated user) on every query path that will
  be exposed over the API.

### Phase 2 — Auth API (1–1.5 weeks)
- JWT login/refresh, signup, email verification, password reset as JSON endpoints
  (replacing the current session/template-based flow for the API surface).
- Basic abuse protection (rate limiting on auth endpoints) since this is now
  public-facing.

### Phase 3 — Billing (2–3 weeks)
- Stripe customers/subscriptions/webhooks, entitlement checks gating API access.
- Apple App Store and Google Play in-app-purchase integration — required by Apple
  for digital subscriptions purchased in-app; not optional if distributing through
  the App Store.
- This phase carries the most schedule risk; see Sequencing below.

### Phase 4 — FastAPI endpoints (4–6 weeks)
- JSON CRUD + actions (rollover, liquidate, repay, plow-back, convert, rent) for
  all six asset types.
- Dashboard aggregation and forecast endpoints.
- Replace Matplotlib/mpld3 image generation (`networth/plots.py`) with raw
  numeric/time-series data for native charting in RN.
- Decide PDF/balance-sheet delivery for mobile (likely: keep the existing
  Celery/WeasyPrint pipeline, deliver via email or a signed download link, don't
  render PDFs on-device).

### Phase 5 — React Native app (6–10 weeks)
- Auth screens (login/signup/verify/reset).
- Dashboard + native charts.
- List/detail/create/edit screens for all six asset types.
- Paywall / subscription screens (App Store/Play Store IAP flow).
- Settings/preferences, currency selection.

### Phase 6 — Genericization (1–2 weeks)
- Currency support beyond the current hardcoded `('NGN', 'CAD', 'USD')` — 
  `django-money` already supports arbitrary currencies, so this is mostly
  loosening a constraint, not a rewrite.
- Onboarding copy and terminology reworked for a general audience (not
  Uzo-specific institutions/context).
- ToS/privacy pages (reuse the new policy page renderer from commit `dfd28e7`).

### Phase 7 — Infra + store review (1–2 weeks + review latency)
- Separate Heroku app/DB tier appropriate for holding other people's financial
  data (not a hobby/free tier).
- Apple ($99/yr) and Google ($25 one-time) developer accounts.
- App Store / Play Store submission and review cycles — days to weeks per round,
  outside direct control, can bounce on subscription or privacy-disclosure issues.

## Sequencing recommendation

Build one asset type (`Saving`) end-to-end through Phases 0–4 plus a bare-bones RN
screen and a working Stripe/IAP charge first, before fanning out to the other five
asset types. This surfaces App Store/billing problems — the highest-risk,
least-code-related part of this plan — early instead of after all six asset types
are built out.

## Biggest risks (not effort, but exposure)

- **Other people's financial data** raises the bar substantially: encryption at
  rest, data export/deletion rights, incident response — this is a liability
  surface, not just an engineering task, once it's not just personal data anymore.
- **Apple IAP compliance** is a hard requirement, not a nice-to-have, for
  subscriptions sold through the iOS app.
- **App review latency** is outside your control and can add weeks if the first
  submission is rejected.

## Total estimate

Roughly **3–5 months solo, part-time**. Faster with full-time focus or a reduced
initial scope (e.g., launch with 2 asset types instead of 6).
