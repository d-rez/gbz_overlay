"""Unit tests for wifi.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
import os

from devices import wifi

class TestWifi(unittest.TestCase):
    """A Class used to test wifi module."""

    def test_add_icons(self):
        """Setup empty dictionary and dummy icon_path and size, call function,
        then check dictionary length and content are correct"""
        icons = {}
        icon_size = "48"
        icon_path = "random_dir/"
        wifi.add_icons(icons, icon_path, icon_size)
        self.assertTrue(len(icons.keys()) == 6)
        self.assertTrue(icons['wifi_4'] == "random_dir/ic_signal_wifi_4_bar_black_48dp.png")
        self.assertTrue(icons['wifi_3'] == "random_dir/ic_signal_wifi_3_bar_black_48dp.png")
        self.assertTrue(icons['wifi_2'] == "random_dir/ic_signal_wifi_2_bar_black_48dp.png")
        self.assertTrue(icons['wifi_1'] == "random_dir/ic_signal_wifi_1_bar_black_48dp.png")
        self.assertTrue(icons['wifi_0'] == "random_dir/ic_signal_wifi_0_bar_black_48dp.png")
        self.assertTrue(icons['wifi_off'] == "random_dir/ic_signal_wifi_off_black_48dp.png")

    def test_get_state_off(self):
        """Test wifi.get_state() with CARRIER and LINKMODE 0, check state is 'wifi_off'"""
        cwd = os.getcwd()
        wifi.WIFI_CARRIER = cwd + "/test/dir2/file0"
        wifi.WIFI_LINKMODE = cwd + "/test/dir2/file0"
        (wifi_state, wifi_quality) = wifi.get_state()
        self.assertTrue(wifi_state == "wifi_off")
        self.assertTrue(wifi_quality == 0)

    def test_get_state_unconnected(self):
        """Test wifi.get_state() with CARRIER 0 and LINKMODE 1, check state is 'wifi_0'"""
        cwd = os.getcwd()
        wifi.WIFI_CARRIER = cwd + "/test/dir2/file0"
        wifi.WIFI_LINKMODE = cwd + "/test/dir2/file1"
        (wifi_state, wifi_quality) = wifi.get_state()
        self.assertTrue(wifi_state == "wifi_0")
        self.assertTrue(wifi_quality == 0)

    def test_get_state_connected(self):
        """Test wifi.get_state() with CARRIER 1, check state is 'wifi_1/2/3/4'"""
        # This will cause subprocess to call iwconfig, which could return anything
        cwd = os.getcwd()
        wifi.WIFI_CARRIER = cwd + "/test/dir2/file1"
        (wifi_state, wifi_quality) = wifi.get_state()
        self.assertTrue(wifi_state in ("wifi_0", "wifi_1", "wifi_2", "wifi_3", "wifi_4"))
        self.assertTrue(0 <= wifi_quality <= 100)

if __name__ == '__main__':
    unittest.main()
