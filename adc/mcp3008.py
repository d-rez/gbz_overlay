"""ADC Plugin for retropie-status-overlay
github.com/bverc/retropie-status-overlay

ADC module for Microchip MCP3008 12-bit ADC

Authors: bverc, louisvarley

Requires Rasperry Pi with MCP3008 connected via SPI, and reading on channel 0
"""

# Import necessary ADC library
import Adafruit_MCP3008

# Setup ADC
ADC_VREF = 3.3
SPI_CLK = 11
SPI_CS = 8
SPI_MISO = 9
SPI_MOSI = 10

try:
    adc = Adafruit_MCP3008.MCP3008(clk=SPI_CLK, cs=SPI_CS, miso=SPI_MISO, mosi=SPI_MOSI)
except (TypeError, RuntimeError):
    pass

def read(channel):
    """Read from ADC and return voltage."""
    value = adc.read_adc(channel)
    value_v = ADC_VREF * value / 1024
    return value_v
