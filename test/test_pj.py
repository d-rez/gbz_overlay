"""Unit tests for adc/pj.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
from unittest.mock import Mock

from adc import pj

pj.pijuice = Mock()

def mock_get_voltage():
    """A method to mock PiJuice.status.GetBatteryVoltage()"""
    return {"data": 1100}

class TestPJ(unittest.TestCase):
    """A Class used to test PJ module."""

    def test_read(self):
        """Test pj.read()"""
        pj.pijuice.status.GetBatteryVoltage.side_effect = mock_get_voltage
        self.assertTrue(pj.read(0) == 1.1)

if __name__ == '__main__':
    unittest.main()
