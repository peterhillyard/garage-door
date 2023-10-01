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
    twilio_endpoint_uri: str
    twilio_acct_sid: str
    twilio_auth_key: str
    twilio_phone_number: str
    recipient_phone_numbers: List[str]
    notification_interval_minutes: int

def get_settings() -> Settings:
    shelly_endpoint_uri = os.getenv("shelly_endpoint_uri")
    shelly_auth_key = os.getenv("shelly_auth_key")
    shelly_device_id = os.getenv("shelly_device_id")
    twilio_endpoint_uri = os.getenv("twilio_endpoint_uri")
    twilio_acct_sid = os.getenv("twilio_acct_sid")
    twilio_auth_key = os.getenv("twilio_auth_key")
    twilio_phone_number = os.getenv("twilio_phone_number")
    notification_interval_minutes = int(os.getenv("notification_interval_minutes"))
    recipient_phone_numbers = json.loads(os.getenv("recipient_phone_numbers"))

    return Settings(
        shelly_endpoint_uri,
        shelly_auth_key,
        shelly_device_id,
        twilio_endpoint_uri,
        twilio_acct_sid,
        twilio_auth_key,
        twilio_phone_number,
        recipient_phone_numbers,
        notification_interval_minutes,
    )


class GarageDoorState(Enum):
    OPEN = auto()
    CLOSED = auto()
    UNKNOWN = auto()

def is_observation_time():
    current_datetime = datetime.datetime.now()
    return True if current_datetime.hour < 6 or current_datetime.hour >= 22 else False

def reqest_garage_door_state(shelly_endpoint_uri: str, shelly_device_id: str, shelly_auth_key: str) -> GarageDoorState:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = f'id={shelly_device_id}&auth_key={shelly_auth_key}'

    try:
        response = requests.post(f'{shelly_endpoint_uri}/device/status', headers=headers, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        return GarageDoorState.UNKNOWN

    response_json = response.json()
    switch_status = response_json["data"]["device_status"]["inputs"][0]["input"]

    return GarageDoorState.CLOSED if switch_status == 0 else GarageDoorState.OPEN

def send_alert_sms(twilio_endpoint_uri: str, twilio_acct_sid: str, twilio_auth_key: str, twilio_phone_number: str, recipient_phone_number: str):
    data = {
        'From': twilio_phone_number,
        'Body': 'The garage door is open',
        'To': recipient_phone_number,
    }

    try:
        response = requests.post(
            f'{twilio_endpoint_uri}/{twilio_acct_sid}/Messages.json',
            data=data,
            auth=(twilio_acct_sid, twilio_auth_key),
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        return

def start_loop():
    settings = get_settings()
    print("running")
    while True:
        time.sleep(settings.notification_interval_minutes * MINUTES_TO_SECONDS)
        garage_state = reqest_garage_door_state(settings.shelly_endpoint_uri, settings.shelly_device_id, settings.shelly_auth_key)

        if garage_state in [GarageDoorState.CLOSED, GarageDoorState.UNKNOWN] or not is_observation_time():
            continue

        for recipient_phone_number in settings.recipient_phone_numbers:
            print("send txt")
            # send_alert_sms(settings.twilio_endpoint_uri, settings.twilio_acct_sid, settings.twilio_auth_key, settings.twilio_phone_number, recipient_phone_number)
        

def main():
    start_loop()

if __name__ == "__main__":
    main()