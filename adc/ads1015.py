# ADC Plugin for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# ADC module for Texas Instruments ADS1015 12-bit ADC
# Also available as Adafruit breakout board
#
# Authors: bverc, d-rez
#
# Requires ADS1015 connected via I2C, and reading on channel 0
#
# I2C must be enabled via raspi-config


# Import necessary ADC library
import Adafruit_ADS1x15

# Setup ADC
adc = Adafruit_ADS1x15.ADS1015()

# ADC read function, return voltage
def read(channel):
    value = adc.read_adc(channel, gain=2/3) # Channel 0, 2/3 gain
    value_v = value * 0.003 #1 bit = 3mV
    return value_v
