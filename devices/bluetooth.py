"""Bluetooth device for retropie-status-overlay
github.com/bverc/retropie-status-overlay

Authors: bverc, d-rez
"""

import subprocess
import os

BT_DEVICES_DIR = "/sys/class/bluetooth"

def add_icons(icons, iconpath, size):
    """Add Bluetooth specific icons."""
    icons['bt_enabled'] = iconpath + "ic_bluetooth_black_" + size + "dp.png"
    icons['bt_connected'] = iconpath + "ic_bluetooth_connected_black_" + size + "dp.png"
    icons['bt_disabled'] = iconpath + "ic_bluetooth_disabled_black_" + size + "dp.png"

def get_state():
    """Get state of Bluetooth device."""
    bt_state = "bt_disabled"
    try:
        with subprocess.Popen('hciconfig', stdout=subprocess.PIPE) as proc1:
            cmd = ['awk', 'FNR == 3 {print tolower($1)}']
            with subprocess.Popen(cmd, stdin=proc1.stdout, stdout=subprocess.PIPE) as proc2:
                state = proc2.communicate()[0].decode().rstrip()
        if state == "up":
            bt_state = "bt_enabled"
    except IOError:
        pass

    try:
        devices = os.listdir(BT_DEVICES_DIR)
        if len(devices) > 1:
            bt_state = "bt_connected"
    except OSError:
        pass

    return bt_state
