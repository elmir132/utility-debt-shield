# Utility Debt Shield (prototype)

A small API that answers one question for a rental platform before a lease is signed: **could the new tenant run into trouble turning the utilities on at this address?** It flags unpaid balances, meter holds and deposit requirements, and says how serious the friction is.

This started as my idea in the Cornell Tech Product Studio (Team 419, fall 2026) and was developed further for the NBAY 6080 business plan. This repository is a **prototype of the check itself**. It is not a product.

## What it is not

- **No real utility data.** The only data source is a mock that returns fictional, deterministic records (`udshield/providers.py`). Every name and figure is invented. No utility company or data aggregator is integrated.
- **Not a debt claim.** Utility debt generally follows the *account holder*, not the address, so a new tenant does not simply inherit a previous tenant's balance. What a balance, shut-off or meter hold can cause is *activation friction*: deposits, disputes, a technician visit, delay. The output wording reflects that, and a high-friction result says explicitly that it does not by itself mean the renter owes anything.
- **Consent is required.** Reading utility account data through aggregators needs the account holder's consent, so the API refuses a check unless the request carries `"consent": true`.
- **Data availability is the real risk.** Aggregators differ in what they expose; some bill APIs return no balance or past-due field at all. The engine treats a missing field as *unknown*, never as *clean*.

## How it works

```
POST /v1/checks  {address, consent}  ->  provider.fetch(address)  ->  rules engine  ->  result
```

Rules (`udshield/engine.py`, deterministic, all thresholds are constants at the top of the file):

| Signal | Friction |
|---|---|
| Balance under $50 | low |
| Balance $50 to $300 | medium |
| Balance $300 or more, or any balance 60+ days past due | high |
| Meter hold | high |
| Deposit required | medium |
| Balance not reported by the source | info; overall result `unknown` if nothing else is known |

The overall result is the worst flag across all utilities.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py        # http://localhost:5000  (PORT=5058 python app.py to change)
pytest -q
```

```bash
curl -X POST localhost:5000/v1/checks \
  -H 'content-type: application/json' \
  -d '{"address": "3 demo street, example city", "consent": true}'
```

Demo addresses `1` to `4 demo street, example city` map to fixed scenarios (clean, small balance, arrears plus meter hold plus deposit, no balance data). Any other address gets a stable pseudo-random scenario.

Without `consent: true` the API returns 403; without `address` it returns 400. `GET /v1/checks/<id>` returns a stored result.

## Layout

```
app.py                 Flask routes
udshield/models.py     records, flags, result
udshield/engine.py     rules
udshield/providers.py  provider interface and the mock source
tests/                 19 tests
```

## Next steps if this were taken further

1. A real provider adapter behind the `Provider` interface, built on whichever aggregator exposes the fields needed, plus a consent flow for the account holder.
2. Retention rules: results are kept in memory only here; a real service would need an explicit policy for this data.
3. Validation against real activation outcomes, not just hand-written rules.
