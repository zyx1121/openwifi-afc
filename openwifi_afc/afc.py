import logging
import tomli as tomllib
import uuid
from urllib.parse import urljoin, urlparse

import bs4
import requests

# Disable insecure request warning (Valid server certificate is covered via attestation)
requests.packages.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)


class AfcConnectionHandler:
    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.base_url = settings["connection"]["base_url"]
        self.method_url = settings["connection"]["method_url"]
        self.login_url = settings["connection"]["login_url"]
        self.timeout = settings["connection"]["timeout"]
        self.username = settings["account"]["username"]
        self.password = settings["account"]["password"]
        self._resp = None

    def _get_csrf_token(self):
        login_url = urljoin(self.base_url, self.login_url)
        session = requests.Session()
        self.logger.info(f"Getting CSRF token from {login_url}")
        response = session.get(login_url, verify=False)

        if response.status_code != 200:
            self.logger.error(f"Failed to get CSRF token, status code: {response.status_code}")
            return None, None

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        token_input = soup.find("input", {"id": "csrf_token"})
        if token_input:
            csrf_token = token_input.get("value")
            cookies = session.cookies.get_dict()
            self.logger.info("CSRF token retrieved successfully")
            return csrf_token, cookies
        else:
            self.logger.error("CSRF token not found in the response")
            return None, None

    def _login(self, csrf_token, cookies):
        login_url = urljoin(self.base_url, "user/sign-in")
        session = requests.Session()
        session.cookies.update(cookies)
        login_payload = {
            "username": self.username,
            "password": self.password,
            "csrf_token": csrf_token,
            "next": "/",
            "reg_next": "/",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": login_url,
            "Cookie": "; ".join([f"{key}={value}" for key, value in cookies.items()]),
        }
        self.logger.info(f"Logging in with username: {self.username}")
        response = session.post(login_url, data=login_payload, headers=headers, verify=False)

        if response.status_code != 200:
            self.logger.error(f"Login failed, status code: {response.status_code}")
            return None

        cookies = session.cookies.get_dict()
        self.logger.info("Login successful")
        return cookies

    def send_request(self, request_json):
        self._resp = None

        if urlparse(self.base_url).scheme != "https":
            self.logger.error("Non-https URLs are not permitted")
            raise ValueError("Non-https URLs are not permitted")

        csrf_token, cookies = self._get_csrf_token()
        if not csrf_token:
            self.logger.error("CSRF token retrieval failed")
            raise ValueError("CSRF token retrieval failed")

        login_cookies = self._login(csrf_token, cookies)
        if not login_cookies:
            self.logger.error("Login failed")
            raise ValueError("Login failed")

        cookies.update(login_cookies)

        headers = {"host": urlparse(self.base_url).hostname, "X-Csrf-Token": csrf_token, "Content-Type": "application/json"}

        self.logger.info(f"Sending request to {urljoin(self.base_url, self.method_url)}")
        self._resp = requests.post(
            urljoin(self.base_url, self.method_url), headers=headers, cookies=cookies, timeout=self.timeout, verify=False, json=request_json
        )

        if self._resp.status_code == 200:
            self.logger.info("Request sent successfully")
        else:
            self.logger.error(f"Request failed with status code: {self._resp.status_code}")

    def get_response(self):
        if self._resp is not None:
            self.logger.info("Getting response JSON")
            return self._resp.json()
        else:
            self.logger.error("No response available")
            return None

    def get_code(self):
        if self._resp is not None:
            self.logger.info(f"Getting response status code: {self._resp.status_code}")
            return self._resp.status_code
        else:
            self.logger.error("No response available")
            return None

    def generate_request(self, inquiredFrequencyRange, inquiredChannels):
        config = None

        with open("afc.toml", "rb") as f:
            config = tomllib.load(f)

        request_data = {
            "version": "1.4",
            "availableSpectrumInquiryRequests": [
                {
                    "requestId": "0",
                    "deviceDescriptor": {
                        "serialNumber": config["ap"]["serialNumber"],
                        "certificationId": [{"rulesetId": config["ap"]["rulesetId"], "id": config["ap"]["certificationId"]}],
                    },
                    "location": {
                        "ellipse": {
                            "center": {"latitude": config["ap"]["latitude"], "longitude": config["ap"]["longitude"]},
                            "majorAxis": config["ap"]["majorAxis"],
                            "minorAxis": config["ap"]["minorAxis"],
                            "orientation": config["ap"]["orientation"],
                        },
                        "elevation": {
                            "height": config["ap"]["height"],
                            "heightType": config["ap"]["heightType"],
                            "verticalUncertainty": config["ap"]["verticalUncertainty"],
                        },
                        "indoorDeployment": config["ap"]["indoorDeployment"],
                    },
                    "inquiredFrequencyRange": inquiredFrequencyRange,
                    "inquiredChannels": [{"globalOperatingClass": channel} for channel in inquiredChannels],
                }
            ],
        }

        return request_data

    def parse_response(self, response):
        available_channels = []
        for inquiry_response in response["availableSpectrumInquiryResponses"]:
            for channel_info in inquiry_response["availableChannelInfo"]:
                available_channels.extend(channel_info["channelCfi"])

        return sorted(set(available_channels))
