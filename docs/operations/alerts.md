# Alerts and rollback runbook

This page is the operator contract for a Prometheus installation. The queries
assume the labels emitted by `morel_requests_total` and
`morel_request_duration_seconds`; adjust the window and thresholds to the
traffic profile of the deployment before enabling paging.

## Recommended alerts

```yaml
groups:
  - name: morel-serving
    rules:
      - alert: MorelReadinessFailure
        expr: max by (instance) (morel_requests_total{endpoint="/health/ready",status=~"5.."}) > 0
        for: 5m
        labels:
          severity: page
        annotations:
          summary: morel is failing readiness checks
          runbook: https://sachncs.github.io/morel/operations/alerts/

      - alert: MorelServerErrorRate
        expr: |
          sum by (instance) (rate(morel_requests_total{status=~"5.."}[5m]))
          /
          clamp_min(sum by (instance) (rate(morel_requests_total[5m])), 1e-6)
          > 0.02
        for: 10m
        labels:
          severity: page
        annotations:
          summary: morel 5xx rate is above 2 percent
          runbook: https://sachncs.github.io/morel/operations/alerts/

      - alert: MorelRequestLatencyHigh
        expr: |
          histogram_quantile(0.95,
            sum by (instance, le) (
              rate(morel_request_duration_seconds_bucket[10m])
            )
          ) > 30
        for: 10m
        labels:
          severity: ticket
        annotations:
          summary: morel request p95 exceeds the default smoke budget
          runbook: https://sachncs.github.io/morel/operations/alerts/
```

The readiness expression is intentionally a starting point: a counter-only
query does not prove the *current* state of a pod. Pair it with the platform's
probe result or replace it with a recording rule that exports the latest
readiness gauge. Always scrape every worker, or aggregate metrics at the
process boundary, as described in [observability](observability.md).

## Triage

1. Check `/health` and `/health/ready` on the affected instance.
2. Inspect structured logs by `request_id`, `failure_kind`, and `retryable`.
3. Compare the 5xx and latency alerts with model-loader, updater, and worker
   restart events.
4. If readiness is failing after a model/configuration change, stop rollout and
   keep the last known-good bundle serving.
5. Do not retry programmer failures blindly; they are non-retryable 500s.

## Rollback procedure

The safe rollback unit is the immutable model run directory, not an in-place
checkpoint edit.

```bash
# 1. Record the incident and identify the last known-good run.
MOREL_ENV=production morel serve --model-dir runs/<known-good-run> --help

# 2. Validate the bundle before opening the listener.
MOREL_ENV=production morel serve --model-dir runs/<known-good-run> \
  --host 127.0.0.1 --port 18116 --workers 2

# 3. From another terminal, verify liveness, readiness, and an authenticated
#    recommendation before shifting traffic.
curl -fsS http://127.0.0.1:18116/health
curl -fsS http://127.0.0.1:18116/health/ready
curl -fsS -H "Authorization: Bearer $MOREL_AUTH_TOKEN_READ" \
  -H 'content-type: application/json' \
  -d '{"user":0,"top":3}' \
  http://127.0.0.1:18116/v1/recommend

# 4. Run the repository's lifecycle and model-backed smoke gates.
make serve-workers-smoke
make serve-model-smoke MOREL_MODEL_SMOKE_DIR=runs/<known-good-run>
```

The commands above are a repeatable procedure, not proof that an external
deployment has completed a rollback. Record the environment, bundle hash,
probe results, and alert recovery time for each real drill.

## Alert recovery evidence

For each deployment environment, retain:

- the Prometheus rule revision and scrape target list;
- the model bundle/configuration hash before and after rollback;
- readiness, recommendation, and error-rate probe output;
- time to page, mitigate, and return to the previous SLO;
- any follow-up issue for an alert that was noisy, late, or missing.
