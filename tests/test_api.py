import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from app.server import Handler

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
    def get(self, path):
        try:
            return urllib.request.urlopen(self.url + path)
        except urllib.error.HTTPError as error:
            return error
    def test_delivery_and_correlation(self):
        response = self.get('/deliveries/demo-1')
        body = json.load(response)
        self.assertEqual(body['status'], 'in_transit')
        self.assertEqual(body['request_id'], response.headers['X-Request-ID'])
    def test_probes(self):
        for path in ('/healthz', '/readyz'):
            self.assertEqual(self.get(path).status, 200)
    def test_simulation_disabled_by_default(self):
        os.environ.pop('ENABLE_SIMULATION', None)
        self.assertEqual(self.get('/simulate/error').status, 404)
    def test_fault_metrics_and_cardinality(self):
        os.environ['ENABLE_SIMULATION'] = 'true'
        try:
            self.assertEqual(self.get('/simulate/error').status, 500)
            self.assertEqual(self.get('/simulate/slow').status, 200)
            self.get('/deliveries/unique-customer-value')
            output = self.get('/metrics').read().decode()
            self.assertIn('logistics_requests_total{route="/simulate/error",status="500"}', output)
            self.assertIn('logistics_request_duration_seconds_bucket{le="+Inf"}', output)
            self.assertNotIn('unique-customer-value', output)
        finally:
            os.environ.pop('ENABLE_SIMULATION', None)

if __name__ == '__main__':
    unittest.main()
