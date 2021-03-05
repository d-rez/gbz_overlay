

# RetroPie Status Overlay
Based on [gbz_overlay](https://github.com/d-rez/gbz_overlay) script by [d-rez](https://github.com/d-rez)

This repository contains a script to display lovely slightly-transparent overlays on top of your RetroPie games and emulationstation menus

![Bluetooth, wifi connected, audio on](_images/240_icons.png)

## Features
- display battery level (Requires appropiate Hardware, currently supports GPIO Low Voltage, MCP and ADS1 chips)
- display WiFi state (connected/disconnected/disabled)
- display Bluetooth state (connected/disconnected/disabled)
- display under-voltage state
- display warning if frequency-capped
- display warning if throttling
- gracefully shut down the Pi after 60s from when voltage goes below 3.2V of low voltage detected (abort shutdown when power is restored)
- show a big imminent shutdown warning when the counter starts ticking
- Only critical icons displayed in game
- Shutdown from button press
- Custom icon colours

## More Screenshots

![Overlay on TFT theme at 240p](_images/240_allicons.png)  
*Overlay on TFT theme at 240p*

![Overlay on Carbon theme at 1080p](_images/1080_carbon.png)  
*Overlay on Carbon theme at 1080p*

![Overlay on terminal](_images/1080_terminal.png)  
*Overlay on terminal*

![Battery Critical](_images/240_lowbat.png)  
*Battery Critical icon*

# Automatic Install Instructions

SSH into your device, or access the terminal using F4.

## Run RetroPie Status Overlay

    cd ~
    git clone https://github.com/bverc/retropie_status_overlay
    cd retropie_status_overlay
    sudo bash install.sh

## Follow the onscreen instructions

retropie_status_overlay will run as a service automatically at boot, and is called "retropie-status-overlay"

You can stop and start this service by running

    sudo service retropie-status-overlay stop
    sudo service retropie-status-overlay start

# Manual Install Instructions

SSH into your device, or access the terminal using F4.

## Install pngview by AndrewFromMelbourne
    mkdir ~/src
    cd ~/src
    git clone https://github.com/bverc/raspidmx
    cd raspidmx/lib
    make
    cd ../pngview
    make
    sudo cp pngview /usr/local/bin/
  
  Note: AndrewFromMelbourne/raspidmx has been replaced with bverc/raspidmx due to added features required by retropie_status_overlay. Will be changed back pending [pull request](https://github.com/AndrewFromMelbourne/raspidmx/pull/31).
	
## Run RetroPie Status Overlay
Install psutil module:

    sudo apt-get install python3-psutil
Download the code:

    cd ~/src
    git clone https://github.com/bverc/retropie_status_overlay
    cp retropie_status_overlay/config.ini.example retropie_status_overlay/config.ini
Test the code:

    python3 retropie_status_overlay/overlay.py
You should see the overlay added to your interface

Now to get it to  run at boot:

    sudo crontab -e
    
At the bottom of the file, add the line:

    @reboot python3 /home/pi/src/retropie_status_overlay/overlay.py

reboot
