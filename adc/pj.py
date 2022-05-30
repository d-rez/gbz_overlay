"""ADC Plugin for retropie-status-overlay
github.com/bverc/retropie-status-overlay

ADC module for PiSupply PiJuice

Author: bverc

I2C must be enabled via raspi-config

Requires python module pijuice.py
Copy from https://github.com/PiSupply/PiJuice/tree/master/Software/Source
or apt-get install pijuice-base
"""

# Import pijuice module
from pijuice import PiJuice

try:
    pijuice = PiJuice(1, 0x14) # Instantiate PiJuice interface object
except FileNotFoundError:
    pass

def read(channel): # pylint: disable=unused-argument
    """Read from ADC and return voltage."""
    voltage = pijuice.status.GetBatteryVoltage()
    return voltage['data'] / 1000
