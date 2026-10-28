"""Bounded polling of real Prometheus/Loki APIs, preserving returned evidence."""
import argparse
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
p = argparse.ArgumentParser()
p.add_argument('check', choices=['metrics', 'logs', 'firing', 'resolved', 'latency-firing', 'latency-resolved', 'down-firing', 'down-resolved'])
p.add_argument('--timeout', type=int, default=240)
a = p.parse_args()
alerts={'firing':'LogisticsHighErrorRate','resolved':'LogisticsHighErrorRate','latency-firing':'LogisticsHighLatency','latency-resolved':'LogisticsHighLatency','down-firing':'LogisticsUnavailable','down-resolved':'LogisticsUnavailable'}
if a.check == 'logs':
    url='http://127.0.0.1:3100/loki/api/v1/query_range?'+urllib.parse.urlencode({'query':'{app="logistics-api"} | json','limit':10})
else:
    query = 'sum(logistics_requests_total)' if a.check == 'metrics' else 'ALERTS{alertname="'+alerts[a.check]+'",alertstate="firing"}'
    url='http://127.0.0.1:9090/api/v1/query?'+urllib.parse.urlencode({'query':query})
end=time.monotonic()+a.timeout
while time.monotonic()<end:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            result=json.load(r)
        if result.get('status') != 'success':
            raise ValueError('API did not return success')
        rows=result['data']['result']
        if a.check.endswith('resolved'):
            ok=not rows
        elif a.check=='metrics':
            ok=bool(rows) and float(rows[0]['value'][1])>0
        else:
            ok=bool(rows)
        if ok:
            Path('evidence').mkdir(exist_ok=True)
            Path(f'evidence/{a.check}.json').write_text(json.dumps(result,indent=2))
            print(a.check, 'PASS')
            break
    except (OSError, ValueError, KeyError) as e:
        print(type(e).__name__, str(e))
    time.sleep(10)
else:
    raise SystemExit(f'{a.check} failed or timed out; inspect diagnostic artifacts')
