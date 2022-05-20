# Battery device for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# Authors: bverc, d-rez

import importlib
from statistics import median
from collections import deque

bat_icons = {"discharging": ["alert_red", "alert", "20", "30", "30", "50", "60",
                             "60", "80", "90", "full", "full"],
             "charging"   : ["charging_20", "charging_20", "charging_20",
                             "charging_30", "charging_30", "charging_50",
                             "charging_60", "charging_60", "charging_80",
                             "charging_90", "charging_full", "charging_full"]}

def add_icons(icons, iconpath):
    icons['battery_critical_shutdown'] = iconpath + "battery-alert_120.png"

def translate_bat(voltage, vmax, vmin):
    # determine if charging or discharging
    state = 'discharging' if voltage <= vmax['discharging'] else 'charging'

    # Figure out how 'wide' each range is
    voltage_span = vmax[state] - vmin[state]
    state_span = len(bat_icons[state]) - 1

    # Convert the voltage into a 0-1 range (float)
    value_scaled = max(float(voltage - vmin[state]) / float(voltage_span), 0)

    # Convert the scaled value into the correct state
    return bat_icons[state][int(round(value_scaled * state_span))]

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

    def get_state(self):
        value_v = self.adc.read(self.adc_channel) * self.adc_gain

        self.battery_history.append(value_v)
        median_v = median(self.battery_history)
        try:
            battery_state = translate_bat(median_v, self.vmax, self.vmin)
        except IndexError:
            battery_state = "alert_red"

        return (battery_state, median_v)
