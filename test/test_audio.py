"""Unit tests for audio.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest

from devices import audio

class TestAudio(unittest.TestCase):
    """A Class used to test Audio module."""

    def test_add_icons(self):
        """Setup empty dictionary and dummy icon_path and size, call function,
        then check dictionary length and content are correct"""
        icons = {}
        icon_size = "48"
        icon_path = "random_dir/"
        audio.add_icons(icons, icon_path, icon_size)
        self.assertTrue(len(icons.keys()) == 4)
        self.assertTrue(icons['volume_0'] == "random_dir/ic_volume_mute_black_48dp.png")
        self.assertTrue(icons['volume_1'] == "random_dir/ic_volume_down_black_48dp.png")
        self.assertTrue(icons['volume_2'] == "random_dir/ic_volume_up_black_48dp.png")
        self.assertTrue(icons['volume_mute'] == "random_dir/ic_volume_off_black_48dp.png")

    def test_get_state(self):
        """Test audio.get_state() by overriding amixer with different volumes."""
        audio.AUDIO_CMD = ["echo", "\n[100%] [0dB] [off]"]
        (audio_state, audio_volume) = audio.get_state()
        self.assertTrue(audio_state == "volume_mute")
        self.assertTrue(audio_volume == 100)

        audio.AUDIO_CMD = ["echo", "\n\n[0%] [0dB] [on]"]
        (audio_state, audio_volume) = audio.get_state()
        self.assertTrue(audio_state == "volume_0")
        self.assertTrue(audio_volume == 0)

        audio.AUDIO_CMD = ["echo", "\n[49%] [0dB] [on]"]
        (audio_state, audio_volume) = audio.get_state()
        self.assertTrue(audio_state == "volume_1")
        self.assertTrue(audio_volume == 49)

        audio.AUDIO_CMD = ["echo", "\n[50%] [0dB] [on]"]
        (audio_state, audio_volume) = audio.get_state()
        self.assertTrue(audio_state == "volume_2")
        self.assertTrue(audio_volume == 50)

if __name__ == '__main__':
    unittest.main()
