"""Battery device for retropie-status-overlay
github.com/bverc/retropie-status-overlay

Authors: bverc, d-rez
"""

import importlib
from statistics import median
from collections import deque

BAT_STATES = {"discharging": ["alert_red", "alert", "20", "30", "30", "50", "60",
                             "60", "80", "90", "full", "full"],
             "charging"   : ["charging_20", "charging_20", "charging_20",
                             "charging_30", "charging_30", "charging_50",
                             "charging_60", "charging_60", "charging_80",
                             "charging_90", "charging_full", "charging_full"]}

def add_icons(icons, iconpath, size):
    """Add battery specific icons."""
    for state in (BAT_STATES["discharging"] + BAT_STATES["charging"]):
        icons[state] = iconpath + "ic_battery_" + state + "_black_" + size + "dp.png"
    icons["alert_red"] = iconpath + "battery-alert_" + size + ".png"
    icons['battery_critical_shutdown'] = iconpath + "battery-alert_120.png"

class Battery:
    """A Class to represent a battery and ADC device."""

    NAME = "BatteryADC"

    def __init__(self, config):
        """Initialise battery object using config file for battery and ADC specifications."""
        self.adc = importlib.import_module('adc.' + config.get("Detection", "ADCType").lower())

        self.vmax = {"discharging": config.getfloat("Detection", "VMaxDischarging"),
                     "charging"   : config.getfloat("Detection", "VMaxCharging")}
        self.vmin = {"discharging": config.getfloat("Detection", "VMinDischarging"),
                     "charging"   : config.getfloat("Detection", "VMinCharging")}

        self.battery_history = deque(maxlen=5)
        self.adc_channel = config.getint("Detection", "ADCChannel")
        self.adc_gain = config.getfloat("Detection", "ADCGain")

    def translate(self, voltage):
        """Get correct battery state given battery voltage."""
        # determine if charging or discharging
        state = 'discharging' if voltage <= self.vmax['discharging'] else 'charging'

        # Figure out how 'wide' each range is
        voltage_span = self.vmax[state] - self.vmin[state]
        state_span = len(BAT_STATES[state]) - 1

        # Convert the voltage into a 0-1 range (float)
        value_scaled = max(float(voltage - self.vmin[state]) / float(voltage_span), 0)

        # Convert the scaled value into the correct state
        return BAT_STATES[state][int(round(value_scaled * state_span))]

    def get_state(self):
        """Get state of battery device."""
        value_v = self.adc.read(self.adc_channel) * self.adc_gain

        self.battery_history.append(value_v)
        median_v = median(self.battery_history)
        try:
            battery_state = self.translate(median_v)
        except IndexError:
            battery_state = "alert_red"

        return (battery_state, median_v)
