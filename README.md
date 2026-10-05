# Utility Debt Shield (prototype)

![tests](https://github.com/elmir132/utility-debt-shield/actions/workflows/ci.yml/badge.svg)

A small API that answers one question for a rental platform before a lease is signed: **could the new tenant run into trouble turning the utilities on at this address?** It flags unpaid balances, meter holds and deposit requirements, and says how serious the friction is.

## Context and contribution

Utility Debt Shield was my idea in the Cornell Tech Product Studio (Team 419: Elmir Abdullaiev, Yihan Gu, Xie Li; fall 2026). Each teammate pitched a different idea; the others were MoveLog (Yihan) and SafePath NYC (Xie Li). I also developed Utility Debt Shield for my own NBAY 6080 business plan. **The code and tests in this repository are mine, written with AI assistance (Claude Code); I specified the rules and the caveats and reviewed the result.** It is a prototype of the check itself, not a product.

## What it is not

- **No real utility data.** The only data source is a mock that returns fictional, deterministic records (`udshield/providers.py`). Every name and figure is invented. No utility company or data aggregator is integrated.
- **Not a debt claim.** Utility debt generally follows the *account holder*, not the address, so a new tenant does not simply inherit a previous tenant's balance. What a balance, shut-off or meter hold can cause is *activation friction*: deposits, disputes, a technician visit, delay. The output wording reflects that, and a high-friction result says explicitly that it does not by itself mean the renter owes anything.
- **Consent is required.** Reading utility account data through aggregators needs the account holder's consent, so the API refuses a check unless the request carries `"consent": true`.
- **Data availability is the real risk.** Aggregators differ in what they expose; some bill APIs return no balance or past-due field at all. The engine treats a missing field as *unknown*, never as *clean*.

## How it works

```
POST /v1/checks  {address, consent}  ->  provider.fetch(address)  ->  rules engine  ->  result
```

### Decision table

Rules live in `udshield/engine.py` and are deterministic; the thresholds are constants at the top of the file. The boundaries below are covered row by row in `tests/test_boundaries.py`.

| Balance | Days past due | Friction |
|---|---|---|
| credit or $0 | any | none |
| $0.01 to $49.99 | under 60 or unknown | low |
| $50.00 to $299.99 | under 60 or unknown | medium |
| $300.00 or more | any | high |
| any amount above $0 | 60 or more | high |
| not reported | n/a | info flag only; overall `unknown` if nothing else is known |

Other signals, independent of the balance:

| Signal | Friction |
|---|---|
| Meter hold | high |
| Deposit required (above $0) | medium |

The overall result is the worst flag across all utilities.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py        # http://localhost:5000  (PORT=5058 python app.py to change)
pytest -q
```

```bash
curl -X POST localhost:5000/v1/checks \
  -H 'content-type: application/json' \
  -d '{"address": "3 demo street, example city", "consent": true}'
```

Demo addresses `1` to `4 demo street, example city` map to fixed scenarios (clean, small balance, arrears plus meter hold plus deposit, no balance data). Any other address gets a stable pseudo-random scenario.

Without `consent: true` the API returns 403; without `address` it returns 400. `GET /v1/checks/<id>` returns a stored result. A request body that is not a JSON object returns 400. The full contract is in [`openapi.yaml`](openapi.yaml); a test keeps it in sync with the routes and flag codes.

## Layout

```
app.py                 Flask routes
udshield/models.py     records, flags, result
udshield/engine.py     rules
udshield/providers.py  provider interface and the mock source
tests/                 44 tests: rules, boundaries, API, OpenAPI sync
openapi.yaml           API contract
.github/workflows/     CI (pytest on Python 3.11 and 3.12)
```

## Next steps if this were taken further

1. A real provider adapter behind the `Provider` interface, built on whichever aggregator exposes the fields needed, plus a consent flow for the account holder.
2. Retention rules: results are kept in memory only here; a real service would need an explicit policy for this data.
3. Validation against real activation outcomes, not just hand-written rules.
