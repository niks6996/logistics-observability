# Troubleshooting Case Studies

## 1. Loki failed to start

Symptom:
Helm timed out while installing Loki. The Loki container entered
CrashLoopBackOff while Prometheus and Grafana remained healthy.

Investigation:
Collected Kubernetes events, pod descriptions, and current and previous
container logs through GitHub Actions artifacts.

Root cause:
Loki attempted to create /var/loki on a read-only root filesystem.
Persistent storage was disabled, and no writable data volume was mounted.

Fix:
Mounted an emptyDir volume at /var/loki while retaining the protected
root filesystem.

Validation:
The subsequent integration workflow passed, including Loki log queries.

Limitation:
The temporary volume is deleted with the pod. A durable deployment
requires an appropriate storage design.

## 2. Dashboard traffic failed after the outage test

Symptom:
Grafana became healthy, but the metrics verification timed out before
dashboard capture.

Diagnosis:
The outage test removed the original API pods. The existing port-forward
was tied to an original pod and could not serve traffic after replacement.

Fix:
Established a fresh API port-forward on port 18080 after recovery,
checked readiness, and directed dashboard traffic through that connection.

Validation:
The subsequent workflow passed. The captured Grafana dashboard showed
request traffic, error recovery, latency changes, and pod resource usage.
