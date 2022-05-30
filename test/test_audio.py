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
        """Test audio.get_state()"""
        # This will cause subprocess to call amixer, which could return anything
        (audio_state, audio_volume) = audio.get_state()
        self.assertTrue(audio_state in ("volume_0", "volume_1", "volume_2", "volume_mute"))
        self.assertTrue(0 <= audio_volume <= 100)

if __name__ == '__main__':
    unittest.main()
