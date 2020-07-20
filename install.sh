#!/bin/bash

echo "Starting installation of Retropie Status Overlay"
echo "Press ENTER to proceed or CTRL+C to abort"
echo "--------------------------------------------------"
read -r _

mkdir ~/src
cd ~/src

read -p "Use [D]efault config.ini or [b]uild from scratch? " CONFIG
if [[ $CONFIG = [bB] ]] ; then
  echo ""
  echo "Building config file"
  echo "--------------------------------------------------"
  echo -n "" > config.ini
  echo "# Created using install.sh" >> config.ini
  echo "" >> config.ini

  echo "[Icons]" >> config.ini 
  echo "# Icon Size: 24, 36 or 48" >> config.ini 
  while [[ $PIXEL != "24" && $PIXEL != "36" && $PIXEL != "48" ]]
  do
    echo "Choose icon size. 36px or lower recommened for low res screens."
    read -p "24/36/48 [48]: " PIXEL
    if [[ $PIXEL = "" ]] ; then
      PIXEL="48"
    fi
  done
  echo "Size = $PIXEL" >> config.ini 
  echo "# Icon Color: white or black" >> config.ini
  while [[ "$COLOR" != "white" && "$COLOR" != "black" ]]
  do
    echo "Choose icon color"
    read -p "[b]lack or [w]hite: " COLOR
    if [[ $COLOR = [bB] ]] ; then
      COLOR="black"
    elif [[ $COLOR = [wW] ]] ; then
      COLOR="white"
    fi
  done
  echo "Color = $COLOR" >> config.ini
  echo "#Horizontal Position: left or right" >> config.ini
  while [[ "$XPOS" != "left" && "$XPOS" != "right" ]]
  do
    read -p "Shall icons align [l]eft or [r]ight? " XPOS
    if [[ $XPOS = [lL] ]] ; then
      XPOS="left"
    elif [[ $XPOS = [rR] ]] ; then
      XPOS="right"
    fi
  done
  echo "Horizontal = $XPOS" >> config.ini
  echo "#Vertical Position: top or bottom" >> config.ini
  while [[ "$YPOS" != "top" && "$YPOS" != "bottom" ]]
  do
    read -p "Shall icons align [t]op or [b]ottom? " YPOS
    if [[ $YPOS = [tT] ]] ; then
      YPOS="top"
    elif [[ $YPOS = [bT] ]] ; then
      YPOS="bottom"
    fi
  done
  echo "Vertical = $YPOS" >> config.ini
  echo "# Padding from corner and between icons" >> config.ini
  PAD=51
  while [[ "$PAD" -lt 0 || "$PAD" -gt 50 ]]
  do
    read -p "Icon Padding [0 - 50]: " PAD
  done
  echo "Padding = $PAD" >> config.ini
  
  echo "" >> config.ini
  echo "[Detection]" >> config.ini
  echo "Enable Wifi icon?"
  read -p "[Y]es or [n]o: " WIFI
  if [[ $WIFI = [nN] ]] ; then
    WIFI="False"
  else
    WIFI="True"
  fi
  echo "Wifi = $WIFI" >> config.ini
  
  echo "Enable Blutooth icon?"
  read -p "[Y]es or [n]o: " BT
  if [[ $BT = [nN] ]] ; then
    BT="False"
  else
    BT="True"
  fi
  echo "Bluetooth = $BT" >> config.ini
 
  echo "Enable Audio icon?"
  read -p "[Y]es or [n]o: " AUDIO
  if [[ $AUDIO = [nN] ]] ; then
    AUDIO="False"
  else
    AUDIO="True"
  fi
  echo "Audio = $AUDIO" >> config.ini
  
  echo "Enable Battery Voltage detection using ADC? (Requires specific hardware)"
  read -p "[y]es or [N]o: " BATADC
  if [[ $BATADC = [yY] ]] ; then
    BATADC="True"
  else
    BATADC="False"
  fi
  echo "BatteryADC = $BATADC" >> config.ini 
  
  echo "Enable Low Battery detection using GPIO? (Requires specific hardware)"
  read -p "[y]es or [N]o: " BATLDO
  if [[ $BATLDO = [yY] ]] ; then
    BATLDO="True"
    LDOGPIO=28
    while [[ "$LDOGPIO" -lt 0 || "$LDOGPIO" -gt 27 ]]
    do
      read -p "LDO GPIO pin [0 - 27]: " LDOGPIO
    done
    read -p "LDO GPIO Active [L]ow or Active [h]igh? " LDOPOL
  else
    BATLDO="False"
  fi
  echo "BatteryLDO = $BATLDO" >> config.ini
  
  echo "Enable Shutdown via GPIO? (Requires specific hardware)"
  read -p "[y]es or [N]o: " SD
  if [[ $SD = [yY] ]] ; then
    SD="True"
    SDGPIO=28
    while [[ "$SDGPIO" -lt 0 || "$SDGPIO" -gt 27 ]]
    do
      read -p "Shutdown GPIO pin [0 - 27]: " SDGPIO
    done
    read -p "Shutdown GPIO Active [L]ow or Active [h]igh? " SDPOL
  else
    SD="False"
  fi
  echo "ShutdownGPIO = $SD" >> config.ini
  
  echo "" >> config.ini 
  echo "[BatteryLDO]" >> config.ini
  echo "GPIO = $LDOGPIO" >> config.ini
  if [[ $LDPOL = [hH] ]] ; then
    echo "ActiveLow = False" >> config.ini
  else
    echo "ActiveLow = True" >> config.ini
  fi
  
  echo "" >> config.ini 
  echo "[ShutdownGPIO]" >> config.ini 
  echo "GPIO = $SDGPIO" >> config.ini 
  if [[ $SDPOL = [hH] ]] ; then
    echo "ActiveLow = False" >> config.ini
  else
    echo "ActiveLow = True" >> config.ini
  fi
  echo "config.ini creation complete"
fi

echo ""
echo "Installing pngview by AndrewFromMelbourne"
echo "--------------------------------------------------"
cd ~/src
git clone https://github.com/AndrewFromMelbourne/raspidmx.git
cd ~/src/raspidmx/lib
make
cd ~/src/raspidmx/pngview
make
sudo cp pngview /usr/local/bin/

echo ""
echo "Downloading Material Design Icons by Google"
echo "--------------------------------------------------"
cd ~/src
git clone http://github.com/google/material-design-icons/ material-design-icons-master

echo ""
echo "Installing required packages"
echo "--------------------------------------------------"
sudo apt-get install python3-psutil python3-rpi.gpio

echo ""
echo "Downloading RetroPie Status Overlay"
echo "--------------------------------------------------"
cd ~/src
git clone http://github.com/bverc/retropie_status_overlay
if [[ $CONFIG = [bB] ]] ; then
  echo "Moving built config.ini to ~/src/retropie_status_overlay"
  mv ~/src/config.ini ~/src/retropie_status_overlay/config.ini
else
  echo "Copying default config.ini"
  echo "Edit this file after install is complete"
  cp ~/src/retropie_status_overlay/config.ini.example ~/src/retropie_status_overlay/config.ini
fi

echo ""
echo "Add Retropie Status Overlay to Crontab"
echo "--------------------------------------------------"
(crontab -l ; echo "@reboot python3 /home/pi/src/retropie_status_overlay/overlay.py") | sort - | uniq - | crontab -
echo "Your crontab now looks like:"
crontab -l

echo ""
echo "--------------------------------------------------"
echo "Retropie Status Overlay installation complete!"
echo "--------------------------------------------------"
echo "Retropie Status Overlay will now run at next boot."
echo "~/src/retropie_status_overlay/config.ini may be edited at any time."
echo "You might also want to delete this file."
echo "A copy remains in ~/src/retropie_status_overlay/"
echo "Use 'rm install.sh' to remove it."