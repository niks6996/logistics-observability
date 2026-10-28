"""Dependency-free, synthetic logistics API. No real customer data."""
import json
import os
import threading
import time
import uuid
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

LOCK = threading.Lock()
COUNTS = Counter()
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)
LATENCIES = Counter()
TOTAL_SECONDS = 0.0
TOTAL_REQUESTS = 0

def metrics():
    with LOCK:
        lines = ['# HELP logistics_requests_total API requests by route and status.',
                 '# TYPE logistics_requests_total counter']
        for (route, status), value in sorted(COUNTS.items()):
            lines.append(f'logistics_requests_total{{route="{route}",status="{status}"}} {value}')
        lines += ['# HELP logistics_request_duration_seconds API request duration.',
                  '# TYPE logistics_request_duration_seconds histogram']
        for bound in BUCKETS:
            lines.append(f'logistics_request_duration_seconds_bucket{{le="{bound}"}} {LATENCIES[bound]}')
        lines += [f'logistics_request_duration_seconds_bucket{{le="+Inf"}} {TOTAL_REQUESTS}',
                  f'logistics_request_duration_seconds_sum {TOTAL_SECONDS}',
                  f'logistics_request_duration_seconds_count {TOTAL_REQUESTS}']
    return '\n'.join(lines) + '\n'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        global TOTAL_SECONDS, TOTAL_REQUESTS
        start = time.monotonic()
        path = urlparse(self.path).path
        request_id = str(uuid.uuid4())
        if path == '/metrics':
            payload = metrics().encode()
            status, content_type = 200, 'text/plain; version=0.0.4; charset=utf-8'
            route = '/metrics'
        else:
            content_type = 'application/json'
            status = 200
            if path in ('/healthz', '/readyz'):
                route, body = path, {'status': 'ok'}
            elif path.startswith('/deliveries/') and len(path.split('/')) == 3:
                route = '/deliveries/:id'
                body = {'delivery_id': path.split('/')[-1], 'status': 'in_transit', 'synthetic': True}
            elif path in ('/simulate/error', '/simulate/slow') and os.getenv('ENABLE_SIMULATION') == 'true':
                route = path
                if path.endswith('error'):
                    status, body = 500, {'error': 'simulated_failure'}
                else:
                    time.sleep(0.75)
                    body = {'status': 'simulated_slow_response'}
            else:
                status, route, body = 404, '/unknown', {'error': 'not_found'}
            payload = json.dumps({**body, 'request_id': request_id}).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('X-Request-ID', request_id)
        self.end_headers()
        self.wfile.write(payload)
        duration = time.monotonic() - start
        # Probes and scrapes are excluded from business traffic measurements.
        if route not in ('/healthz', '/readyz', '/metrics'):
            with LOCK:
                COUNTS[(route, str(status))] += 1
                TOTAL_REQUESTS += 1
                TOTAL_SECONDS += duration
                for bound in BUCKETS:
                    if duration <= bound:
                        LATENCIES[bound] += 1
            print(json.dumps({'timestamp': time.time(), 'service': 'logistics-api',
                'request_id': request_id, 'route': route, 'status': status,
                'duration_seconds': duration}), flush=True)

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.getenv('PORT', '8080'))), Handler).serve_forever()
