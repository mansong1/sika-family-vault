# Sika Bank — Family Vault (Susu Circles)

## Problem
West Africans save in groups (Susu, Ajo, Esusu) — rotating savings clubs where 10-20 people pool money monthly, one person takes the pot each cycle. No digital equivalent exists that understands the cultural trust dynamics.

## Solution
Digital Susu circles with group wallets, auto-round-up, and cultural trust mechanisms.

## Features
- [ ] Create Susu circle (invite members, set contribution amount, set cycle)
- [ ] Group wallet (multi-sig, requires 2+ approvals for withdrawals)
- [ ] Auto-round-up (round every purchase to nearest 1 GHS, deposit to Susu)
- [ ] Rotation schedule (who gets the pot when — transparent, no disputes)
- [ ] Late payment handling (grace period, penalty, replacement member)
- [ ] Default protection (insurance for circle collapse)
- [ ] Credit score boost (consistent Susu participation = better score)
- [ ] Family sub-accounts (parent controls, child savings, chore-linked)

## Technical
- FastAPI backend, Supabase Postgres
- Multi-sig wallet logic (smart contract on Celo or L2)
- Mobile money integration (MTN MoMo, Vodafone Cash)
- Target: iOS 18+, Android 14+

## Competitor Pain Points
- Chipper Cash: No Susu feature, just peer-to-peer
- PiggyVest: Savings pots exist but no group/rotation mechanism
- Cowrywise: Investment focus, no cultural savings products
- Esusu (US): African diaspora only, no mobile money, no auto-round-up

## Differentiation
- First digital Susu with mobile money integration
- Auto-round-up makes saving invisible
- Credit score linkage (participation = creditworthiness)
- Default insurance (protects against circle collapse)

## Out of Scope
- Investment returns (Susu is savings, not investing)
- Cross-border Susu (Phase 2)
- Interest on savings (not how Susu works)

## Stack
iOS (Swift/SwiftUI) + Android (Kotlin/Jetpack Compose) + FastAPI + Supabase
