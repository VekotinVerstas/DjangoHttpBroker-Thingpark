import datetime
import struct
import pytz

from broker.utils import create_dataline, create_parsed_data_message


def extract_bits(value, first, last):
    """
    Extract some bits from int `value`
    :param int value:
    :param int first:
    :param int last:
    :return: int
    """
    value >>= first
    mask = ~((-1) << (last - first + 1))
    return value & mask


def get_timestamp(value):
    """
    Extract timezone aware datetime from mcf88 measurement
    :param bytes value: measurement converted to bytes
    :return: datetime
    """
    timestamp, = struct.unpack('<I6x', value)
    year = extract_bits(timestamp, 25, 31) + 2000
    month = extract_bits(timestamp, 21, 24)
    day = extract_bits(timestamp, 16, 20)
    hour = extract_bits(timestamp, 11, 15)
    minute = extract_bits(timestamp, 5, 10)
    second = extract_bits(timestamp, 0, 4) * 2
    dt = pytz.UTC.localize(datetime.datetime(year, month, day, hour, minute, second))
    return dt


def parse_mcf88(hex_str, port=None):
    """
    Parse payload like "0462651527da078e4d8e01a4691527dd078f488e01676d1527e9078d1a8e015d" float values
    :param hex_str: MCF88 hex payload
    :param port: LoRaWAN port
    :return: dict containing float values
    """
    if hex_str[:2] == '04':
        line = hex_str[2:62]
        n = 20
        datas = [line[i:i + n] for i in range(0, len(line), n)]
        datalines = []
        for data in datas:
            value = bytes.fromhex(data)
            ts = get_timestamp(value)  # datetime in UTC (timezone aware)
            # print("'{}'".format(data[8:10]))
            parsed_data = {
                'temp': struct.unpack('<h', bytes.fromhex(data[8:12]))[0] / 100,  # °C
                'humi': int(data[12:14], 16) / 2,
                'pres': struct.unpack('<I', bytes.fromhex(data[14:20] + '00'))[0] / 100  # hPa
            }
            dataline = create_dataline(ts, parsed_data)
            datalines.append(dataline)
        return datalines
    return None




def decode_hex(hex_str: str, port: int = None):
    return parse_mcf88(hex_str, port=port)


if __name__ == '__main__':
    import sys

    try:
        print(decode_hex(sys.argv[1], int(sys.argv[2])))
    except IndexError as err:
        print('Some examples:')
        for s in [('04d276522a44fcb3649001147b522a3cfcb6579001d77e522a22fcb72e900152', 2),
                  ('04bd79522a2ffcc8869001827d522a06fcc8549001c481522a12fcc84190015b', 2),
                  ('042279522a68fca5489101e57c522a72fca62191012781522a6efca60691015c', 2),
                  ]:
            print(decode_hex(s[0], s[1]))

        print(f'\nUsage: {sys.argv[0]} hex_payload port\n\n')
