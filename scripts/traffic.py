"""Run locally against a port-forward. Faults only affect this synthetic lab."""
import argparse
import time
import urllib.request
import urllib.error
p = argparse.ArgumentParser()
p.add_argument('--url', default='http://127.0.0.1:8080')
p.add_argument('--mode', choices=['normal', 'error', 'slow'], default='normal')
p.add_argument('--seconds', type=int, default=180)
a = p.parse_args()
path = {'normal': '/deliveries/demo-1', 'error': '/simulate/error', 'slow': '/simulate/slow'}[a.mode]
end = time.monotonic() + a.seconds
counts = {}
while time.monotonic() < end:
    try:
        with urllib.request.urlopen(a.url + path, timeout=5) as r:
            code = str(r.status)
    except urllib.error.HTTPError as e:
        code = str(e.code)
    except OSError:
        code = 'connection_error'
    counts[code] = counts.get(code, 0) + 1
    time.sleep(0.1)
print(counts)

expected = '500' if a.mode == 'error' else '200'
if counts.get(expected, 0) == 0 or any(code != expected for code in counts):
    raise SystemExit('Traffic verification failed: unexpected status or connection error')
