from dataclasses import dataclass
from enum import Enum, auto
import json
import os
import time
from typing import List
import requests
import datetime

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

def get_settings() -> Settings:
    shelly_endpoint_uri = os.getenv("shelly_endpoint_uri")
    shelly_auth_key = os.getenv("shelly_auth_key")
    shelly_device_id = os.getenv("shelly_device_id")
    brevo_url = os.getenv("brevo_url")
    brevo_api_key = os.getenv("brevo_api_key")
    sender_email = os.getenv("sender_email")
    notification_interval_minutes = int(os.getenv("notification_interval_minutes"))
    recipient_email_addresses = json.loads(os.getenv("recipient_email_addresses"))

    return Settings(
        shelly_endpoint_uri,
        shelly_auth_key,
        shelly_device_id,
        brevo_url,
        brevo_api_key,
        sender_email,
        recipient_email_addresses,
        notification_interval_minutes,
    )


class GarageDoorState(Enum):
    OPEN = auto()
    CLOSED = auto()
    UNKNOWN = auto()

def is_observation_time():
    current_datetime = datetime.datetime.now()
    return True if current_datetime.hour < 6 or current_datetime.hour >= 22 else False

def reqest_garage_door_state(settings: Settings) -> GarageDoorState:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = f'id={settings.shelly_device_id}&auth_key={settings.shelly_auth_key}'

    try:
        response = requests.post(f'{settings.shelly_endpoint_uri}/device/status', headers=headers, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        return GarageDoorState.UNKNOWN

    response_json = response.json()
    switch_status = response_json["data"]["device_status"]["inputs"][0]["input"]

    return GarageDoorState.OPEN if switch_status == 1 else GarageDoorState.CLOSED

def send_alert_sms(settings: Settings, recipient_email_address: str):
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

    headers = {
        "accept": "application/json",
        "api-key": settings.brevo_api_key,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            settings.brevo_url,
            json=data,
            headers=headers,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        return

def start_loop():
    settings = get_settings()
    print("running")
    while True:
        time.sleep(settings.notification_interval_minutes * MINUTES_TO_SECONDS)
        # time.sleep(settings.notification_interval_minutes)
        garage_state = reqest_garage_door_state(settings)

        print(garage_state, datetime.datetime.now().hour, datetime.datetime.now().minute)
        if garage_state in [GarageDoorState.CLOSED, GarageDoorState.UNKNOWN] or not is_observation_time():
            continue

        for recipient_email_address in settings.recipient_email_addresses:
            print("send txt", garage_state, datetime.datetime.now().hour, datetime.datetime.now().minute)
            send_alert_sms(settings, recipient_email_address)


def main():
    start_loop()

if __name__ == "__main__":
    main()
