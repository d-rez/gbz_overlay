# Gameboy Zero RetroPie status overlays
This repository contains a script to display lovely slightly-transparent overlays on top of your RetroPie games and emulationstation menus

## What can it do?
- display battery level (charging, discharging, %, critical)
- display imminent shutdown warning when battery goes below 3.2V
- gracefully shut down the Pi after 60s from when voltage goes below 3.2V
- display WiFi state (connected/disconnected/disabled)
- display Bluetooth state (connected/disconnected/disabled)
- display under-voltage state
- display warning if frequency-capped
- display warning if throttling

## What do I need to get it running?
- [pngview](https://github.com/AndrewFromMelbourne/raspidmx/tree/master/pngview) from AndrewFromMelbourne
- [material-design-icons](https://github.com/google/material-design-icons/archive/master.zip) from Google
- Adafruit ADS1015 with Vbat on A0 (or alternative)
- a symbolic link to *overlay\_icons/ic\_battery\_alert\_red\_white\_36dp.png* under *material\_design\_icons\_master/device/drawable-mdpi/*
- an entry in crontab to start this on boot
- check and adjust paths in the script header
- some battery readings calibration - check logs
- some patience

## But how does it look like?
Like that:

![Bluetooth, wifi connected, battery discharging](_images/connected.png)
Bluetooth, wifi connected, battery discharging

![Bluetooth, wifi disconnected, battery discharging](_images/disconnected.png)
Bluetooth, wifi disconnected, battery discharging

![Bluetooth, wifi disabled, battery charging](_images/disabled_charging.png)
Bluetooth, wifi disabled, battery charging

![CPU throttled due to high temperature](_images/throttle.png)
CPU throttled due to high temperature

![Under-Voltage, Freq-capped due to high temperature, battery critical, shutdown imminent warning](_images/freqcap_undervolt_criticalbat_shutdown.png)
Under-Voltage, Freq-capped due to high temperature, battery critical, shutdown imminent warning - shutting down in 60s
