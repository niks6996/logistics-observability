#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# This script installs into the CURRENT kubectl context. Use a disposable lab.
kubectl config current-context
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
# Optional explicit chart versions. Capture actual versions in evidence after deployment.
args=(); [[ -z "${PROMETHEUS_CHART_VERSION:-92.14.1}" ]] || args+=(--version "$PROMETHEUS_CHART_VERSION")
helm upgrade --install obs prometheus-community/kube-prometheus-stack -n monitoring --create-namespace -f monitoring/prometheus-values.yaml "${args[@]}" --wait --timeout 10m
args=(); [[ -z "${LOKI_CHART_VERSION:-7.5.0}" ]] || args+=(--version "$LOKI_CHART_VERSION")
helm upgrade --install loki grafana/loki -n monitoring -f monitoring/loki-values.yaml "${args[@]}" --wait --timeout 10m
args=(); [[ -z "${ALLOY_CHART_VERSION:-1.14.4}" ]] || args+=(--version "$ALLOY_CHART_VERSION")
helm upgrade --install alloy grafana/alloy -n monitoring -f monitoring/alloy-values.yaml "${args[@]}" --wait --timeout 5m
kubectl apply -f k8s/app.yaml
kubectl apply -f monitoring/resources.yaml
kubectl create configmap logistics-dashboard -n monitoring --from-file=logistics.json=monitoring/dashboard.json --dry-run=client -o yaml | kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl apply -f -
kubectl rollout status deployment/logistics-api -n logistics --timeout=180s
mkdir -p evidence
helm list -n monitoring -o json > evidence/chart-versions.json
