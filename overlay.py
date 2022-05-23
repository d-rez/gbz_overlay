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

def pngview(device, x_pos, y_pos, icon_path, alpha=255):
    """Call pngview from binary location."""
    call = [PNGVIEW_PATH, "-d", "0", "-b", "0x0000",
            "-n", "-l", "15000", "-y", str(y_pos), "-x", str(x_pos)]
    if int(alpha) < 255:
        call += ["-a", str(alpha)]
    call += [icon_path]
    kill_overlay_process(device)
    overlay_processes[device] = subprocess.Popen(call) # pylint: disable=consider-using-with

icons = {
    "under-voltage": ICON_PATH + "flash_" + ICON_SIZE + ".png",
    "freq-capped": ICON_PATH + "thermometer_" + ICON_SIZE + ".png",
    "throttled": ICON_PATH + "thermometer-lines_" + ICON_SIZE + ".png",
}
wifi.add_icons(icons, ICON_PATH, ICON_SIZE)
bluetooth.add_icons(icons, ICON_PATH, ICON_SIZE)
audio.add_icons(icons, ICON_PATH, ICON_SIZE)
battery.add_icons(icons, ICON_PATH)

ENV_CMD = "vcgencmd get_throttled"

def get_x_pos(count):
    """Return x position for next icon based on number or icons already displayed."""
    if config['Icons']['Horizontal'] == "right":
        return int(resolution[0]) - (int(ICON_SIZE) + int(ICON_PADDING)) * count
    return int(ICON_PADDING) + (int(ICON_SIZE) + int(ICON_PADDING)) * (count - 1)

def environment():
    """Return state of environment, such as unndervoltage or throttled."""
    env_output = subprocess.check_output(ENV_CMD.split()).decode().rstrip()
    val = int(re.search(r"throttled=(0x\d+)", env_output).groups()[0], 16)
    env = {
        "under-voltage": bool(val & 0x01),
        "freq-capped": bool(val & 0x02),
        "throttled": bool(val & 0x04)
    }
    return env

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

def shutdown():
    """Shutdown system in 60 seconds."""
    my_logger.warning("Low Battery. Initiating shutdown in 60 seconds.")
    x_pos = int(resolution[0]) / 2 - 60
    y_pos = int(resolution[1]) / 2 - 60
    pngview("caution", x_pos, y_pos, icons["battery_critical_shutdown"])
    os.system("sudo shutdown -P +1")

def abort_shutdown():
    """Abort pending shutdown."""
    os.system("sudo shutdown -c")
    kill_overlay_process("caution")
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

if config.getboolean('Detection', 'BatteryADC'):
    bat = battery.Battery(config)

def main(): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    """ Main Function."""
    states = {"wifi": None, "bt": None, "bat": None, "audio": None, "ingame": None}
    shutdown_pending = False

    # Main Loop
    while True:
        count = 0

        # Check if retroarch is running then set alpha
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

            if new_battery_state != states["bat"] or new_ingame != states["ingame"]:
                bat_icon_path = (ICON_PATH + "ic_battery_" + new_battery_state +
                                "_black_" + ICON_SIZE + "dp.png")
                if new_battery_state == "alert_red":
                    bat_icon_path = ICON_PATH + "battery-alert_" + ICON_SIZE + ".png"
                pngview("bat", get_x_pos(count), Y_POS, bat_icon_path, alpha)
                states["bat"] = new_battery_state

                if config.getboolean('Detection', 'ADCShutdown'):
                    if shutdown_pending and value_v > config.getfloat("Detection", "VMinCharging"):
                        abort_shutdown()
                        shutdown_pending = False
                    elif value_v < config.getfloat("Detection", "VMinDischarging"):
                        shutdown()
                        shutdown_pending = True

            log = log + f', battery: {value_v:.2f} {states["bat"]}%'

        # Wifi Icon
        if config.getboolean('Detection', 'Wifi'):
            count += 1
            (new_wifi_state, wifi_quality) = wifi.get_state()
            if new_wifi_state != states["wifi"] or new_ingame != states["ingame"]:
                pngview("wifi", get_x_pos(count), Y_POS, icons[new_wifi_state], alpha)
                states["wifi"] = new_wifi_state
            log = log + f', wifi: {states["wifi"]} {wifi_quality}%'

        # Bluetooth Icon
        if config.getboolean('Detection', 'Bluetooth'):
            count += 1
            new_bt_state = bluetooth.get_state()
            if new_bt_state != states["bt"] or new_ingame != states["ingame"]:
                pngview("bt", get_x_pos(count), Y_POS, icons[new_bt_state], alpha)
                states["bt"] = new_bt_state
            log = log + f', bt: {states["bt"]}'

        # Audio Icon
        if config.getboolean('Detection', 'Audio'):
            count += 1
            (new_audio_state, audio_volume) = audio.get_state()
            if new_audio_state != states["audio"] or new_ingame != states["ingame"]:
                pngview("audio", get_x_pos(count), Y_POS, icons[new_audio_state], alpha)
                states["audio"] = new_audio_state
            log = log + f', Audio: {states["audio"]} {audio_volume}%'

        # Enviroment Icons
        if not config.getboolean('Detection', 'HideEnvWarnings'):
            env = environment()
            env_text = 'normal'
            for key, value in env.items():
                if value:
                    env_text = key
                    if not key in overlay_processes:
                        count += 1
                        pngview(key, get_x_pos(count), Y_POS, icons[key], alpha)
                elif not value:
                    kill_overlay_process(key)
            log = log + f', environment: {env_text}'

        my_logger.info(log)
        states["ingame"] = new_ingame
        time.sleep(5)

if __name__ == "__main__":
    main()
