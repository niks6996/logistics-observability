import unittest
from scripts.verify import check_result

def vector(*values):
    return {'data': {'result': [{'value': [0, str(v)]} for v in values]}}

class VerificationTests(unittest.TestCase):
    def test_missing_alert_without_health_is_not_recovery(self):
        self.assertFalse(check_result('resolved', vector()))
        self.assertFalse(check_result('down-resolved', vector(), vector()))
    def test_firing_alert_is_not_recovery(self):
        self.assertFalse(check_result('resolved', vector(1), vector(1)))
    def test_healthy_active_service_without_alert_is_recovered(self):
        self.assertTrue(check_result('down-resolved', vector(), vector(1)))
    def test_empty_log_stream_does_not_prove_ingestion(self):
        self.assertFalse(check_result('logs', {'data': {'result': [{'values': []}]}}))
        self.assertTrue(check_result('logs', {'data': {'result': [{'values': [['1','entry']]}]}}))
    def test_zero_requests_do_not_prove_traffic(self):
        self.assertFalse(check_result('metrics', vector(0)))
        self.assertTrue(check_result('metrics', vector(5)))
