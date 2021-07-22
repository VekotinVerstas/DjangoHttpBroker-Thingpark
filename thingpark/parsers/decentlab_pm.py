"""
https://github.com/decentlab/decentlab-decoders/blob/master/DL-TRS12/DL-TRS12.py
"""

import struct
import binascii

PROTOCOL_VERSION = 2

SENSORS = [
    {'length': 1,
     'values': [{'name': 'Battery voltage',
                 'convert': lambda x: x[0] / 1000,
                 'unit': 'V'}]},
    {'length': 10,
     'values': [{'name': 'PM1.0 mass concentration',
                 'convert': lambda x: x[0] / 10,
                 'unit': 'µg⋅m⁻³'},
                {'name': 'PM2.5 mass concentration',
                 'convert': lambda x: x[1] / 10,
                 'unit': 'µg⋅m⁻³'},
                {'name': 'PM4 mass concentration',
                 'convert': lambda x: x[2] / 10,
                 'unit': 'µg⋅m⁻³'},
                {'name': 'PM10 mass concentration',
                 'convert': lambda x: x[3] / 10,
                 'unit': 'µg⋅m⁻³'},
                {'name': 'Typical particle size',
                 'convert': lambda x: x[4],
                 'unit': 'nm'},
                {'name': 'PM0.5 number concentration',
                 'convert': lambda x: x[5] / 10},
                {'name': 'PM1.0 number concentration',
                 'convert': lambda x: x[6] / 10},
                {'name': 'PM2.5 number concentration',
                 'convert': lambda x: x[7] / 10},
                {'name': 'PM4 number concentration',
                 'convert': lambda x: x[8] / 10},
                {'name': 'PM10 number concentration',
                 'convert': lambda x: x[9] / 10}]},
    {'length': 2,
     'values': [{'name': 'Air temperature',
                 'convert': lambda x: 175.72 * x[0] / 65536 - 46.85,
                 'unit': '°C'},
                {'name': 'Air humidity',
                 'convert': lambda x: 125 * x[1] / 65536 - 6,
                 'unit': '%'}]},
    {'length': 1,
     'values': [{'name': 'Barometric pressure',
                 'convert': lambda x: x[0] * 2,
                 'unit': 'Pa'}]}
]


def decode(msg, hex=False):
    """msg: payload as one of hex string, list, or bytearray"""
    bytes_ = bytearray(binascii.a2b_hex(msg)
                       if hex
                       else msg)
    version = bytes_[0]
    if version != PROTOCOL_VERSION:
        raise ValueError("protocol version {} doesn't match v2".format(version))

    devid = struct.unpack('>H', bytes_[1:3])[0]
    bin_flags = bin(struct.unpack('>H', bytes_[3:5])[0])
    flags = bin_flags[2:].zfill(struct.calcsize('>H') * 8)[::-1]

    words = [struct.unpack('>H', bytes_[i:i + 2])[0]
             for i
             in range(5, len(bytes_), 2)]

    cur = 0
    result = {'Device ID': devid, 'Protocol version': version}
    for flag, sensor in zip(flags, SENSORS):
        if flag != '1':
            continue

        x = words[cur:cur + sensor["length"]]
        cur += sensor["length"]
        for value in sensor['values']:
            if 'convert' not in value:
                continue

            result[value['name']] = {'value': value['convert'](x),
                                     'unit': value.get('unit', None)}

    return result


def parse_decentlab_pm(hex_str, port=None):
    decoded = decode(hex_str, hex=True)
    data = {}
    # Just extract value from decoded object, do not "harmonize"
    # (because I've 30 minutes work left before my vacation)
    for k in decoded.keys():
        if isinstance(decoded[k], dict):
            print(k, decoded[k])
            data[k] = decoded[k]["value"]
    return data


def decode_hex(hex_str: str, port: int = None):
    return parse_decentlab_pm(hex_str, port=port)


if __name__ == '__main__':
    import sys

    try:
        print(decode_hex(sys.argv[1], int(sys.argv[2])))
    except IndexError as err:
        print('Some examples:')
        for s in [
            # ('021b50000f0c25002500270027002701f50107012c012d012d012d67bd618dbd10', 5),
            # ('021b50000d0c2567bd618dbd10', 5),
            # ('021b5000010c25', 5),
            ('022590000d0c4968bf5b2cc433', 1),  # Real data
            ('02258e000d0c2c68de5badc434', 1),  # Real data
            ('02258e000d0c2b69615c4cc452', 1),  # Real data
            ('022308000d0bd0689d5c74c401', 1),  # Real data
        ]:
            print(decode_hex(s[0], s[1]))

        print(f'\nUsage: {sys.argv[0]} hex_payload port\n\n')
