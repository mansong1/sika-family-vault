# Auto-Round-Up → Susu Savings — Feature Spec

## Problem
**No Susu/circle app globally offers auto-round-up contributions.** Acorns, Qapital, and Revolut all offer round-ups into personal savings/investing, but zero competitors link round-ups to rotating savings circles — where the cultural money ritual matters most.

## Solution
Every purchase rounds up to nearest 1 GHS (or configurable unit: 5 GHS). Spare change automatically flows into the user's active Susu circles. Users see exactly which circles their spare change is funding — turning invisible transactions into visible community wealth.

## Key Differentiation
- **First globally** to connect spare-change automation with rotating savings circles
- Directly solves the #1 Susu pain point: missed contributions
- Turns "I forgot to contribute" into "I contribute automatically"

## Competitor Pain Points (Synthesized from Research)

### Round-Up Apps — What Sucks
| Pain Point | Frequency | Source | Our Solution |
|-----------|-----------|--------|-------------|
| Bank connection failures break round-ups | Very common | Acorns reviews | Manual trigger option + Mobile Money API (no bank connection needed) |
| Overdraft risk — apps pull money causing negative balance | Common | Qapital reviews | Balance-aware: never pull if checking < threshold |
| High fees eat small contributions | Very common | Acorns BBB F-rating | **Zero fees on auto-round-up** — differentiator in African market |
| Can't pause rules temporarily | Common | Qapital reviews | One-tap pause per circle, auto-resume after date |
| Delayed withdrawals — spare change stuck | Common | Multiple apps | Real-time sweep into Susu circle wallet |
| No group visibility | Silent gap | All competitors | **Circle-wide round-up tracker** — members see collective spare-change pool grow |
| No credit score link | Silent gap | All competitors | Round-up consistency → credit score boost (credit bureaus in Ghana/Nigeria) |

### Must-Match Features (What Users Love)
1. **Set-and-forget simplicity** — configure once, spare change flows forever
2. **Visual progress** — see accumulated round-ups in real time
3. **Multiplier options** — 2x, 5x round-up boost for aggressive savings
4. **Goal linking** — each round-up tagged to a specific circle/goal
5. **Transaction history** — every round-up logged, transparent

### Wish-List Features We'll Build
- **Per-circle allocation** — split round-ups across multiple circles (e.g., 60% family Susu, 40% personal goal)
- **Round-up floor** — minimum spare change to trigger sweep (avoid micro-sweeps)
- **Weekend boost** — 2x round-ups on weekends (gamification)
- **Circle leaderboard** — who contributed most spare change this month?

## Architecture

### Backend (FastAPI)
```
/backend/app/
├── services/
│   └── round_up_service.py    # NEW: Round-up engine
├── models/
│   └── round_up.py            # NEW: RoundUpRule, RoundUpTransaction models
├── api/
│   └── round_ups.py           # NEW: Round-up CRUD + config API
└── crud/
    └── round_up_crud.py       # NEW: DB operations
```

### Frontend (Next.js 16)
```
/frontend/src/
├── components/
│   ├── RoundUpConfig.tsx      # NEW: Configure round-up rules
│   ├── RoundUpWidget.tsx      # NEW: Dashboard widget showing accumulated
│   ├── RoundUpHistory.tsx     # NEW: Transaction log
│   └── CircleRoundUp.tsx      # NEW: Per-circle round-up view
├── app/
│   └── round-ups/
│       ├── page.tsx           # NEW: Round-up settings page
│       └── [circleId]/page.tsx # NEW: Per-circle round-up detail
└── lib/
    └── round-up-api.ts        # NEW: API client
```

### Data Models
```python
class RoundUpRule(Base):
    id: UUID
    user_id: UUID
    circle_id: UUID (nullable — can be personal savings)
    active: bool
    round_to: Decimal  # 1 GHS default
    multiplier: int  # 1x, 2x, 5x
    floor_amount: Decimal  # minimum spare change to sweep (default 0.10 GHS)
    weekly_cap: Decimal  # max round-up per week
    allocation_pct: float  # % of round-ups going to this circle
    created_at: datetime

class RoundUpTransaction(Base):
    id: UUID
    user_id: UUID
    circle_id: UUID
    rule_id: UUID
    purchase_amount: Decimal
    rounded_amount: Decimal
    spare_change: Decimal  # rounded - purchase
    swept_at: datetime
    source_tx_id: str  # linked to mobile money transaction
```

## Design (Premium Minimalist)
- Round-up widget on dashboard: subtle gold amber progress ring around circle icon
- Animation: coins "falling" into circle when sweep completes (purposeful only)
- Typography: Inter for numbers (tabular figures), Playfair Display for circle names
- Zero visual noise — one toggle, one slider, done

## API Endpoints
- `POST /api/round-ups/rules` — Create round-up rule
- `GET /api/round-ups/rules?circle_id=X` — List rules
- `PATCH /api/round-ups/rules/{id}` — Update rule (pause, change multiplier)
- `DELETE /api/round-ups/rules/{id}` — Delete rule
- `GET /api/round-ups/transactions?circle_id=X` — Transaction history
- `POST /api/round-ups/simulate` — Simulate round-up on mock purchase
- `GET /api/round-ups/stats?circle_id=X` — Aggregate stats for circle
