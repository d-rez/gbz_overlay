"""Unit tests for battery.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
import configparser
from unittest.mock import Mock

from devices import battery

def mock_read(channel): # pylint: disable=unused-argument
    """A function to mock adc.read()"""
    return 4.5

class TestBattery(unittest.TestCase):
    """A Class used to test battery module."""

    def test_add_icons(self):
        """Setup empty dictionary and dummy icon_path, call function,
        then check dictionary length and content are correct"""
        icons = {}
        icon_size = "48"
        icon_path = "random_dir/"
        battery.add_icons(icons, icon_path, icon_size)
        self.assertTrue(len(icons.keys()) == 17)
        self.assertTrue(icons['battery_critical_shutdown'] == "random_dir/battery-alert_120.png")
        self.assertTrue(icons['30'] == "random_dir/ic_battery_30_black_48dp.png")
        self.assertTrue(icons['charging_60'] == "random_dir/ic_battery_charging_60_black_48dp.png")
        self.assertTrue(icons['alert_red'] == "random_dir/battery-alert_48.png")

    def test_battery(self):
        """Create Battery object."""
        config = configparser.ConfigParser()
        config['Detection'] = {'ADCType': 'ads1015',
                               'VMaxCharging': '4.5',
                               'VMinCharging': '4.25',
                               'VMaxDischarging': '4',
                               'VMinDischarging': '3.2',
                               'ADCChannel': '0',
                               'ADCGain': '1'}
        bat = battery.Battery(config)
        self.assertTrue(bat.adc_gain == 1)

        bat.adc = Mock()
        bat.adc.read.side_effect = mock_read

        (bat_state, median_v) = bat.get_state()
        self.assertTrue(bat_state == "charging_full")
        self.assertTrue(median_v == 4.5)

if __name__ == '__main__':
    unittest.main()
