# Release monitoring checklist

Define production baselines and alert thresholds before deployment. Record
service, query/filter, dashboard link, owner, and escalation contact.

## Signals

- [ ] HTTP 500/502/503/504 count and rate by Website/API route.
- [ ] Unexpected 404 rate, especially `/blogs/*` and static assets.
- [ ] CSRF 400 rate by form/route without logging tokens.
- [ ] PostgreSQL availability, active/idle connections, saturation, locks,
  deadlocks, long transactions, storage, and replication/backup health.
- [ ] Website/API CPU and memory, restarts, OOM events, and instance health.
- [ ] p50/p95/p99 response time and request volume by endpoint.
- [ ] Deployment, migration, and application logs with secret redaction.
- [ ] Cloudinary upload failures, timeouts, invalid responses, and folder usage.
- [ ] Comment/reply/report/moderation mutation failure rates.
- [ ] Payload validation failures and any unexpected 5xx after invalid input.
- [ ] Authentication failures, authorization denials, and service-token mismatch.
- [ ] Blog counters/analytics anomalies and queue backlog.

## Observation windows

- First 15 minutes: continuous operator watch.
- First 2 hours: review every 15 minutes.
- First 24 hours: hourly/business-approved review and incident readiness.
- After 24 hours: hand over to normal monitoring only after acceptance.

## Success and abort

Success requires stable health, no unexplained error spike, no data-integrity
alarm, bounded resources, acceptable latency, successful controlled mutations,
and zero secret exposure. Any security/data-integrity issue is an immediate
abort; sustained error or latency breach triggers the rollback checklist.
