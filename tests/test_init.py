"""Tests for Fitatu integration."""
import unittest


class TestInit(unittest.TestCase):
    def test_import(self):
        import custom_components.fitatu
        self.assertIsNotNone(custom_components.fitatu)
