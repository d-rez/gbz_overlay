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

from devices import *

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
}
wifi.icons(icons, iconpath, config['Icons']['Size'])
bluetooth.icons(icons, iconpath, config['Icons']['Size'])
audio.icons(icons, iconpath, config['Icons']['Size'])

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
      elif not v:
        kill_overlay_process(k)

  return val

def battery(new_ingame):
  global battery_level, overlay_processes, battery_history, shutdown_pending, count
  
  value_v = adc.read(config.getint("Detection", "ADCChannel")) * config.getfloat("Detection", "ADCGain")

  count+=1

  my_logger.info("Battery Voltage " + str(value_v))

  battery_history.append(value_v)
  try:
    level_icon=translate_bat(median(battery_history))
  except IndexError:
    level_icon="alert_red"

  if config.getboolean('Detection','ADCShutdown'):
    if shutdown_pending and value_v > config.getfloat("Detection", "VMinCharging"):
      shutdown(False)
      shutdown_pending = False
    elif value_v < config.getfloat("Detection", "VMinDischarging"):
      shutdown(True)
      shutdown_pending = True

  if level_icon != battery_level or new_ingame != ingame:
    kill_overlay_process("bat")
    
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

def kill_overlay_process(device):
  if device in overlay_processes:
    overlay_processes[device].kill()
    del overlay_processes[device]
  
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
  kill_overlay_process("caution")
  if low_voltage:
    my_logger.warning("Low Battery. Initiating shutdown in 60 seconds.")
    overlay_processes["caution"] = subprocess.Popen(pngview_call(int(resolution[0]) / 2 - 60, int(resolution[1]) / 2 - 60, icons["battery_critical_shutdown"]))
    os.system("sudo shutdown -P +1")
  else:
    os.system("sudo shutdown -c")
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
shutdown_pending = False

# Main Loop
while True:
  count = 0
  
  # Check if retroarch is running
  new_ingame = check_process('retroarch')
  
  if new_ingame:
    alpha = config['Detection']['InGameAlpha']
  else:
    alpha = "255";

  log = str("%s" % (datetime.now()))
  
  # Battery Icon
  if config.getboolean('Detection','BatteryADC'):
    (battery_level, value_v) = battery(new_ingame)
    log = log + str(", median: %.2f, %s,icon: %s" % (
      value_v,
      list(battery_history),
      battery_level
    ))
  
  # Wifi Icon
  if config.getboolean('Detection','Wifi'):
    count += 1
    (new_wifi_state, wifi_quality) = wifi.get_state()
    if new_wifi_state != wifi_state or new_ingame != ingame:  
      kill_overlay_process("wifi")
      overlay_processes["wifi"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons[new_wifi_state], alpha))
      wifi_state = new_wifi_state
    log = log + str(", wifi: %s %i%%" % (
      wifi_state,
      wifi_quality
    ))
    
  # Bluetooth Icon
  if config.getboolean('Detection','Bluetooth'):
    count += 1
    new_bt_state = bluetooth.getstate()
    if new_bt_state != bt_state or new_ingame != ingame:
      kill_overlay_process("bt")
      overlay_processes["bt"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons[new_bt_state], alpha))
      bt_state = new_bt_state
    log = log + str(", bt: %s" % (bt_state))
  
  # Audio Icon
  if config.getboolean('Detection', 'Audio'):
    count += 1
    (new_audio_state, audio_volume) = audio.getstate()
    if new_audio_state != audio_state or new_ingame != ingame:
      kill_overlay_process("audio")
      overlay_processes["audio"] = subprocess.Popen(pngview_call(x_position(count), y_position, icons[new_audio_state], alpha))
      audio_state = new_audio_state
    log = log + str(", Audio: %s %i%%" % (audio_state, audio_volume))

  env = environment()
  my_logger.info(log + str(", throttle: %#0x" % (env)))
  
  ingame = new_ingame
  time.sleep(5)
  