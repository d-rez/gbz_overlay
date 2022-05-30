"""Unit tests for devices/bluetooth.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
import os

from devices import bluetooth

class TestBluetooth(unittest.TestCase):
    """A Class used to test devices.bluetooth module."""

    def test_add_icons(self):
        """Setup empty dictionary and dummy icon_path and size, call function,
        then check dictionary length and content are correct"""
        icons = {}
        icon_size = "48"
        icon_path = "random_dir/"
        bluetooth.add_icons(icons, icon_path, icon_size)
        self.assertTrue(len(icons.keys()) == 3)
        self.assertTrue(icons['bt_enabled'] == "random_dir/ic_bluetooth_black_48dp.png")
        self.assertTrue(icons['bt_connected'] == "random_dir/ic_bluetooth_connected_black_48dp.png")
        self.assertTrue(icons['bt_disabled'] == "random_dir/ic_bluetooth_disabled_black_48dp.png")

    def test_get_state_connected(self):
        """Test bluetooth.get_state() with a directory with at least one file"""
        cwd = os.getcwd()
        bluetooth.BT_DEVICES_DIR = cwd + "/test/dir2"
        bt_state = bluetooth.get_state()
        self.assertTrue(bt_state == "bt_connected")

    def test_get_state_disconnected(self):
        """Test bluetooth.get_state() with an empty directory"""
        # This will cause subprocess to call hciconfig, which could return anything
        cwd = os.getcwd()
        bluetooth.BT_DEVICES_DIR = cwd + "/test/dir0"
        bt_state = bluetooth.get_state()
        self.assertTrue(bt_state in ("bt_enabled", "bt_disabled"))

if __name__ == '__main__':
    unittest.main()
