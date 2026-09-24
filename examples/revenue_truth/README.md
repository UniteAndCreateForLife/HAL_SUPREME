# Revenue Truth Projection

This example turns opportunity records into an evidence-bound revenue pipeline.
It is designed for bounty, contract, grant, and sponsor workflows where a draft,
submission, acceptance, award, and payment are materially different events.

The projection is derived. It does not submit applications, spend money, change
payout settings, store identity data, or become the canonical work ledger.

## Stages

1. discovered
2. qualified
3. prepared
4. submitted
5. accepted for review
6. merged or delivery accepted
7. sponsor or client accepted
8. awarded
9. payout initiated
10. funds available
11. paid and reconciled

## Run the focused tests

```bash
python -m unittest -v examples.revenue_truth.test_revenue_projection
```

The tests exercise the failure modes that matter to revenue reporting:

- an explicitly unsubmitted packet stays prepared;
- a claim is submitted without implying sponsor acceptance;
- a merge does not imply an award or payment;
- paid status requires verified cash evidence;
- advertised value remains separate from verified paid value; and
- a funded or paid bounty pool does not prove recipient payment.
