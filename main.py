from dataclasses import dataclass
from enum import Enum, auto
import json
import os
import time
from typing import List
from urllib import request
import urllib.error
import datetime
import logging

MINUTES_TO_SECONDS = 60

@dataclass
class Settings:
    shelly_endpoint_uri: str
    shelly_auth_key: str
    shelly_device_id: str
    brevo_url: str
    brevo_api_key: str
    sender_email: str
    recipient_email_addresses: List[str]
    notification_interval_minutes: int
    awake_start_end_hours: List[int]

def get_settings() -> Settings:
    shelly_endpoint_uri = os.getenv("shelly_endpoint_uri")
    shelly_auth_key = os.getenv("shelly_auth_key")
    shelly_device_id = os.getenv("shelly_device_id")
    brevo_url = os.getenv("brevo_url")
    brevo_api_key = os.getenv("brevo_api_key")
    sender_email = os.getenv("sender_email")
    notification_interval_minutes = int(os.getenv("notification_interval_minutes"))
    recipient_email_addresses = json.loads(os.getenv("recipient_email_addresses"))
    awake_start_end_hours = json.loads(os.getenv("awake_start_end_hours"))

    return Settings(
        shelly_endpoint_uri,
        shelly_auth_key,
        shelly_device_id,
        brevo_url,
        brevo_api_key,
        sender_email,
        recipient_email_addresses,
        notification_interval_minutes,
        awake_start_end_hours,
    )


class GarageDoorState(Enum):
    OPEN = auto()
    CLOSED = auto()
    UNKNOWN = auto()

def is_observation_time(settings: Settings) -> bool:
    current_datetime = datetime.datetime.now()
    return True if current_datetime.hour < settings.awake_start_end_hours[0] or current_datetime.hour >= settings.awake_start_end_hours[1] else False

def reqest_garage_door_state(settings: Settings) -> GarageDoorState:
    data = f'id={settings.shelly_device_id}&auth_key={settings.shelly_auth_key}'
    encoded_data = data.encode()
    
    req = request.Request(f'{settings.shelly_endpoint_uri}/device/status', method="POST")
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        r = request.urlopen(req, data=encoded_data)
        content = r.read()
        decoded_content = content.decode('utf-8')
        print(decoded_content)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        return GarageDoorState.UNKNOWN

    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return GarageDoorState.UNKNOWN

    response_json = json.loads(decoded_content)

    switch_status = response_json["data"]["device_status"]["inputs"][0]["input"]

    return GarageDoorState.OPEN if switch_status == 1 else GarageDoorState.CLOSED

def send_alert_sms(settings: Settings, recipient_email_address: str) -> None:
    data = {
        "sender": {
            "name": "Open Garage Checker",
            "email": settings.sender_email,
        },
        "to": [
            {
                "name": "Pete Hillyard",
                "email": recipient_email_address,
            }
        ],
        "subject": "Garage is open",
        "htmlContent": f"<html><head></head><body><p>The garage is open at {datetime.datetime.now()}</p></body></html>"
    }
    encoded_data = json.dumps(data).encode()

    headers = {
        "accept": "application/json",
        "api-key": settings.brevo_api_key,
        "content-type": "application/json",
    }
    req = request.Request(settings.brevo_url, method="POST")
    [req.add_header(key, value) for key, value in headers.items()]

    try:
        request.urlopen(req, data=encoded_data)
        logging.warning(f"successfully sent msg to {recipient_email_address}")
    except urllib.error.HTTPError as e:
        logging.warning(f"HTTP Error: {e.code} {e.reason}")
        logging.warning(f"failed to send to {recipient_email_address}")

    except urllib.error.URLError as e:
        logging.warning(f"failed to send to {recipient_email_address}")
        logging.warning(f"URL Error: {e.reason}")

def start_loop():
    settings = get_settings()
    logging.warning(f"{settings.recipient_email_addresses}")
    logging.warning(f"{settings.awake_start_end_hours}")
    logging.warning("running")
    while True:
        time.sleep(settings.notification_interval_minutes * MINUTES_TO_SECONDS)
        # time.sleep(settings.notification_interval_minutes)
        garage_state = reqest_garage_door_state(settings)

        logging.warning(f"{garage_state}, {datetime.datetime.now().hour}, {datetime.datetime.now().minute}")
        if garage_state in [GarageDoorState.CLOSED, GarageDoorState.UNKNOWN] or not is_observation_time(settings):
            continue

        for recipient_email_address in settings.recipient_email_addresses:
            logging.warning(f"send txt to {recipient_email_address}:  {garage_state}, {datetime.datetime.now().hour}, {datetime.datetime.now().minute}")
            send_alert_sms(settings, recipient_email_address)

def main():
    start_loop()

if __name__ == "__main__":
    main()