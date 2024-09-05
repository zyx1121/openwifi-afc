import argparse
import logging
import queue
import sys
import threading
import time
import tomli as tomllib

from openwifi_afc.afc import AfcConnectionHandler
from openwifi_afc.openwifi import OpenwifiController


def setup_logging(log_file=None):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def afc_request_loop(afc, openwifi, logger, command_queue):
    while True:
        try:
            command = command_queue.get_nowait()
            if command.startswith("set"):
                logger.info(f"Setting channel to {command}")
                _, channel = command.split()

                afc_request = afc.generate_request([], [131])
                logger.info(f"Sending AFC request: {afc_request}")
                afc.send_request(afc_request)
                response = afc.get_response()
                logger.info(f"Received AFC response: {response}")
                available_channels = afc.parse_response(response)
                logger.info(f"Available channels: {available_channels}")
                if available_channels:
                    mapped_channel = openwifi.channel_mapping(int(channel))
                    logger.info(f"Mapped channel: {mapped_channel}")
                    openwifi.set_channel(mapped_channel)
                    logger.info(f"Set channel: {mapped_channel}")
                else:
                    logger.warning("No available 6GHz channel, switching to 2.4GHz/5GHz")
                    openwifi.switch_to_legacy_band()

        except queue.Empty:
            pass


def user_input_loop(command_queue, logger):
    while True:
        command = input("openwifi-afc> ")
        command_queue.put(command)


def main(log_file, config_file):
    logger = setup_logging(log_file)
    logger.info("Hello, Open WiFi AFC Project!")

    try:
        with open(config_file, "rb") as file:
            config = tomllib.load(file)
    except FileNotFoundError:
        logger.error(f"Config file {config_file} not found")
        sys.exit(1)

    afc = AfcConnectionHandler(config)
    openwifi = OpenwifiController()

    try:
        afc_request = afc.generate_request([], [131])

        logger.info(f"AFC request: {afc_request}")
        logger.info("Sending AFC request")
        afc.send_request(afc_request)
        logger.info("AFC request sent successfully")

        response = afc.get_response()
        logger.info(f"Received AFC response: {response}")

        available_channels = afc.parse_response(response)
        logger.info(f"Available channels: {available_channels}")

        if available_channels:
            selected_channel = select_best_channel(available_channels)
            logger.info(f"Selected channel: {selected_channel}")
            mapped_channel = openwifi.channel_mapping(selected_channel)
            logger.info(f"Mapped channel: {mapped_channel}")
            openwifi.set_channel(mapped_channel)
            logger.info(f"Set channel: {mapped_channel}")
        else:
            logger.warning("No available 6GHz channel, switching to 2.4GHz/5GHz")
            openwifi.switch_to_legacy_band()

    except ConnectionError:
        logger.error("Failed to connect to AFC server, switching to 2.4GHz/5GHz")
        openwifi.switch_to_legacy_band()

    except Exception as e:
        logger.error(f"An error occurred: {e}")

    command_queue = queue.Queue()

    # Start AFC request loop
    afc_thread = threading.Thread(target=afc_request_loop, args=(afc, openwifi, logger, command_queue))
    afc_thread.daemon = True
    afc_thread.start()

    # Start user input loop
    input_thread = threading.Thread(target=user_input_loop, args=(command_queue, logger))
    input_thread.daemon = True
    input_thread.start()

    try:
        # Keep the main thread running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Program interrupted by user. Exiting...")

    finally:
        logger.info("Shutdown complete.")


def select_best_channel(available_channels):
    return available_channels[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open WiFi AFC Project")
    parser.add_argument("-l", "--logfile", type=str, help="log file path", default=None)
    parser.add_argument("-c", "--config", type=str, help="config file path", default="afc.toml")

    args = parser.parse_args()

    main(args.logfile, args.config)
