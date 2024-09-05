import logging
import subprocess


VALID_2G_CHANNELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
VALID_5G_CHANNELS = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
CFI_6G = [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93, 97]


class OpenwifiController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def restart_ap(self):
        try:
            subprocess.run(["/root/openwifi/fosdem.sh"], check=True)
            self.logger.info("Restart AP success")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Restart AP error: {e}")

    def channel_mapping(self, channel):
        if channel in CFI_6G:
            return VALID_5G_CHANNELS[CFI_6G.index(channel)]
        else:
            return None

    def set_channel(self, channel):
        CONFIG_FILE = "/root/openwifi/hostapd-openwifi.conf"

        try:
            with open(CONFIG_FILE, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if line.startswith("hw_mode="):
                    lines[i] = f"hw_mode=a\n"
                elif line.startswith("channel="):
                    lines[i] = f"channel={channel}\n"

            with open(CONFIG_FILE, "w") as f:
                f.writelines(lines)

            self.logger.info(f"Successfully set channel to {channel} and hw_mode to a")

        except IOError as e:
            self.logger.error(f"Modify config file error: {e}")

        self.restart_ap()

    def switch_to_legacy_band(self):
        CONFIG_FILE = "/root/openwifi/hostapd-openwifi.conf"

        try:
            with open(CONFIG_FILE, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if line.startswith("hw_mode="):
                    lines[i] = f"hw_mode=g\n"
                elif line.startswith("channel="):
                    lines[i] = f"channel=1\n"

            with open(CONFIG_FILE, "w") as f:
                f.writelines(lines)

            self.logger.info(f"Successfully set channel to 1 and hw_mode to g")

        except IOError as e:
            self.logger.error(f"Modify config file error: {e}")

        self.restart_ap()
