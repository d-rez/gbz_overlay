"""Audio device for retropie-status-overlay
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import subprocess

NAME = "Audio"
AUDIO_CMD = "amixer"

def add_icons(icons, iconpath, size):
    """Add audio specific icons."""
    icons['volume_0'] = iconpath + "ic_volume_mute_black_" + size + "dp.png"
    icons['volume_1'] = iconpath + "ic_volume_down_black_" + size + "dp.png"
    icons['volume_2'] = iconpath + "ic_volume_up_black_" + size + "dp.png"
    icons['volume_mute'] = iconpath + "ic_volume_off_black_"  + size + "dp.png"

def get_state():
    """Get state of audio device."""
    audio_state = "volume_mute"
    audio_volume = 0
    try:
        with subprocess.Popen(AUDIO_CMD, stdout=subprocess.PIPE) as proc:
            for line in proc.stdout:
                if b'[' in line:
                    audio_volume = int(line.split(b"[")[1].split(b"%")[0])
                    if line.split(b"[")[3].split(b"]")[0] == b"on":
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
