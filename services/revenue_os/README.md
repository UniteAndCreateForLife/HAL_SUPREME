# HAL Revenue OS

Revenue OS is a zero-spend, evidence-bound projection for HAL's paid-work pipeline.

It deliberately does **not** become a new source of truth:
- HAL WorkGraph remains authoritative for durable tasks, leases, attempts and checkpoints.
- HAL provider mesh / compute router remains authoritative for provider admission, capability routing, credentials and zero-spend readiness.
- Revenue OS scores opportunities, validates evidence gates, records money-state truth and ranks already-admitted worker routes.
- External submissions, identity/tax declarations, payout changes and spending remain explicit human gates.

## Financial truth

`advertised != submitted != merged != accepted != awarded != paid`

A paid state requires a payment receipt.

## Validation

```bash
python -m unittest discover -s tests -p "test_revenue_os.py" -v
python -m compileall -q services/revenue_os tests/test_revenue_os.py
```
