# BUILD_PLAN.md — Sika Family Vault

## Scope Decision
**Web MVP (Next.js 16 + FastAPI)** with mobile-first PWA design.
Native iOS/Android apps to follow in Phase 2. This maximizes overnight delivery probability while maintaining premium quality.

## Architecture
```
Frontend: Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui
Backend: FastAPI + Python 3.12 + Supabase (auth + db)
PWA: Service worker, offline support, add-to-home-screen
```

## Feature Priority (Review-Driven)

### P0 — Must Ship Tonight
1. **Susu Circle Creation** — Name, contribution amount, cycle length, member invites
2. **Transparent Rotation Schedule** — Who gets paid when, randomized fair order
3. **Group Wallet** — Multi-sig concept (2+ approvals for withdrawals)
4. **Mobile Money Integration** — MTN MoMo, Vodafone Cash, AirtelTigo (mock layer)
5. **Default Protection** — Insurance pool UI, penalty mechanism
6. **Credit Score Dashboard** — Visual score from participation history
7. **Auto-Round-Up** — Configure round-up rules, show accumulated savings

### P1 — If Time Permits
8. Family sub-accounts (parent/child)
9. Push notifications for payment reminders
10. Referral system

## Pages
1. Landing → Onboarding (30s max)
2. Dashboard → Circle list + create
3. Circle Detail → Members, schedule, wallet
4. Payment → Mobile money checkout
5. Profile → Credit score, settings
6. Insurance → Default protection pool

## Design System
- Primary: Gold/Amber (#D4A017) — wealth, prosperity, Ghana
- Neutral: Slate scale (50-900)
- Typography: Inter (body) + Playfair Display (headings)
- Icons: Lucide, outlined, 1.5px stroke
- Spacing: Generous whitespace, 24px base grid

## Commit Strategy (Vertical Slices)
1. `scaffold: Next.js + FastAPI + Supabase`
2. `feat: auth + onboarding`
3. `feat: Susu circle creation`
4. `feat: rotation schedule`
5. `feat: mobile money payments`
6. `feat: credit score + insurance`
7. `feat: auto-round-up`
8. `polish: premium minimalist design`
9. `test: quality gates`
10. `ship: push to GitHub`

## Status: BUILDING
