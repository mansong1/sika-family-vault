# Sika Bank — Family Vault

Digital Susu circles for West Africa. Save together, grow together.

## What is Susu?

Susu (also known as Ajo, Esusu, Chama, or Stokvel) is a centuries-old rotating savings system where trusted groups pool money monthly — one member takes the pot each cycle. It's the backbone of community finance across West Africa, but until now there's been no digital equivalent that truly understands the cultural trust dynamics.

## Competitor Pain Points Solved

| Pain Point | Source | Our Solution |
|-----------|--------|-------------|
| "Who holds my money?" — Trust issues | All platforms | Multi-sig group wallets, transparent on-chain ledger |
| Hidden fees (AjoApp: 3.3%) | User reviews | Zero hidden fees — shown upfront |
| No group/rotation mechanism | PiggyVest, Chipper Cash | First-class Susu circles with auto-rotation |
| App crashes, login failures | PiggyVest reviews | Offline-first architecture |
| Poor customer service (single line) | PiggyVest reviews | In-app chat + 24h SLA |
| No mobile money integration | Chipper Cash (limited) | MTN MoMo, Vodafone Cash, AirtelTigo native |
| Default risk — circle collapses | Traditional Susu | Default insurance pool + penalty mechanism |
| No credit score from discipline | All platforms | Credit score improves with every on-time payment |

## Features

- **Susu Circle Creation** — Invite members, set contribution amount and cycle
- **Transparent Rotation** — Randomized fair order, visible to all members
- **Mobile Money Payments** — MTN MoMo, Vodafone Cash, AirtelTigo (mock layer)
- **Default Protection** — 2% insurance pool protects against circle collapse
- **Credit Score Dashboard** — Consistent participation = better score
- **Auto Round-Up** — Round every purchase to nearest GHS, save automatically
- **Family Sub-Accounts** — Parent controls, child savings (Phase 2)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 + TypeScript + Tailwind v4 |
| Backend | FastAPI + Python 3.12 |
| Auth | JWT + bcrypt (PBKDF2) |
| Database | In-memory (Supabase in production) |
| PWA | Service worker, add-to-home-screen |
| Design | Premium Minimalist (gold + slate) |

## Design System

- **Primary:** Gold/Amber (#D4A017) — wealth, prosperity, Ghana
- **Neutral:** Slate scale
- **Typography:** Inter (body) + Playfair Display (headings)
- **Icons:** Lucide, outlined, 1.5px stroke
- **Spacing:** Generous whitespace, 24px base grid

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/dashboard | Dashboard data |
| GET | /api/v1/circles | List circles |
| POST | /api/v1/circles | Create circle |
| GET | /api/v1/circles/{id} | Circle detail |
| POST | /api/v1/circles/{id}/join | Join circle |
| POST | /api/v1/circles/{id}/pay | Make payment |
| GET | /api/v1/circles/{id}/schedule | Rotation schedule |
| GET | /api/v1/credit-score | Credit score |
| POST | /api/v1/roundup | Create round-up rule |

## Quality Gates

- TypeScript strict: ✅
- ESLint: ✅ (clean)
- Python ruff: ✅
- Tests: 4/4 passing ✅
- No hardcoded secrets: ✅
- Next.js build: ✅

## What's Next

- Native iOS (Swift/SwiftUI) + Android (Kotlin/Jetpack Compose)
- Real mobile money API integration
- Supabase + PostgreSQL
- Push notifications
- Smart contract multi-sig wallet (Celo)

## License

MIT

## Credits

Built overnight by the OpenClaw overnight-builder pipeline.
