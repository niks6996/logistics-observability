# Lab incident runbooks

## High error rate
Trigger: run `python scripts/traffic.py --mode error --seconds 180`.
Check the error ratio in Grafana. Query Loki with `{app="logistics-api"} | json | status = 500`.
Inspect the route and request ID, then correlate it with the response header.
Recovery: stop fault traffic and run normal traffic for 180 seconds. Verify the alert resolves.
In a real service, investigate recent releases, dependencies and failed requests before choosing remediation.

## High latency
Trigger: run `python scripts/traffic.py --mode slow --seconds 180`.
Check p95 latency, request volume and CPU/memory panels. Search logs for `/simulate/slow`.
Recovery: return to normal traffic and wait for the two-minute rate window and pending period to clear.
The lab deliberately sleeps in the handler. This is not evidence of a real database bottleneck.

## Unavailable
Trigger: scale the logistics Deployment to zero in the disposable lab.
Inspect replicas, pod events, readiness and Prometheus targets.
Recovery: restore two replicas and wait for readiness and successful scrapes.
This alert detects missing or failed scrape targets, which can also indicate monitoring or network failures.

## Failed observability installation
Inspect `helm list -n monitoring`, pod events and logs. Pending pods often indicate insufficient memory.
Compare the installed chart versions with the last successful evidence artifact. Re-run with explicit chart version environment variables after confirming compatibility.
Never record a failed or unexecuted check as successful evidence.
