#!/usr/bin/env python3
# Authors: d-rez, bverc, louisvarley
# Requires:
# - pngview by AndrewFromMelbourne
# - an entry in crontab

import time
import subprocess
import os
import re
import logging
import logging.handlers
import psutil
import configparser
from RPi import GPIO
from datetime import datetime
from statistics import median
from collections import deque
from enum import Enum

# Load Configuration
config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + '/config.ini')

# Set up logging
logfile = os.path.dirname(os.path.realpath(__file__)) + "/overlay.log"
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=102400, backupCount=1)
my_logger.addHandler(handler)
console = logging.StreamHandler()
my_logger.addHandler(console)

# Get Framebuffer resolution
fbfile="tvservice -s"
resolution=re.search("(\d{3,}x\d{3,})", subprocess.check_output(fbfile.split()).decode().rstrip()).group().split('x')
my_logger.info(resolution)

# Setup icons
iconpath = os.path.dirname(os.path.realpath(__file__)) + "/colored_icons/"

pngview_path="/usr/local/bin/pngview"
y_position = config['Icons']['Padding']
if config['Icons']['Vertical'] == "bottom":
  y_position = str(int(resolution[1]) - int(config['Icons']['Size']) - int(config['Icons']['Padding']))

def pngview_call(x, y, icon, alpha=255):
  pngview_call=[pngview_path, "-d", "0", "-b", "0x0000", "-n", "-l", "15000", "-y", str(y), "-x", str(x)]
  if int(alpha) < 255:
    pngview_call += ["-a", str(alpha)]
  pngview_call += [icon]
  
  return pngview_call

icons = {
  "under-voltage": iconpath + "flash_" + config['Icons']['Size'] + ".png",
  "freq-capped": iconpath + "thermometer_" + config['Icons']['Size'] + ".png",
  "throttled": iconpath + "thermometer-lines_" + config['Icons']['Size'] + ".png",
  "battery_critical_shutdown": iconpath + "battery-alert_120.png",
  "wifi_4": iconpath + "ic_signal_wifi_4_bar_black_" + config['Icons']['Size'] + "dp.png",
  "wifi_3": iconpath + "ic_signal_wifi_3_bar_black_" + config['Icons']['Size'] + "dp.png",
  "wifi_2": iconpath + "ic_signal_wifi_2_bar_black_" + config['Icons']['Size'] + "dp.png",
  "wifi_1": iconpath + "ic_signal_wifi_1_bar_black_" + config['Icons']['Size'] + "dp.png",
  "wifi_0": iconpath + "ic_signal_wifi_0_bar_black_" + config['Icons']['Size'] + "dp.png",
  "wifi_off": iconpath + "ic_signal_wifi_off_black_" + config['Icons']['Size'] + "dp.png",
  "bt_enabled": iconpath + "ic_bluetooth_black_" + config['Icons']['Size'] + "dp.png",
  "bt_connected": iconpath + "ic_bluetooth_connected_black_" + config['Icons']['Size'] + "dp.png",
  "bt_disabled": iconpath + "ic_bluetooth_disabled_black_" + config['Icons']['Size'] + "dp.png",
  "volume_0": iconpath + "ic_volume_mute_black_" + config['Icons']['Size'] + "dp.png",
  "volume_1": iconpath + "ic_volume_down_black_" + config['Icons']['Size'] + "dp.png",
  "volume_2": iconpath + "ic_volume_up_black_" + config['Icons']['Size'] + "dp.png",
  "volume_mute": iconpath + "ic_volume_off_black_"  + config['Icons']['Size'] + "dp.png"
}

wifi_carrier = "/sys/class/net/wlan0/carrier" # 1 when wifi connected, 0 when disconnected and/or ifdown
wifi_linkmode = "/sys/class/net/wlan0/link_mode" # 1 when ifup, 0 when ifdown
bt_devices_dir="/sys/class/bluetooth"
env_cmd="vcgencmd get_throttled"


if config.getboolean('Detection','BatteryADC'):
  import importlib
  adc = importlib.import_module('adc.' + config.get('Detection','ADCType').lower())
  
  vmax = {"discharging": config.getfloat("Detection", "VMaxDischarging"),
          "charging"   : config.getfloat("Detection", "VMaxCharging") }
  vmin = {"discharging": config.getfloat("Detection", "VMinDischarging"),
          "charging"   : config.getfloat("Detection", "VMinCharging") }

  bat_icons = { "discharging": [ "alert_red", "alert", "20", "30", "30", "50", "60",
                             "60", "80", "90", "full", "full" ],
            "charging"   : [ "charging_20", "charging_20", "charging_20",
                             "charging_30", "charging_30", "charging_50",
                             "charging_60", "charging_60", "charging_80",
                             "charging_90", "charging_full", "charging_full" ]}

class InterfaceState(Enum):
  DISABLED = 0
  ENABLED = 1
  CONNECTED = 2
  CONNECTED_3 = 3
  CONNECTED_2 = 4
  CONNECTED_1 = 5
  CONNECTED_0 = 6
  
  
def x_position(count):
  if config['Icons']['Horizontal'] == "right":
    return int(resolution[0]) - (int(config['Icons']['Size']) + int(config['Icons']['Padding'])) * count
  else:
    return int(config['Icons']['Padding']) + (int(config['Icons']['Size']) + int(config['Icons']['Padding'])) * (count - 1)

def translate_bat(voltage):
  # Figure out how 'wide' each range is
  state = voltage <= vmax["discharging"] and "discharging" or "charging"

  leftSpan = vmax[state] - vmin[state]
  rightSpan = len(bat_icons[state]) - 1

  # Convert the left range into a 0-1 range (float)
  valueScaled = float(voltage - vmin[state]) / float(leftSpan)

  # Convert the 0-1 range into a value in the right range.
  return bat_icons[state][int(round(valueScaled * rightSpan))]

def wifi(new_ingame):
  global wifi_state, ingame, overlay_processes, count, wifi_quality

  count += 1
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
    
    if new_wifi_state == InterfaceState.ENABLED:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_0"], alpha))
    elif new_wifi_state == InterfaceState.DISABLED:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_off"], alpha))
    elif new_wifi_state == InterfaceState.CONNECTED:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_4"], alpha))
    elif new_wifi_state == InterfaceState.CONNECTED_3:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_3"], alpha))
    elif new_wifi_state == InterfaceState.CONNECTED_2:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_2"], alpha))
    elif new_wifi_state == InterfaceState.CONNECTED_1:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_1"], alpha))
    elif new_wifi_state == InterfaceState.CONNECTED_0:
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["wifi_0"], alpha))
  return new_wifi_state

def audio(new_ingame):
  global audio_state, ingame, overlay_processes, count, audio_volume

  count += 1
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

    if new_audio_state == InterfaceState.ENABLED:
      overlay_processes["audio"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["volume_0"], alpha))
    elif new_audio_state == InterfaceState.DISABLED:
      overlay_processes["audio"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["volume_mute"], alpha))
    elif new_audio_state == InterfaceState.CONNECTED_1:
      overlay_processes["audio"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["volume_2"], alpha))
    elif new_audio_state == InterfaceState.CONNECTED_0:
      overlay_processes["audio"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["volume_1"], alpha))
  
  return new_audio_state

def bluetooth(new_ingame):
  global bt_state, overlay_processes, count

  count += 1
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

    if new_bt_state == InterfaceState.CONNECTED:
      overlay_processes["bt"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["bt_connected"], alpha))
    elif new_bt_state == InterfaceState.ENABLED:
      overlay_processes["bt"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["bt_enabled"], alpha))
    elif new_bt_state == InterfaceState.DISABLED:
      overlay_processes["bt"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons["bt_disabled"], alpha))
  return new_bt_state

def environment():
  global overlay_processes, count

  val=int(re.search("throttled=(0x\d+)", subprocess.check_output(env_cmd.split()).decode().rstrip()).groups()[0], 16)
  env = {
    "under-voltage": bool(val & 0x01),
    "freq-capped": bool(val & 0x02),
    "throttled": bool(val & 0x04)
  }

  if(config.get('Detection','HideEnvWarnings') == False):
    for k,v in env.items():
      if v and not k in overlay_processes:
        count += 1
        overlay_processes[k] = subprocess.Popen(pngview_call(x_position(count), y_position, icons[k]), alpha)
      elif not v and k in overlay_processes:
        overlay_processes[k].kill()
        del(overlay_processes[k])

  return val

def battery(new_ingame):
  global battery_level, overlay_processes, battery_history, count
  
  value_v = adc.read(config.getint("Detection", "ADCChannel")) * config.getfloat("Detection", "ADCGain")

  count+=1

  my_logger.info("Battery Voltage " + str(value_v))

  battery_history.append(value_v)
  try:
    level_icon=translate_bat(median(battery_history))
  except IndexError:
    level_icon="unknown"

  if value_v <= 3.2 and config.getboolean('Detection','ADCShutdown'):
    shutdown(True)

  if level_icon != battery_level or new_ingame != ingame:
    if "bat" in overlay_processes:
      overlay_processes["bat"].kill()
      del overlay_processes["bat"]
    
    bat_iconpath = iconpath + "ic_battery_" + level_icon + "_black_" + config['Icons']['Size'] + "dp.png"
    if (level_icon == "alert_red"):
      bat_iconpath = iconpath + "battery-alert_" + config['Icons']['Size'] + ".png"
    overlay_processes["bat"] = subprocess.Popen(pngview_call(x_position(count), y_position, bat_iconpath, alpha))
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
  if channel == int(config['BatteryLDO']['GPIO']):
    if GPIO.input(channel) != config.getboolean('BatteryLDO','ActiveLow'):
      shutdown(True)
    else:
      shutdown(False)
  elif channel == int(config['ShutdownGPIO']['GPIO']):
    if GPIO.input(channel) != config.getboolean('ShutdownGPIO','ActiveLow'):
      time.sleep(1)
      if GPIO.input(channel) != config.getboolean('ShutdownGPIO','ActiveLow'):
        my_logger.warning("Shutdown button pressed, shutting down now.")
        os.system("sudo shutdown -P now")
      else:
        my_logger.info("Shutdown button pressed, but not long enough to trigger Shutdown.")
 
def shutdown(low_voltage):
  if low_voltage:
    my_logger.warning("Low Battery. Initiating shutdown in 60 seconds.")
    if "caution" in overlay_processes:
      overlay_processes["caution"].kill()
      del overlay_processes["caution"]
    
    overlay_processes["caution"] = subprocess.Popen(pngview_call(int(resolution[0]) / 2 - 60, int(resolution[1]) / 2 - 60, icons["battery_critical_shutdown"]))
    os.system("sudo shutdown -P +1")
  else:
    os.system("sudo shutdown -c")
    overlay_processes["caution"].kill()
    my_logger.info("Power Restored, shutdown aborted.")

GPIO.setmode(GPIO.BCM)
if config.getboolean('Detection','BatteryLDO'):
  my_logger.info("LDO Active on GPIO %s", config['BatteryLDO']['GPIO'])
  GPIO.setup(int(config['BatteryLDO']['GPIO']), GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.add_event_detect(int(config['BatteryLDO']['GPIO']), GPIO.BOTH, callback = interrupt_shutdown, bouncetime = 500)

if config.getboolean('Detection','ShutdownGPIO'):
  my_logger.info("Shutdown button on GPIO %s", config['ShutdownGPIO']['GPIO'])
  GPIO.setup(int(config['ShutdownGPIO']['GPIO']), GPIO.IN, pull_up_down = GPIO.PUD_UP)
  GPIO.add_event_detect(int(config['ShutdownGPIO']['GPIO']), GPIO.BOTH, callback = interrupt_shutdown, bouncetime = 200)

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
  count = 0
  
  # Check if retroarch is running
  new_ingame = check_process('retroarch')
  
  if new_ingame:
    alpha = config['Detection']['InGameAlpha']
  else:
    alpha = "255";

  log = str("%s" % (datetime.now()))
  if config.getboolean('Detection','BatteryADC'):
    (battery_level, value_v) = battery(new_ingame)
    log = log + str(", median: %.2f, %s,icon: %s" % (
      value_v,
      list(battery_history),
      battery_level
    ))
  if config.getboolean('Detection','Wifi'):
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
  if config.getboolean('Detection','Bluetooth'):
    bt_state = bluetooth(new_ingame)
    log = log + str(", bt: %s" % (bt_state.name))
  if config.getboolean('Detection', 'Audio'):
    audio_state = audio(new_ingame)
    log = log + str(", Audio: %s %i%%" % (audio_state.name, audio_volume))
  env = environment()
  my_logger.info(log + str(", throttle: %#0x" % (env)))
  
  ingame = new_ingame
  time.sleep(5)
  