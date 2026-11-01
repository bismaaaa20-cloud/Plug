import os
import unittest
from unittest.mock import patch
from plug.config.settings import Settings

class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Settings.from_env(), Settings())
    def test_invalid_concurrency_rejected(self):
        with patch.dict(os.environ, {"PLUG_MAX_CONCURRENCY": "0"}):
            with self.assertRaises(ValueError):
                Settings.from_env()
