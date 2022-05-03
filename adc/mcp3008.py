# ADC Plugin for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# ADC module for Microchip MCP3008 12-bit ADC
#
# Authors: bverc, louisvarley
#
# Requires Rasperry Pi with MCP3008 connected via SPI, and reading on channel 0

# Import necessary ADC library
import Adafruit_MCP3008

# Setup ADC
adc_vref = 3.3
spi_clk = 11
spi_cs = 8
spi_miso = 9
spi_mosi = 10

adc = Adafruit_MCP3008.MCP3008(clk=spi_clk, cs=spi_cs, miso=spi_miso, mosi=spi_mosi)

#ADC read function, return voltage
def read(channel):
  value = adc.read_adc(channel)
  value_v = adc_vref * value / 1024
