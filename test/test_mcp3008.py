"""Unit tests for adc/mcp3008.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
from unittest.mock import Mock

from adc import mcp3008

mcp3008.adc = Mock()

def mock_read_adc(channel):
    """A function to mock MCP3008().read_adc()"""
    if channel == 0:
        return 0
    if channel == 1:
        return 256
    if channel == 2:
        return 512
    return 1024

class TestMCP3008(unittest.TestCase):
    """A Class used to test MCP3008 module."""

    def test_read(self):
        """Test mcp3008.read()"""
        mcp3008.adc.read_adc.side_effect = mock_read_adc
        self.assertTrue(mcp3008.read(0) == 0)
        self.assertTrue(mcp3008.read(1) == 0.825)
        self.assertTrue(mcp3008.read(2) == 1.65)
        self.assertTrue(mcp3008.read(3) == 3.3)

if __name__ == '__main__':
    unittest.main()
