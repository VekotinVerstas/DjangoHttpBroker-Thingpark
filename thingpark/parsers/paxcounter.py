"""
See example here:
https://github.com/cyberman54/ESP32-Paxcounter/blob/master/src/TTN/plain_decoder.js
"""


def parse_paxcounter(payload_hex, port=None):
    data = {}
    b = bytearray.fromhex(payload_hex)
    len_b = len(b)
    if port == '1':
        payload_len = len(payload_hex)
        print(payload_len)
        # We assume here PAXCOUNTER is configured to send data in "plain" format
        # paxcounter.conf: #define PAYLOAD_ENCODER                 1
        if payload_len == 4:
            data['wifi'] = float(int(payload_hex[0:4], 16))
        elif payload_len == 8:
            data['wifi'] = float(int(payload_hex[0:4], 16))
            data['ble'] = float(int(payload_hex[4:8], 16))
    # TODO: Other ports and payload formats are not implemented yet
    # else:
    #     raise ValueError(f'Unknown port "{port}"')
    return data

if __name__ == '__main__':
    import sys

    print("virt")

    data = parse_paxcounter(sys.argv[1], port='1')
    print(data)
