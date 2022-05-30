# RetroPie Status Overlay
Based on [gbz_overlay](https://github.com/d-rez/gbz_overlay) script by [d-rez](https://github.com/d-rez)

![Pylint](https://github.com/bverc/retropie-status-overlay/actions/workflows/pylint.yml/badge.svg)
![unittest](https://github.com/bverc/retropie-status-overlay/actions/workflows/unittest.yml/badge.svg)

This repository contains a script to display status icons on top of your RetroPie games and emulationstation menus

![Bluetooth, wifi connected, audio on](_images/240_icons.png)

## Features
- display battery level (Requires appropiate Hardware)
- display WiFi state
- display Bluetooth state
- display Audio state
- display warning if under voltage, frequency-capped or throttling
- gracefully shut down the Pi after 60s from when voltage goes below 3.2V of low voltage detected (abort shutdown when power is restored)
- show a big imminent shutdown warning when the counter starts ticking
- Set icon transparency while in game
- Shutdown from button press
- Custom icon colours

## Battery Level Detection Support
- Low Voltage GPIO
- Texas Instruments ADS1015 (Also available as Adafruit breakout board)
- Microchip MCP3008
- PiJuice HAT / PiJuice Zero
- Simple plugin system to add your own ADC / Battery monitor

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

Run RetroPie Status Overlay
```bash
cd ~
git clone https://github.com/bverc/retropie-status-overlay
cd retropie-status-overlay
bash install.sh
```
Follow the onscreen instructions

retropie-status-overlay will run as a service automatically at boot, and is called "retropie-status-overlay"

You can stop and start this service by running:
```bash
sudo service retropie-status-overlay stop
sudo service retropie-status-overlay start
```
# Manual Install Instructions

SSH into your device, or access the terminal using F4.

## Install pngview by AndrewFromMelbourne
```bash
mkdir ~/src
cd ~/src
git clone https://github.com/bverc/raspidmx
cd raspidmx/lib
make
cd ../pngview
make
sudo cp pngview /usr/local/bin/
 ```
  Note: AndrewFromMelbourne/raspidmx has been replaced with bverc/raspidmx due to added features required by retropie-status-overlay. Will be changed back pending [pull request](https://github.com/AndrewFromMelbourne/raspidmx/pull/31).
  
## Run RetroPie Status Overlay
Install psutil module:
```bash
sudo apt-get install python3-psutil
```
Download the code:
```bash
cd ~/src
git clone https://github.com/bverc/retropie-status-overlay
cd retropie-status-overlay
cp config.ini.example config.ini
```

Colorize Icons:
```bash
sudo apt-get install imagemagick
cp -r overlay_icons colored_icons
mogrify -fill "#7d7d7d" -colorize 100 colored_icons/*black*.png
```
Replace `"#7d7d7d"` with preffered color in HEX in quotes or as a word (e.g. `blue`) without quotes

Test the code:
```bash
python3 overlay.py
```
You should see the overlay added to your interface

Now to get it to  run at boot:
```bash
sudo crontab -e
```
At the bottom of the file, add the line:
```
@reboot python3 /home/pi/src/retropie-status-overlay/overlay.py
```
reboot

## (Optional) Script to Toggle Status Overlay in retropiemenu
Copy shell script to retropiemenu:
```bash
cd ~/src
cp retropie-status-overlay/toggle\ status\ overlay.sh ~/RetroPie/retropiemenu/
```

Make script executable:
```bash
cd ~/RetroPie/retropiemenu
chmod +x toggle\ status\ overlay.sh
```

You can now toggle the overlay on and off from the RetroPie menu.
