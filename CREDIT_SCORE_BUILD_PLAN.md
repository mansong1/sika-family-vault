# BUILD PLAN: Credit Score Linkage from Susu Discipline

**App:** Sika Family Vault  
**Feature:** SusuScore™ — Alternative Credit Scoring from Rotating Savings  
**Effort:** 5-7 days → Compressed to overnight build  
**Stack:** FastAPI (backend) + Next.js 16 (frontend) + Supabase

## Architecture

### Scoring Model (SusuScore™)

Score range: 300–850 (standard FICO-compatible range)

**Factors (weighted):**

| Factor | Weight | Data Source | Rationale |
|--------|--------|-------------|-----------|
| On-time contribution rate | 30% | Susu circle payment history | Most predictive of credit reliability |
| Streak length (consecutive cycles) | 20% | Continuous participation | Long-term discipline signal |
| Circle size & role | 15% | Circle membership data | Larger circles = more social accountability |
| Contribution amount consistency | 15% | Payment variance | Stable income = stable credit |
| Default/delinquency history | 15% | Default records | Negative signal for lenders |
| Circle completion rate | 5% | Completed vs abandoned circles | Completion = commitment |

**Score tiers:**
- 300–579: Needs Improvement
- 580–669: Fair
- 670–739: Good
- 740–799: Very Good
- 800–850: Excellent

### Backend Components

```
backend/app/
├── models/susu_score.py      # SusuScore, ScoreFactor, ScoreHistory ORM models
├── services/score_engine.py  # Score computation engine
├── api/score_routes.py       # REST endpoints for score
├── tasks/score_refresh.py    # Background score recalculation
```

### Frontend Components

```
frontend/src/
├── components/CreditScoreWidget.tsx    # Main score display (circular gauge)
├── components/ScoreBreakdown.tsx       # Factor bar chart
├── components/ScoreHistory.tsx         # Trend line chart
├── components/ScoreImprovement.tsx     # Actionable tips card
├── components/ScoreShare.tsx          # Privacy-respecting share button
├── lib/credit-score-api.ts            # API client for score endpoints
├── app/credit-score/page.tsx          # Full credit score dashboard
```

### Premium Minimalist Design Rules
- Single accent: #D4AF37 (gold — Ghanaian / premium)
- Display: Inter Display Bold (score number)
- Body: Inter (everything else)
- Circular gauge for main score (not a progress bar)
- Glass-like card with subtle shadow for score breakdown
- Empty state: illustrated encouragement "Start a Susu circle to build your score"
- Error state: human-readable, actionable
- Skeleton loading throughout

## Quality Gates
1. TypeScript: `tsc --noEmit` — zero errors
2. Python: `ruff check .` — zero errors
3. Tests: new tests for score engine, API routes, React components
4. Coverage: ≥60%
5. Security: no secrets committed
6. Visual: premium minimalist compliance

## Success Criteria
- [ ] Score computed from real Susu participation data
- [ ] Score visible in dashboard widget
- [ ] Score breakdown shows factor contributions
- [ ] Score history shows trend
- [ ] Improvement tips are actionable
- [ ] All quality gates pass
- [ ] Pushed to mansong1/sika-family-vault on GitHub
