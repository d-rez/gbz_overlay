# Wifi device for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# Authors: bverc, d-rez

import subprocess

WIFI_CARRIER = "/sys/class/net/wlan0/carrier" # 1 when wifi connected, 0 when disconnected and/or ifdown
WIFI_LINKMODE = "/sys/class/net/wlan0/link_mode" # 1 when ifup, 0 when ifdown

def icons(icons, iconpath, size):
    icons['wifi_4'] = iconpath + "ic_signal_wifi_4_bar_black_" + size + "dp.png"
    icons['wifi_3'] = iconpath + "ic_signal_wifi_3_bar_black_" + size + "dp.png"
    icons['wifi_2'] = iconpath + "ic_signal_wifi_2_bar_black_" + size + "dp.png"
    icons['wifi_1'] = iconpath + "ic_signal_wifi_1_bar_black_" + size + "dp.png"
    icons['wifi_0'] = iconpath + "ic_signal_wifi_0_bar_black_" + size + "dp.png"
    icons['wifi_off'] = iconpath + "ic_signal_wifi_off_black_" + size + "dp.png"

def get_state():
    wifi_state = "wifi_off"
    wifi_quality = 0
    try:
        f = open(WIFI_CARRIER, "r")
        carrier_state = int(f.read().rstrip())
        f.close()
        if carrier_state == 1:
            # ifup and connected to AP
            wifi_state = "wifi_4"
            # get wifi quality
            cmd = subprocess.Popen(["iwconfig", "wlan0"], stdout=subprocess.PIPE)
            for line in cmd.stdout:
                if b'Link Quality' in line:
                    x = line.split()[1].split(b"=")[1].split(b"/")
                    wifi_quality = int(100*int(x[0])/int(x[1]))
                    if wifi_quality < 20:
                        wifi_state = "wifi_0"
                    elif wifi_quality < 40:
                        wifi_state = "wifi_1"
                    elif wifi_quality < 60:
                        wifi_state = "wifi_2"
                    elif wifi_quality < 80:
                        wifi_state = "wifi_3"
                    else:
                        wifi_state = "wifi_4"
        elif carrier_state == 0:
            f = open(WIFI_LINKMODE, "r")
            linkmode_state = int(f.read().rstrip())
            f.close()
            if linkmode_state == 1:
                # ifup but not connected to any network
                wifi_state = "wifi_0"
                # else - must be ifdown

    except IOError:
        pass

    return wifi_state, wifi_quality
