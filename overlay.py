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
try:
    from RPi import GPIO
except RuntimeError:
    print("This module can only be run on a Raspberry Pi!")
    print("Proceeding, as likely a unit test.")

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
try:
    FB_OUTPUT = subprocess.check_output(FB_FILE.split()).decode().rstrip()
    resolution = re.search(r"(\d{3,}x\d{3,})", FB_OUTPUT).group().split('x')
except FileNotFoundError:
    resolution = ['1920', '1080'] # Default to 1080p if unable to check
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
for module in [wifi, bluetooth, audio, battery]:
    module.add_icons(icons, ICON_PATH, ICON_SIZE)

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
            shutdown()
        else:
            abort_shutdown()
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

def adc_shutdown(shutdown_pending, voltage):
    """Check if battery voltage should trigger a shutdown or recover a pending shutdown."""
    if shutdown_pending and voltage > config.getfloat("Detection", "VMinCharging"):
        abort_shutdown()
        shutdown_pending = False
    elif voltage < config.getfloat("Detection", "VMinDischarging"):
        shutdown()
        shutdown_pending = True
    return shutdown_pending

def get_alpha(ingame):
    """Get alpha value if in game, otherwise max."""
    if ingame:
        return config['Detection']['InGameAlpha']
    return "255"

def setup_interrupts():
    """setup interrupts for shutdown."""
    GPIO.setmode(GPIO.BCM)
    for interrupt in ['BatteryLDO', 'ShutdownGPIO']:
        if config.getboolean('Detection', interrupt):
            channel = config[interrupt]['GPIO']
            my_logger.info("%s active on GPIO %s", interrupt, channel)
            GPIO.setup(int(channel), GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(int(channel), GPIO.BOTH, callback=interrupt_shutdown,
                                  bouncetime=500)

def update_device_icon(count, device, states, new_ingame, alpha):
    """Check if device states hav changed; if so, update icons."""
    (new_state, info) = device.get_state()
    if new_state != states[device.NAME] or new_ingame != states["ingame"]:
        pngview(device.NAME, get_x_pos(count), Y_POS, icons[new_state], alpha)
        states[device.NAME] = new_state
    return info

def update_env_icons(count, alpha):
    """Check environment status, and display any relevant icons."""
    env = environment()
    env_text = 'normal'
    for key, value in env.items():
        if value:
            env_text = key
            if not key in overlay_processes:
                count += 1
                pngview(key, get_x_pos(count), Y_POS, icons[key], alpha)
        else:
            kill_overlay_process(key)
    return env_text

overlay_processes = {}

def main():
    """ Main Function."""
    states = {"Wifi": None, "Bluetooth": None, "Audio": None, "BatteryADC": None, "ingame": None}
    devices = [wifi, bluetooth, audio]
    if config.getboolean('Detection', 'BatteryADC'):
        bat = battery.Battery(config)
        devices.append(bat)
    shutdown_pending = False
    setup_interrupts()

    # Main Loop
    while True:
        count = 0
        log = str(datetime.now())

        # Check if retroarch is running then set alpha
        new_ingame = check_process('retroarch')
        alpha = get_alpha(new_ingame)

        # Device Icons
        for device in devices:
            if config.getboolean('Detection', device.NAME):
                count += 1
                info = update_device_icon(count, device, states, new_ingame, alpha)
                log = log + f', {device.NAME}: {states[device.NAME]} {info}'
                if device.NAME == "BatteryADC" and config.getboolean('Detection', 'ADCShutdown'):
                    shutdown_pending = adc_shutdown(shutdown_pending, info)

        # Enviroment Icons
        if not config.getboolean('Detection', 'HideEnvWarnings'):
            env_text = update_env_icons(count, alpha)
            log = log + f', environment: {env_text}'

        my_logger.info(log)
        states["ingame"] = new_ingame
        time.sleep(5)

if __name__ == "__main__":
    main()
