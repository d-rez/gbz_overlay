#!/usr/bin/env python3
""" Python script to display status icons on top of your RetroPie games and emulationstation menus
github.com/bverc/retropie-status-overlay

Authors: d-rez, bverc, louisvarley

Requires:
- pngview by AndrewFromMelbourne
- an entry in crontab
"""

import time
import subprocess
import os
import re
import logging
import logging.handlers
import configparser
from datetime import datetime

import psutil
from RPi import GPIO

from devices import wifi, audio, bluetooth, battery

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
FB_FILE = "tvservice -s"
FB_OUTPUT = subprocess.check_output(FB_FILE.split()).decode().rstrip()
resolution = re.search(r"(\d{3,}x\d{3,})", FB_OUTPUT).group().split('x')
my_logger.info(resolution)

# Setup icons
ICON_PATH = os.path.dirname(os.path.realpath(__file__)) + "/colored_icons/"
ICON_SIZE = config['Icons']['Size']
ICON_PADDING = config['Icons']['Padding']

PNGVIEW_PATH = "/usr/local/bin/pngview"
Y_POS = ICON_PADDING
if config['Icons']['Vertical'] == "bottom":
    Y_POS = str(int(resolution[1]) - int(ICON_SIZE) - int(ICON_PADDING))

def pngview_call(x, y, icon, alpha=255):
    """Return an array used to call pngview from binary location."""
    pngview_call = [PNGVIEW_PATH, "-d", "0", "-b", "0x0000",
                    "-n", "-l", "15000", "-y", str(y), "-x", str(x)]
    if int(alpha) < 255:
        pngview_call += ["-a", str(alpha)]
    pngview_call += [icon]

    return pngview_call

icons = {
    "under-voltage": ICON_PATH + "flash_" + ICON_SIZE + ".png",
    "freq-capped": ICON_PATH + "thermometer_" + ICON_SIZE + ".png",
    "throttled": ICON_PATH + "thermometer-lines_" + ICON_SIZE + ".png",
}
wifi.add_icons(icons, ICON_PATH, ICON_SIZE)
bluetooth.add_icons(icons, ICON_PATH, ICON_SIZE)
audio.add_icons(icons, ICON_PATH, ICON_SIZE)
battery.add_icons(icons, ICON_PATH)

env_cmd = "vcgencmd get_throttled"

def x_pos(count):
    """Return x position for next icon based on number or icons already displayed."""
    if config['Icons']['Horizontal'] == "right":
        return int(resolution[0]) - (int(ICON_SIZE) + int(ICON_PADDING)) * count
    return int(ICON_PADDING) + (int(ICON_SIZE) + int(ICON_PADDING)) * (count - 1)

def environment():
    """Return state of environment, such as unndervoltage or throttled."""
    global overlay_processes, count

    env_output = subprocess.check_output(env_cmd.split()).decode().rstrip()
    val = int(re.search(r"throttled=(0x\d+)", env_output).groups()[0], 16)
    env = {
        "under-voltage": bool(val & 0x01),
        "freq-capped": bool(val & 0x02),
        "throttled": bool(val & 0x04)
    }

    if not config.get('Detection', 'HideEnvWarnings'):
        for key, value in env.items():
            if value and not key in overlay_processes:
                count += 1
                cmd = pngview_call(x_pos(count), Y_POS, icons[key], alpha)
                overlay_processes[key] = subprocess.Popen(cmd)
            elif not value:
                kill_overlay_process(key)

    return val

def check_process(process):
    """Check to see if process is already running."""
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if process.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def kill_overlay_process(device):
    """Kill process for specific icon type."""
    if device in overlay_processes:
        overlay_processes[device].kill()
        del overlay_processes[device]

def interrupt_shutdown(channel):
    """Shutdown system if interrupt activated."""
    if channel == int(config['BatteryLDO']['GPIO']):
        if GPIO.input(channel) != config.getboolean('BatteryLDO', 'ActiveLow'):
            shutdown(True)
        else:
            shutdown(False)
    elif channel == int(config['ShutdownGPIO']['GPIO']):
        if GPIO.input(channel) != config.getboolean('ShutdownGPIO', 'ActiveLow'):
            time.sleep(1)
            if GPIO.input(channel) != config.getboolean('ShutdownGPIO', 'ActiveLow'):
                my_logger.warning("Shutdown button pressed, shutting down now.")
                os.system("sudo shutdown -P now")
            else:
                my_logger.info("Shutdown button pressed, but not long enough to trigger Shutdown.")

def shutdown(low_voltage):
    """Shutdown system if low voltage, otherwise abort shutdown."""
    kill_overlay_process("caution")
    if low_voltage:
        my_logger.warning("Low Battery. Initiating shutdown in 60 seconds.")
        x = int(resolution[0]) / 2 - 60
        y = int(resolution[1]) / 2 - 60
        cmd = pngview_call(x, y, icons["battery_critical_shutdown"])
        overlay_processes["caution"] = subprocess.Popen(cmd)
        os.system("sudo shutdown -P +1")
    else:
        os.system("sudo shutdown -c")
        my_logger.info("Power Restored, shutdown aborted.")

GPIO.setmode(GPIO.BCM)
if config.getboolean('Detection', 'BatteryLDO'):
    LDO_GPIO = config['BatteryLDO']['GPIO']
    my_logger.info("LDO Active on GPIO %s", LDO_GPIO)
    GPIO.setup(int(LDO_GPIO), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(int(LDO_GPIO), GPIO.BOTH, callback=interrupt_shutdown, bouncetime=500)

if config.getboolean('Detection', 'ShutdownGPIO'):
    SD_GPIO = config['ShutdownGPIO']['GPIO']
    my_logger.info("Shutdown button on GPIO %s", SD_GPIO)
    GPIO.setup(int(SD_GPIO), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(int(SD_GPIO), GPIO.BOTH, callback=interrupt_shutdown, bouncetime=200)

overlay_processes = {}
wifi_state = None
bt_state = None
audio_state = None
battery_state = None
env = None
ingame = None
value_v = None
audio_volume = 0
shutdown_pending = False

if config.getboolean('Detection', 'BatteryADC'):
    bat = battery.Battery(config)

# Main Loop
while True:
    count = 0

    # Check if retroarch is running
    new_ingame = check_process('retroarch')

    if new_ingame:
        alpha = config['Detection']['InGameAlpha']
    else:
        alpha = "255"

    log = str(datetime.now())

    # Battery Icon
    if config.getboolean('Detection', 'BatteryADC'):
        count += 1
        (new_battery_state, value_v) = bat.get_state()

        if new_battery_state != battery_state or new_ingame != ingame:
            kill_overlay_process("bat")

            bat_icon_path = (ICON_PATH + "ic_battery_" + new_battery_state +
                            "_black_" + ICON_SIZE + "dp.png")
            if new_battery_state == "alert_red":
                bat_icon_path = ICON_PATH + "battery-alert_" + ICON_SIZE + ".png"
            cmd = pngview_call(x_pos(count), Y_POS, bat_icon_path, alpha)
            overlay_processes["bat"] = subprocess.Popen(cmd)

            battery_state = new_battery_state

            if config.getboolean('Detection', 'ADCShutdown'):
                if shutdown_pending and value_v > config.getfloat("Detection", "VMinCharging"):
                    shutdown(False)
                    shutdown_pending = False
                elif value_v < config.getfloat("Detection", "VMinDischarging"):
                    shutdown(True)
                    shutdown_pending = True

        log = log + f', battery: {value_v:.2f} {battery_state}%'

    # Wifi Icon
    if config.getboolean('Detection', 'Wifi'):
        count += 1
        (new_wifi_state, wifi_quality) = wifi.get_state()
        if new_wifi_state != wifi_state or new_ingame != ingame:
            kill_overlay_process("wifi")
            cmd = pngview_call(x_pos(count), Y_POS, icons[new_wifi_state], alpha)
            overlay_processes["wifi"] = subprocess.Popen(cmd)
            wifi_state = new_wifi_state
        log = log + f', wifi: {wifi_state} {wifi_quality}%'

    # Bluetooth Icon
    if config.getboolean('Detection', 'Bluetooth'):
        count += 1
        new_bt_state = bluetooth.get_state()
        if new_bt_state != bt_state or new_ingame != ingame:
            kill_overlay_process("bt")
            cmd = pngview_call(x_pos(count), Y_POS, icons[new_bt_state], alpha)
            overlay_processes["bt"] = subprocess.Popen(cmd)
            bt_state = new_bt_state
        log = log + f', bt: {bt_state}'

    # Audio Icon
    if config.getboolean('Detection', 'Audio'):
        count += 1
        (new_audio_state, audio_volume) = audio.get_state()
        if new_audio_state != audio_state or new_ingame != ingame:
            kill_overlay_process("audio")
            cmd = pngview_call(x_pos(count), Y_POS, icons[new_audio_state], alpha)
            overlay_processes["audio"] = subprocess.Popen(cmd)
            audio_state = new_audio_state
        log = log + f', Audio: {audio_state} {audio_volume}%'

    env = environment()
    my_logger.info(log + f', throttle: 0x{env}')

    ingame = new_ingame
    time.sleep(5)
