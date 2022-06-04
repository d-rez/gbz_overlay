"""Unit tests for overlay.py
github.com/bverc/retropie-status-overlay

Author: bverc
"""

import unittest
import subprocess
import os
from unittest.mock import Mock

import overlay

overlay.GPIO = Mock()
overlay.GPIO.input = Mock()

class TestOverlay(unittest.TestCase):
    """A Class used to test overlay module."""

    def test_pngview(self):
        """Test pngview adds to overlay_processes by checking key was added."""
        overlay.PNGVIEW_PATH = "echo"
        self.assertFalse("test1" in overlay.overlay_processes)
        overlay.pngview("test1", 0, 0, overlay.icons["under-voltage"])
        self.assertTrue("test1" in overlay.overlay_processes)
        overlay.overlay_processes["test1"].kill()

        self.assertFalse("test2" in overlay.overlay_processes)
        overlay.pngview("test2", 0, 0, overlay.icons["under-voltage"],0)
        self.assertTrue("test2" in overlay.overlay_processes)
        overlay.overlay_processes["test2"].kill()

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

    def test_shutdown_abort_shutdown(self):
        """Start a shutdown then abort, check icon has been added then removed."""
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.shutdown()
        self.assertTrue("caution" in overlay.overlay_processes)
        overlay.abort_shutdown()
        self.assertFalse("caution" in overlay.overlay_processes)

    def test_get_alpha(self):
        """Test get_alpha() with different game states."""
        overlay.config['Detection']['InGameAlpha'] = "255"
        self.assertTrue(overlay.get_alpha(False) == "255")
        self.assertTrue(overlay.get_alpha(True) == "255")

        overlay.config['Detection']['InGameAlpha'] = "100"
        self.assertTrue(overlay.get_alpha(False) == "255")
        self.assertTrue(overlay.get_alpha(True) == "100")

    def test_adc_shutdown(self):
        """Test adc_shutdown() with various voltages and pending shutdown states."""
        overlay.PNGVIEW_PATH = "echo"
        overlay.config['Detection']['VMinCharging'] = "4"
        overlay.config['Detection']['VMinDischarging'] = "3.2"

        # Voltage below minimum discharging voltage, expect always True
        self.assertTrue(overlay.adc_shutdown(True, 3.0))
        self.assertTrue(overlay.adc_shutdown(False, 3.0))

        # Voltage above minimum discharging voltage, expect match input
        self.assertTrue(overlay.adc_shutdown(True, 3.5))
        self.assertFalse(overlay.adc_shutdown(False, 3.5))

        # Voltage above minimum charging voltage, expect always False
        self.assertFalse(overlay.adc_shutdown(True, 4.1))
        self.assertFalse(overlay.adc_shutdown(False, 4.1))

        # Abort any pending shutdown
        os.system("sudo shutdown -c")

    def test_interrupt_shutdown_rising(self):
        """Test interrupt_shutdown() with rising edge GPIO."""
        overlay.GPIO.input.return_value = True

        # GPIO Rising Edge Interrupt
        overlay.config['BatteryLDO']['GPIO'] = "1"
        overlay.config['ShutdownGPIO']['GPIO'] = "2"

        # BatteryLDO, ActiveLow, GPIO High, no shutdown
        overlay.config['BatteryLDO']['ActiveLow'] = "True"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(1)
        self.assertFalse("caution" in overlay.overlay_processes)

        # BatteryLDO, ActiveHigh, GPIO High, Shutdown
        overlay.config['BatteryLDO']['ActiveLow'] = "False"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(1)
        self.assertTrue("caution" in overlay.overlay_processes)
        overlay.abort_shutdown()

        # ShutdownGPIO, ActiveLow, GPIO High, no shutdown
        overlay.config['ShutdownGPIO']['ActiveLow'] = "True"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(2)
        self.assertFalse("caution" in overlay.overlay_processes)

        # Cannot test ShutdownGPIO, ActiveHigh, GPIO High, as will cause immediate shutdown

        # Abort any pending shutdown
        os.system("sudo shutdown -c")

    def test_interrupt_shutdown_falling(self):
        """Test interrupt_shutdown() with falling edge GPIO."""
        overlay.GPIO.input.return_value = False

        # GPIO Falling Edge Interrupt
        overlay.config['BatteryLDO']['GPIO'] = "11"
        overlay.config['ShutdownGPIO']['GPIO'] = "12"

        # BatteryLDO, ActiveLow, GPIO Low, Shutdown
        overlay.config['BatteryLDO']['ActiveLow'] = "True"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(11)
        self.assertTrue("caution" in overlay.overlay_processes)
        overlay.abort_shutdown()

        # BatteryLDO, ActiveHigh, GPIO Low, no shutdown
        overlay.config['BatteryLDO']['ActiveLow'] = "False"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(11)
        self.assertFalse("caution" in overlay.overlay_processes)

        # ShutdownGPIO, ActiveHigh, GPIO Low, no shutdown
        overlay.config['ShutdownGPIO']['ActiveLow'] = "False"
        self.assertFalse("caution" in overlay.overlay_processes)
        overlay.interrupt_shutdown(12)
        self.assertFalse("caution" in overlay.overlay_processes)

        # Cannot test ShutdownGPIO, ActiveLow, GPIO Low, as will cause immediate shutdown

        # Abort any pending shutdown
        os.system("sudo shutdown -c")

    def test_update_device_icon(self):
        """Test update_device_icon() with mock data."""
        overlay.PNGVIEW_PATH = "echo"
        overlay.icons = {
            "state1": "state1.png",
            "state2": "state2.png",
        }

        # Create mock device
        device = Mock()
        device.NAME = "DeviceName"
        device.get_state.return_value = "state1", "info"

        states = {"DeviceName": "state1", "ingame": False}

        # State unchanged, ingame unchanged
        info = overlay.update_device_icon(1, device, states, False, 255)
        self.assertTrue(info == "info")
        self.assertFalse("DeviceName" in overlay.overlay_processes)

        # State unchanged, ingame changed
        info = overlay.update_device_icon(1, device, states, True, 255)
        self.assertTrue(info == "info")
        self.assertTrue("state1.png" in overlay.overlay_processes["DeviceName"].args)

        # State changed, ingame unchanged
        device.get_state.return_value = "state2", "new_info"
        info = overlay.update_device_icon(1, device, states, True, 255)
        self.assertTrue(info == "new_info")
        self.assertTrue("state2.png" in overlay.overlay_processes["DeviceName"].args)

        # Kill process
        overlay.kill_overlay_process("DeviceName")

    def test_update_env_icons(self):
        """Test update_env_icons() with mock data."""
        overlay.PNGVIEW_PATH = "echo"
        overlay.environment = Mock()
        overlay.icons = {
            "under-voltage": "flash.png",
            "freq-capped": "thermometer.png",
            "throttled": "thermometer-lines.png"
        }

        # Normal Environment
        overlay.environment.return_value = {
            "under-voltage": False,
            "freq-capped": False,
            "throttled": False
        }
        self.assertEqual(overlay.update_env_icons(1, 255), "normal")

        # Under voltage
        overlay.environment.return_value = {
            "under-voltage": True,
            "freq-capped": False,
            "throttled": False
        }
        self.assertEqual(overlay.update_env_icons(1, 255), "under-voltage")

        # Frequency capped
        overlay.environment.return_value = {
            "under-voltage": False,
            "freq-capped": True,
            "throttled": False
        }
        self.assertEqual(overlay.update_env_icons(1, 255), "freq-capped")

        # Throttled
        overlay.environment.return_value = {
            "under-voltage": False,
            "freq-capped": False,
            "throttled": True
        }
        self.assertEqual(overlay.update_env_icons(1, 255), "throttled")

if __name__ == '__main__':
    unittest.main()
