# Battery Detection Modules

In order to display a battery level indicator, a method of reading the battery voltage is required.

Plugins in the `/adc` directory can be used to read from various ADC modules or ICs. The plugin will return  a voltage to the main script which will convert it to a battery percentage based on values in the config file.

## Config File

The default values in the config file likely won't match your hardware setup, so need to be configured.

```
# Enable Battery Voltage Monitoring Via ADC
BatteryADC = False
```
Set `BatteryADC = True` if you have a supported ADC module

```
# Which chip are you using for ADC (Only applies if BatteryADC=True)
# MCP3008
# ADS1015
# PJ (PiJuice or PiJuice Zero)
ADCType = PJ
```
Set `ADCType` to one of the above options or another name if you have a custom plugin

```
# Gain for ADC Voltage. Adjust if dividing voltage before ADC input
ADCGain = 1.0
```
Set `ADCGain` to be the inverse of any voltage dividing done before entering your ADC. For example, if you use a 100K/100K voltage divider between your battery and your ADC, then you should set `ADCGain = 2.0` to return the read voltage back to the actual battery voltage.

```
# ADC Channel for ADCs which have multiple channels
ADCChannel = 0
```
For ADC plugins that support multiple channels, you can set this using `ADCChannel` 

```
# Change how your battery calculations are made, See Read Me
VMaxDischarging = 4
VMaxCharging = 4.5
VMinDischarging = 3.2
VMinCharging = 4.25
```
The above four values set the outer limits of the sensed voltages to determine charge Level. You should set each value based on the read battery voltage in each state to the the most accurate battery level. Using the console log can help determine these values.

`VMaxDischarging` is the highest voltage on the battery when fully charged, but power is removed.  
`VMaxCharging` is the highest voltage on the battery when fully charged, and power remains.  
`VMinDischarging` is the lowest voltage on the battery when discharging before it dies or can no longer power your hardware. Usually 3.2 V for LiPo batteries.  
`VMinCharging` is the lowest voltage on the battery when charging. This will be the voltage when power is restored when the battery has the lowest charge.

```
# Should low ADC cause shutdown
ADCShutdown = False
```
Set `ADCShutdown = True` if you want the device to shutdown safely when voltage drops below `VMinDischarging`. Shutdown will be restored if voltage exceeds `VMinCharging` within 60 seconds.

## Custom Plugin Module

If you have an ADC or battery monitor that is not currently supported, you can easily add your own.

Create a blank file in the `/adc` folder as `[module name].py`

Your module must define a `read()` function which accept one argument (optionally for a channel, which can be ignored). This function should return a voltage value 
*before* the ADCGain adjustment. The ADCGain adjust will be applied in the main script.

Use `ads1015.py` as a simple example to get started.

Once you have it working, submit a Pull Request to get it added to this repository.
