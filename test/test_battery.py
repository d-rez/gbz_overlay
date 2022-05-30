"""Unit tests for battery.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest

from devices import battery

class TestBattery(unittest.TestCase):
    """A Class used to test battery module."""

    def test_add_icons(self):
        """Setup empty dictionary and dummy icon_path, call function,
        then check dictionary length and content are correct"""
        icons = {}
        icon_path = "random_dir/"
        battery.add_icons(icons, icon_path)
        self.assertTrue(len(icons.keys()) == 1)
        self.assertTrue(icons['battery_critical_shutdown'] == "random_dir/battery-alert_120.png")

if __name__ == '__main__':
    unittest.main()
