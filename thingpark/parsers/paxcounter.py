def parse_paxcounter(payload_hex):
    return {
        'wifi': hex2int(payload_hex[0:4]),
        'ble': hex2int(payload_hex[4:8])
    }
