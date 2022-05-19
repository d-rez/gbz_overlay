# Audio device for retropie-status-overlay
# github.com/bverc/retropie-status-overlay
#
# Author: bverc

import subprocess

def icons(icons, iconpath, size):
    icons['volume_0'] = iconpath + "ic_volume_mute_black_" + size + "dp.png"
    icons['volume_1'] = iconpath + "ic_volume_down_black_" + size + "dp.png"
    icons['volume_2'] = iconpath + "ic_volume_up_black_" + size + "dp.png"
    icons['volume_mute'] = iconpath + "ic_volume_off_black_"  + size + "dp.png"

def getstate():
    audio_state = "volume_mute"
    try:
        cmd = subprocess.Popen('amixer', stdout=subprocess.PIPE)
        for line in cmd.stdout:
            if b'[' in line:
                if line.split(b"[")[3].split(b"]")[0] == b"on":
                    audio_volume = int(line.split(b"[")[1].split(b"%")[0])
                    if audio_volume == 0:
                        audio_state = "volume_0"
                    elif audio_volume < 50:
                        audio_state = "volume_1"
                    else:
                        audio_state = "volume_2"
                break

    except IOError:
        pass

    return audio_state, audio_volume
