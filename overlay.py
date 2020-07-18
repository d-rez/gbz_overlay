#!/usr/bin/python3
# @ made by d-rez / dark_skeleton
# Requires:
# - pngview
# - an entry in crontab
# - material_design_icons_master github clone

import time
import subprocess
import os
import re
import logging
import logging.handlers
import psutil
import configparser
import RPi.GPIO as GPIO
from datetime import datetime
from statistics import median
from collections import deque
from enum import Enum

# Load Configuration
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + '/config.ini')
icon_size = int(config['Icons']['Size'])
icon_color = config['Icons']['Color']
detect_battery = config.getboolean('Detection','BatteryADC')
detect_wifi = config.getboolean('Detection','Wifi')
detect_bluetooth = config.getboolean('Detection','Bluetooth')
detect_audio = config.getboolean('Detection', 'Audio')

# Set up logging
logfile = os.path.dirname(os.path.realpath(__file__)) + "/overlay.log"
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=102400, backupCount=1)
my_logger.addHandler(handler)
console = logging.StreamHandler()
my_logger.addHandler(console)


fbfile="tvservice -s"

# Get Framebuffer resolution
resolution=re.search("(\d{3,}x\d{3,})", subprocess.check_output(fbfile.split()).decode().rstrip()).group().split('x')
my_logger.info(resolution)

# Setup icons
iconpath="/home/pi/src/material-design-icons-master/device/drawable-mdpi/"
iconpath2 = os.path.dirname(os.path.realpath(__file__)) + "/overlay_icons/"
iconpath3="/home/pi/src/material-design-icons-master/av/drawable-mdpi/"

pngview_path="/usr/local/bin/pngview"
pngview_call=[pngview_path, "-d", "0", "-b", "0x0000", "-n", "-l", "15000", "-y", "0", "-x"]


env_icons = {
  "under-voltage": iconpath2 + "flash_" + str(icon_size) + ".png",
  "freq-capped":   iconpath2 + "thermometer_" + str(icon_size) + ".png",
  "throttled":     iconpath2 + "thermometer-lines_" + str(icon_size) + ".png"
}
wifi_icons = {
  "connected4": iconpath + "ic_signal_wifi_4_bar_" + icon_color + "_"      + str(icon_size) + "dp.png",
  "connected3": iconpath + "ic_signal_wifi_3_bar_" + icon_color + "_"      + str(icon_size) + "dp.png",
  "connected2": iconpath + "ic_signal_wifi_2_bar_" + icon_color + "_"      + str(icon_size) + "dp.png",
  "connected1": iconpath + "ic_signal_wifi_1_bar_" + icon_color + "_"      + str(icon_size) + "dp.png",
  "connected0": iconpath + "ic_signal_wifi_0_bar_" + icon_color + "_"      + str(icon_size) + "dp.png",
  "disabled":  iconpath + "ic_signal_wifi_off_" + icon_color + "_"   + str(icon_size) + "dp.png",
  "enabled":   iconpath + "ic_signal_wifi_0_bar_" + icon_color + "_" + str(icon_size) + "dp.png"
}
bt_icons = {
  "enabled":   iconpath + "ic_bluetooth_" + icon_color + "_"           + str(icon_size) + "dp.png",
  "connected": iconpath + "ic_bluetooth_connected_" + icon_color + "_" + str(icon_size) + "dp.png",
  "disabled":  iconpath + "ic_bluetooth_disabled_" + icon_color + "_"  + str(icon_size) + "dp.png"
}
audio_icons = {
  "volume0":   iconpath3 + "ic_volume_mute_" + icon_color + "_"           + str(icon_size) + "dp.png",
  "volume1":   iconpath3 + "ic_volume_down_" + icon_color + "_" + str(icon_size) + "dp.png",
  "volume2":   iconpath3 + "ic_volume_up_" + icon_color + "_" + str(icon_size) + "dp.png",
  "disabled":  iconpath3 + "ic_volume_off_" + icon_color + "_"  + str(icon_size) + "dp.png"
}
icon_battery_critical_shutdown = iconpath2 + "battery-alert-128.png"

wifi_carrier = "/sys/class/net/wlan0/carrier" # 1 when wifi connected, 0 when disconnected and/or ifdown
wifi_linkmode = "/sys/class/net/wlan0/link_mode" # 1 when ifup, 0 when ifdown
bt_devices_dir="/sys/class/bluetooth"
env_cmd="vcgencmd get_throttled"


if detect_battery:
  import Adafruit_ADS1x15
  adc = Adafruit_ADS1x15.ADS1015()
  # Choose a gain of 1 for reading voltages from 0 to 4.09V.
  # Or pick a different gain to change the range of voltages that are read:
  #  - 2/3 = +/-6.144V
  #  -   1 = +/-4.096V
  #  -   2 = +/-2.048V
  #  -   4 = +/-1.024V
  #  -   8 = +/-0.512V
  #  -  16 = +/-0.256V
  # See table 3 in the ADS1015i/ADS1115 datasheet for more info on gain.

  #charging no load: 4.85V max (full bat)
  #charging es load: 4.5V max

  vmax = {"discharging": 3.95,
          "charging"   : 4.5 }
  vmin = {"discharging": 3.2,
          "charging"   : 4.25 }
  icons = { "discharging": [ "alert_red", "alert", "20", "30", "30", "50", "60",
                             "60", "80", "90", "full", "full" ],
            "charging"   : [ "charging_20", "charging_20", "charging_20",
                             "charging_30", "charging_30", "charging_50",
                             "charging_60", "charging_60", "charging_80",
                             "charging_90", "charging_full", "charging_full" ]}
                             
  # From my tests:
  # over 4V => charging
  # 4.7V => charging and charged 100%
  # 3.9V => not charging, 100%
  # 3.2V => will die in 10 mins under load, shut down
  # 3.3V => warning icon?

class InterfaceState(Enum):
  DISABLED = 0
  ENABLED = 1
  CONNECTED = 2
  CONNECTED_3 = 3
  CONNECTED_2 = 4
  CONNECTED_1 = 5
  CONNECTED_0 = 6

def translate_bat(voltage):
  # Figure out how 'wide' each range is
  state = voltage <= vmax["discharging"] and "discharging" or "charging"

  leftSpan = vmax[state] - vmin[state]
  rightSpan = len(icons[state]) - 1

  # Convert the left range into a 0-1 range (float)
  valueScaled = float(voltage - vmin[state]) / float(leftSpan)

  # Convert the 0-1 range into a value in the right range.
  return icons[state][int(round(valueScaled * rightSpan))]

def wifi(new_ingame):
  global wifi_state, ingame, overlay_processes, position, wifi_quality

  position += 1
  new_wifi_state = InterfaceState.DISABLED
  try:
    f = open(wifi_carrier, "r")
    carrier_state = int(f.read().rstrip())
    f.close()
    if carrier_state == 1:
      # ifup and connected to AP
      new_wifi_state = InterfaceState.CONNECTED
      # get wifi quality
      cmd = subprocess.Popen(["iwconfig", "wlan0"], stdout=subprocess.PIPE)
      for line in cmd.stdout:
        if b'Link Quality' in line:
          x = line.split()[1].split(b"=")[1].split(b"/")
          wifi_quality = int(100*int(x[0])/int(x[1]))
          if wifi_quality < 20:
            new_wifi_state = InterfaceState.CONNECTED_0
          elif wifi_quality < 40:
            new_wifi_state = InterfaceState.CONNECTED_1
          elif wifi_quality < 60:
            new_wifi_state = InterfaceState.CONNECTED_2
          elif wifi_quality < 80:
            new_wifi_state = InterfaceState.CONNECTED_3
          else:
            new_wifi_state = InterfaceState.CONNECTED
    elif carrier_state == 0:
      f = open(wifi_linkmode, "r")
      linkmode_state = int(f.read().rstrip())
      f.close()
      if linkmode_state == 1:
        # ifup but not connected to any network
        new_wifi_state = InterfaceState.ENABLED
        # else - must be ifdown
      
  except IOError:
    pass

  if new_wifi_state != wifi_state or new_ingame != ingame:
    if "wifi" in overlay_processes:
      overlay_processes["wifi"].kill()
      del overlay_processes["wifi"]
    
    if not new_ingame:
      if new_wifi_state == InterfaceState.ENABLED:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["enabled"]])
      elif new_wifi_state == InterfaceState.DISABLED:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["disabled"]])
      elif new_wifi_state == InterfaceState.CONNECTED:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["connected4"]])
      elif new_wifi_state == InterfaceState.CONNECTED_3:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["connected3"]])
      elif new_wifi_state == InterfaceState.CONNECTED_2:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["connected2"]])
      elif new_wifi_state == InterfaceState.CONNECTED_1:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["connected1"]])
      elif new_wifi_state == InterfaceState.CONNECTED_0:
        overlay_processes["wifi"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), wifi_icons["connected0"]])
  return new_wifi_state

def audio(new_ingame):
  global audio_state, ingame, overlay_processes, position, audio_volume

  position += 1
  new_audio_state = InterfaceState.DISABLED
  try:
    cmd = subprocess.Popen('amixer', stdout=subprocess.PIPE)
    for line in cmd.stdout:
      if b'[' in line:
        if line.split(b"[")[3].split(b"]")[0] == b"on":
          audio_volume = int(line.split(b"[")[1].split(b"%")[0])
          if audio_volume == 0:
            new_audio_state = InterfaceState.ENABLED
          elif audio_volume < 50:
            new_audio_state = InterfaceState.CONNECTED_0
          else:
            new_audio_state = InterfaceState.CONNECTED_1
        break

  except IOError:
    pass

  if new_audio_state != audio_state or new_ingame != ingame:
    if "audio" in overlay_processes:
      overlay_processes["audio"].kill()
      del overlay_processes["audio"]

    if not new_ingame:
      if new_audio_state == InterfaceState.ENABLED:
        overlay_processes["audio"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), audio_icons["volume0"]])
      elif new_audio_state == InterfaceState.DISABLED:
        overlay_processes["audio"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), audio_icons["disabled"]])
      elif new_audio_state == InterfaceState.CONNECTED_1:
        overlay_processes["audio"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), audio_icons["volume2"]])
      elif new_audio_state == InterfaceState.CONNECTED_0:
        overlay_processes["audio"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), audio_icons["volume1"]])
  
  return new_audio_state

def bluetooth(new_ingame):
  global bt_state, overlay_processes, position

  position += 1
  new_bt_state = InterfaceState.DISABLED
  try:
    p1 = subprocess.Popen('hciconfig', stdout = subprocess.PIPE)
    p2 = subprocess.Popen(['awk', 'FNR == 3 {print tolower($1)}'], stdin = p1.stdout, stdout=subprocess.PIPE)
    state=p2.communicate()[0].decode().rstrip()
    if state == "up":
      new_bt_state = InterfaceState.ENABLED
  except IOError:
    pass

  try:
    devices=os.listdir(bt_devices_dir)
    if len(devices) > 1:
      new_bt_state = InterfaceState.CONNECTED
  except OSError:
    pass

  if new_bt_state != bt_state or new_ingame != ingame:
    if "bt" in overlay_processes:
      overlay_processes["bt"].kill()
      del overlay_processes["bt"]

    if not new_ingame:
      if new_bt_state == InterfaceState.CONNECTED:
        overlay_processes["bt"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), bt_icons["connected"]])
      elif new_bt_state == InterfaceState.ENABLED:
        overlay_processes["bt"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), bt_icons["enabled"]])
      elif new_bt_state == InterfaceState.DISABLED:
        overlay_processes["bt"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), bt_icons["disabled"]])
  return new_bt_state

def environment():
  global overlay_processes, position

  val=int(re.search("throttled=(0x\d+)", subprocess.check_output(env_cmd.split()).decode().rstrip()).groups()[0], 16)
  env = {
    "under-voltage": bool(val & 0x01),
    "freq-capped": bool(val & 0x02),
    "throttled": bool(val & 0x04)
  }
  for k,v in env.items():
    if v and not k in overlay_processes:
      position += 1
      overlay_processes[k] = subprocess.Popen(pngview_call + [str(int(resolution[0]) - icon_size * position), env_icons[k]])
    elif not v and k in overlay_processes:
      overlay_processes[k].kill()
      del(overlay_processes[k])
  #return env # too much data
  return val

def battery(new_ingame):
  global battery_level, overlay_processes, battery_history
  value = adc.read_adc(0, gain=2/3)
  value_v = value * 0.003

  battery_history.append(value_v)
  try:
    level_icon=translate_bat(median(battery_history))
  except IndexError:
    level_icon="unknown"


  if value_v <= 3.2:
    shutdown(True)

  if level_icon != battery_level or new_ingame != ingame:
    if "bat" in overlay_processes:
      overlay_processes["bat"].kill()
      del overlay_processes["bat"]
    
    bat_iconpath = iconpath + "ic_battery_" + level_icon + "_" + icon_color + "_" + str(icon_size) + "dp.png"
    if (level_icon == "alert_red"):
      bat_iconpath = iconpath2 + "battery-alert_" + str(icon_size) + ".png"
    elif not new_ingame:
      overlay_processes["bat"] = subprocess.Popen(pngview_call + [ "0", bat_iconpath])
  return (level_icon, value_v)



def check_process(process):
  #Iterate over the all the running process
  for proc in psutil.process_iter():
    try:
      # Check if process name contains the given name string.
      if process.lower() in proc.name().lower():
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
      pass
  return False;
  
  
def interrupt_shutdown(channel):
  if config.getboolean('BatteryLDO','ActiveLow'):
    shutdown(not GPIO.input(int(config['BatteryLDO']['GPIO'])))
  else:
    shutdown(GPIO.input(int(config['BatteryLDO']['GPIO'])))
 
def shutdown(low_voltage):
  if low_voltage:
    my_logger.warning("Low Battery. Initiating shutdown in 60 seconds.")
    if "caution" in overlay_processes:
      overlay_processes["caution"].kill()
      del overlay_processes["caution"]
    
    overlay_processes["caution"] = subprocess.Popen(pngview_call + [str(int(resolution[0]) / 2 - 64), "-y", str(int(resolution[1]) / 2 - 64), icon_battery_critical_shutdown])
    os.system("sudo shutdown +1")
  
  else:
    os.system("sudo shutdown -c")
    overlay_processes["caution"].kill()
    my_logger.info("Power Restored, shutdown aborted.")

GPIO.setmode(GPIO.BCM)
if config.getboolean('Detection','BatteryLDO'):
  my_logger.info("LDO Active on GPIO %s", config['BatteryLDO']['GPIO'])
  GPIO.setup(int(config['BatteryLDO']['GPIO']), GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.add_event_detect(int(config['BatteryLDO']['GPIO']), GPIO.BOTH, callback = interrupt_shutdown, bouncetime = 500)

overlay_processes = {}
wifi_state = None
bt_state = None
audio_state = None
battery_level = None
env = None
ingame = None
value_v = None
battery_history = deque(maxlen=5)
audio_volume = 0

while True:
  position = 0;
  # Check if retroarch is running
  new_ingame = check_process('retroarch')
  log = str("%s" % (datetime.now()))
  if detect_battery:
    (battery_level, value_v) = battery(new_ingame)
    log = log + str(", median: %.2f, %s,icon: %s" % (
      value_v,
      list(battery_history),
      battery_level
    ))
  if detect_wifi:
    wifi_state = wifi(new_ingame)
    if wifi_state == InterfaceState.CONNECTED:
      log = log + str(", wifi: %s %i%%" % (
        wifi_state.name,
        wifi_quality
      ))
    else:
      log = log + str(", wifi: %s" % (
        wifi_state.name
      ))
  if detect_bluetooth:
    bt_state = bluetooth(new_ingame)
    log = log + str(", bt: %s" % (bt_state.name))
  if detect_audio:
    audio_state = audio(new_ingame)
    log = log + str(", Audio: %s %i%%" % (audio_state.name, audio_volume))
  env = environment()
  my_logger.info(log + str(", throttle: %#0x" % (env)))
  
  ingame = new_ingame
  time.sleep(5)
  
