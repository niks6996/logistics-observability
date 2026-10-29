"""Query live APIs. Recovery requires healthy scrapes and active request traffic."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request

ALERTS = {
    'firing': 'LogisticsHighErrorRate', 'resolved': 'LogisticsHighErrorRate',
    'latency-firing': 'LogisticsHighLatency', 'latency-resolved': 'LogisticsHighLatency',
    'down-firing': 'LogisticsUnavailable', 'down-resolved': 'LogisticsUnavailable',
}
RECOVERY_QUERY = (
    '(min(up{namespace="logistics",service="logistics-api"}) == 1)'
    ' and (sum(rate(logistics_requests_total[1m])) > 0)'
)

def query(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        result = json.load(response)
    if result.get('status') != 'success':
        raise ValueError('API did not return success')
    return result

def prom_url(base, expression):
    return base + '/api/v1/query?' + urllib.parse.urlencode({'query': expression})

def check_result(check, result, health=None):
    rows = result['data']['result']
    if check.endswith('resolved'):
        # Missing alert series alone does not establish recovery.
        return not rows and health is not None and any(
            float(row['value'][1]) == 1 for row in health['data']['result']
        )
    if check == 'metrics':
        return bool(rows) and float(rows[0]['value'][1]) > 0
    if check == 'logs':
        return any(row.get('values') for row in rows)
    return any(float(row['value'][1]) == 1 for row in rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('check', choices=['metrics', 'logs', *ALERTS])
    parser.add_argument('--timeout', type=float, default=240)
    parser.add_argument('--prometheus-url', default='http://127.0.0.1:9090')
    parser.add_argument('--loki-url', default='http://127.0.0.1:3100')
    args = parser.parse_args()
    if args.check == 'logs':
        url = args.loki_url + '/loki/api/v1/query_range?' + urllib.parse.urlencode({
            'query': '{app="logistics-api"} | json', 'limit': 10
        })
    else:
        expression = 'sum(logistics_requests_total)' if args.check == 'metrics' else (
            'ALERTS{alertname="' + ALERTS[args.check] + '",alertstate="firing"}'
        )
        url = prom_url(args.prometheus_url, expression)
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        try:
            result = query(url)
            health = query(prom_url(args.prometheus_url, RECOVERY_QUERY)) if args.check.endswith('resolved') else None
            if check_result(args.check, result, health):
                output = Path(os.getenv('EVIDENCE_DIR', 'artifacts/runtime'))
                output.mkdir(parents=True, exist_ok=True)
                (output / f'{args.check}.json').write_text(json.dumps(result, indent=2))
                if health is not None:
                    (output / f'{args.check}-health.json').write_text(json.dumps(health, indent=2))
                print(args.check, 'PASS')
                return
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(type(error).__name__, str(error))
        time.sleep(10)
    raise SystemExit(f'{args.check} failed or timed out; inspect this run diagnostics')

if __name__ == '__main__':
    main()
