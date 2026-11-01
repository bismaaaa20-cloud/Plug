import unittest
from plug.providers.base import ProviderRequest, ProviderResponse

class ProviderModelTests(unittest.TestCase):
    def test_request_rejects_nan_temperature(self):
        with self.assertRaises(ValueError):
            ProviderRequest("hello", temperature=float("nan"))
    def test_response_rejects_negative_tokens(self):
        with self.assertRaises(ValueError):
            ProviderResponse("fake", "ok", input_tokens=-1)
    def test_response_rejects_infinite_latency(self):
        with self.assertRaises(ValueError):
            ProviderResponse("fake", "ok", latency_ms=float("inf"))
