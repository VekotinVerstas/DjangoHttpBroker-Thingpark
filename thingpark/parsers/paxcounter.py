"""
See example here:
https://github.com/cyberman54/ESP32-Paxcounter/blob/master/src/TTN/plain_decoder.js
"""


def parse_paxcounter(payload_hex, port=None):
    if port == '1':
        data = {
            'wifi': int(payload_hex[0:4], 16),
            'ble': int(payload_hex[4:8], 16)
        }
    else:
        raise ValueError(f'Unknown port "{port}"')
    return data
