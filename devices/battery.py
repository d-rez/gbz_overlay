# Battery device for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# Authors: bverc, d-rez

import configparser
import importlib
from statistics import median
from collections import deque

bat_icons = {"discharging": ["alert_red", "alert", "20", "30", "30", "50", "60",
                             "60", "80", "90", "full", "full"],
             "charging"   : ["charging_20", "charging_20", "charging_20",
                             "charging_30", "charging_30", "charging_50",
                             "charging_60", "charging_60", "charging_80",
                             "charging_90", "charging_full", "charging_full"]}

def icons(icons, iconpath, size):
    icons['battery_critical_shutdown'] = iconpath + "battery-alert_120.png"

def translate_bat(voltage, vmax, vmin):
    # Figure out how 'wide' each range is
    state = voltage <= vmax["discharging"] and "discharging" or "charging"

    leftSpan = vmax[state] - vmin[state]
    rightSpan = len(bat_icons[state]) - 1

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(voltage - vmin[state]) / float(leftSpan)
    if valueScaled < 0:
        valueScaled = 0

    # Convert the 0-1 range into a value in the right range.
    return bat_icons[state][int(round(valueScaled * rightSpan))]

class Battery:
    def __init__(self, config):
        self.adc = importlib.import_module('adc.' + config.get("Detection", "ADCType").lower())

        self.vmax = {"discharging": config.getfloat("Detection", "VMaxDischarging"),
                     "charging"   : config.getfloat("Detection", "VMaxCharging")}
        self.vmin = {"discharging": config.getfloat("Detection", "VMinDischarging"),
                     "charging"   : config.getfloat("Detection", "VMinCharging")}

        self.battery_history = deque(maxlen=5)
        self.adc_channel = config.getint("Detection", "ADCChannel")
        self.adc_gain = config.getfloat("Detection", "ADCGain")

    def getstate(self):
        value_v = self.adc.read(self.adc_channel) * self.adc_gain

        self.battery_history.append(value_v)
        median_v = median(self.battery_history)
        try:
            battery_state = translate_bat(median_v, self.vmax, self.vmin)
        except IndexError:
            battery_state = "alert_red"

        return (battery_state, median_v)
