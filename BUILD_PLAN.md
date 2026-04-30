# BUILD PLAN: Sika Family Vault

## Stack
- **Backend:** FastAPI + Python 3.12 + Supabase Postgres + SQLAlchemy 2.0
- **iOS:** Swift 6 + SwiftUI + @Observable + SwiftData
- **Android:** Kotlin 2 + Jetpack Compose + Material 3 + Room
- **API:** REST + Pydantic v2 + OpenAPI

## Phase: BUILD (Vertical Slices)

### Slice 1: Backend Core Models + API (FastAPI)
- [ ] SusuCircle model (id, name, contribution_amount, cycle_days, members[], status)
- [ ] SusuMember model (user_id, circle_id, position_in_rotation, status)
- [ ] RotationSchedule model (sequence, assigned_date, status, payout)
- [ ] Wallet model (balance, multi-sig approvals, transactions)
- [ ] Payment model (amount, method, status, confirmations)
- [ ] Pydantic schemas + CRUD endpoints
- [ ] Alembic migrations

### Slice 2: iOS — Susu Circle Creation + Member Invite
- [ ] Create circle flow (name, amount, cycle, max members)
- [ ] Member invite via link / phone number
- [ ] Circle dashboard (members, rotation, balance)

### Slice 3: iOS — Rotation Schedule + Payout Display
- [ ] Rotation timeline view
- [ ] Payout history
- [ ] Next payout countdown

### Slice 4: iOS — Wallet + Payments
- [ ] Balance display
- [ ] Mobile money deposit mock
- [ ] Transaction history

### Slice 5: Android Parity
- [ ] Mirror iOS screens in Kotlin/Jetpack Compose

### Slice 6: Auto-Round-Up (Backend)
- [ ] Transaction webhook listener
- [ ] Round-up calculation engine
- [ ] Auto-deposit to active Susu circle

### Slice 7: Family Sub-Accounts
- [ ] Parent-child account linking
- [ ] Chore-linked savings
- [ ] Parent approval for withdrawals

## Quality Gates
- [ ] TypeScript / Swift / Kotlin strict mode
- [ ] Backend tests ≥60% coverage
- [ ] No hardcoded secrets
- [ ] ESLint / SwiftLint / ktlint clean
- [ ] Build passes on Linux (Swift backend compile)

## STATUS: IN PROGRESS
