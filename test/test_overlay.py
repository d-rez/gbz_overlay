"""Unit tests for overlay.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
import subprocess
import time
import os

import overlay

class TestOverlay(unittest.TestCase):
    """A Class used to test overlay module."""

    def test_pngview(self):
        """Test pngview adds to overlay_processes by checking key was added."""
        overlay.PNGVIEW_PATH = "echo"
        overlay.pngview("test1", 0, 0, overlay.icons["under-voltage"])
        self.assertTrue("test1" in overlay.overlay_processes)
        overlay.overlay_processes["test1"].kill()
        self.assertFalse("test2" in overlay.overlay_processes)

    def test_kill_overlay_process(self):
        """Test kill_overlay_process() by checking key is removed from overlay_processes."""
        overlay.overlay_processes["test3"] = subprocess.Popen("top") # pylint: disable=consider-using-with
        self.assertTrue("test3" in overlay.overlay_processes)
        overlay.kill_overlay_process("test3")
        self.assertFalse("test3" in overlay.overlay_processes)
        # Test raises an unexpected ResourceWarning, but test passes

    def test_get_x_pos_left(self):
        """Test get_x_pos() function from left side."""
        overlay.ICON_PADDING = "8"
        overlay.ICON_SIZE = "48"
        overlay.resolution[0] = "1920"
        overlay.config['Icons']['Horizontal'] = "left"
        count = 1
        self.assertTrue(overlay.get_x_pos(count) == 8) # 8
        count = 2
        self.assertTrue(overlay.get_x_pos(count) == 64) # 8+48+8
        count = 7
        self.assertTrue(overlay.get_x_pos(count) == 344) # ((8+48)*6)+8

    def test_get_x_pos_right(self):
        """Test get_x_pos() function from right side."""
        overlay.ICON_PADDING = "4"
        overlay.ICON_SIZE = "24"
        overlay.resolution[0] = "480"
        overlay.config['Icons']['Horizontal'] = "right"
        count = 1
        self.assertTrue(overlay.get_x_pos(count) == 452) # 480-(4+24)
        count = 2
        self.assertTrue(overlay.get_x_pos(count) == 424) # 480-2*(4+24)
        count = 7
        self.assertTrue(overlay.get_x_pos(count) == 284) # 480-7*(4+24)

    def test_environment_normal(self):
        """Test environment() function in normal operation."""
        overlay.ENV_CMD = "echo throttled=0x0"
        env = overlay.environment()
        self.assertFalse(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertFalse(env["throttled"])

    def test_environment_throttled(self):
        """Test environment() function in while throttled."""
        overlay.ENV_CMD = "echo throttled=0x4"
        env = overlay.environment()
        self.assertFalse(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertTrue(env["throttled"])

        overlay.ENV_CMD = "echo throttled=0x40004"
        env = overlay.environment()
        self.assertFalse(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertTrue(env["throttled"])

    def test_environment_throttled_under_voltage(self):
        """Test environment() function in while throttled and under voltage."""
        overlay.ENV_CMD = "echo throttled=0x5"
        env = overlay.environment()
        self.assertTrue(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertTrue(env["throttled"])

        overlay.ENV_CMD = "echo throttled=0x50005"
        env = overlay.environment()
        self.assertTrue(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertTrue(env["throttled"])

    def test_environment_freq_capped(self):
        """Test environment() function in while frequency capped."""
        overlay.ENV_CMD = "echo throttled=0x2"
        env = overlay.environment()
        self.assertFalse(env["under-voltage"])
        self.assertTrue(env["freq-capped"])
        self.assertFalse(env["throttled"])

        overlay.ENV_CMD = "echo throttled=0x20002"
        env = overlay.environment()
        self.assertFalse(env["under-voltage"])
        self.assertTrue(env["freq-capped"])
        self.assertFalse(env["throttled"])

    def test_environment_under_voltage(self):
        """Test environment() function in while under voltage."""
        overlay.ENV_CMD = "echo throttled=0x1"
        env = overlay.environment()
        self.assertTrue(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertFalse(env["throttled"])

        overlay.ENV_CMD = "echo throttled=0x10001"
        env = overlay.environment()
        self.assertTrue(env["under-voltage"])
        self.assertFalse(env["freq-capped"])
        self.assertFalse(env["throttled"])

    def test_check_process(self):
        """Test check_process() with various processes names."""
        # process abcdefg should not exist
        self.assertFalse(overlay.check_process("abcdefg"))
        # process systemd should be running
        self.assertTrue(overlay.check_process("systemd"))
        # process python should be running
        self.assertTrue(overlay.check_process("python"))

    def test_abort_shutdown(self):
        """Abort a pending shutdown, then check system still responds 60 seconds later."""
        os.system("sudo shutdown -P +1")
        time.sleep(30)
        overlay.abort_shutdown()
        time.sleep(31)
        # Must be True if system has not shutdown
        self.assertTrue(True) # pylint: disable=redundant-unittest-assert

if __name__ == '__main__':
    unittest.main()
