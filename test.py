from main import reqest_garage_door_state, get_settings, send_alert_sms

def test_reqest_garage_door_state():
    settings = get_settings()

    print(reqest_garage_door_state(settings))

def test_send_alert_sms():
    settings = get_settings()

    for email_address in settings.recipient_email_addresses:
        send_alert_sms(settings, email_address)

if __name__ == "__main__":
    test_reqest_garage_door_state()
    test_send_alert_sms()