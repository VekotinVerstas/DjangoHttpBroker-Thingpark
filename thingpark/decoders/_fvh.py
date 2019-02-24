import logging
import binascii
import influxdb
import dateutil
import pytz
from django.utils import timezone
from django.utils.timezone import get_default_timezone

logger = logging.getLogger(__name__)


def hex2int(hex_str):
    """
    Convert hex characters (e.g. "23" or "011a") to int (35 or 282)
    :param hex_str: hex character string
    :return: int integer
    """
    return int(hex_str, 16)


def hex2value10(hex_str):
    """
    Convert 2 hex characters (e.g. "23") to float (3.5)
    :param hex_str: hex character string
    :return: float value
    """
    return hex2int(hex_str) / 10.0


def calc_temp(hex_str):
    """
    Convert 4 hex characters (e.g. "040b") to float temp (25.824175824175825)
    :param hex_str: hex character string
    :return: float temperature
    """
    adc = int(hex_str[0:2], 16) * 256 + int(hex_str[2:4], 16)
    temp = (300 * adc / 4095) - 50
    return temp


def calc_volts(hex_str):
    """
    Convert 2 hex characters (e.g. "fe") to float volts (3.5043478260869567)
    :param hex_str: hex character string
    :return: float volts
    """
    volts = ((int(hex_str, 16) / 0.23) + 2400) / 1000
    return volts


def parse_clickey_tempsens(hex_str):
    temp1 = calc_temp(hex_str[2:6])
    temp2 = calc_temp(hex_str[6:10])
    volts = calc_volts(hex_str[10:12])
    return {
        'temp1': temp1,
        'temp2': temp2,
        'volt': volts
    }


def parse_aqburk(hex_str):
    """
    Parse payload like "2a2a0021002c002800300056003b0000" float values
    :param hex_str: AQLoRaBurk hex payload
    :return: dict containing float values
    """
    data = {
        'pm25min': hex2value10(hex_str[4:8]),
        'pm25max': hex2value10(hex_str[8:12]),
        'pm25avg': hex2value10(hex_str[12:16]),
        'pm25med': hex2value10(hex_str[16:20]),
        'pm10min': hex2value10(hex_str[20:24]),
        'pm10max': hex2value10(hex_str[24:28]),
        'pm10avg': hex2value10(hex_str[28:32]),
        'pm10med': hex2value10(hex_str[32:36]),
    }
    if len(hex_str) == 52:
        data['temp'] = round(hex2value10(hex_str[36:40]) - 100, 1)
        data['humi'] = hex2value10(hex_str[40:44])
        data['pres'] = hex2value10(hex_str[44:48])
        data['gas'] = hex2value10(hex_str[48:52])
    return data


def parse_keyval(hex_str):
    """
    :param hex_str: key-value hex payload
    :return: dict containing parsed balues
    :raises UnicodeDecodeError: if hex_str contains illegal bytes for utf8
    """
    _str = binascii.unhexlify(hex_str)  # --> b'temp=24.61,hum=28.69'
    _str = _str.decode()  # --> 'temp=24.61,hum=28.69'
    keyvals = [x.split('=') for x in _str.split(',')]  # --> [['temp', '24.61'], ['hum', '28.69']]
    keyvals = [[x[0], float(x[1])] for x in keyvals]  # --> [['temp', 24.61], ['hum', 28.69]]
    data = dict(keyvals)  # --> {'temp': 24.61, 'hum': 28.69}
    return data


def parse_paxcounter(payload_hex):
    return {
        'wifi': hex2int(payload_hex[0:4]),
        'ble': hex2int(payload_hex[4:8])
    }


def parse(payload_hex):
    if len(payload_hex) == 8:
        data = parse_paxcounter(payload_hex)
    elif payload_hex[:2] == '13':
        data = parse_clickey_tempsens(payload_hex)
    elif payload_hex[:2].lower() == '2a':  # payload_hex[:4].lower() == '2a2a':
        data = parse_aqburk(payload_hex)
    elif len(payload_hex) >= 2:  # Assume we have key-val data
        try:
            data = parse_keyval(payload_hex)
        except (UnicodeDecodeError, IndexError) as err:
            data = None
    else:
        data = None
        # TODO log error
    return data


def get_influxdb_client(host='127.0.0.1', port=8086, database='mydb'):
    iclient = influxdb.InfluxDBClient(host=host, port=port, database=database)
    return iclient


def create_influxdb_obj(dev_id, measurement, fields, timestamp=None, extratags=None):
    # Make sure timestamp is timezone aware and in UTC time
    if timestamp is None:
        timestamp = pytz.UTC.localize(datetime.datetime.utcnow())
    elif timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        timestamp = get_default_timezone().localize(timestamp)
    timestamp = timestamp.astimezone(pytz.UTC)
    for k, v in fields.items():
        fields[k] = float(v)
    measurement = {
        "measurement": measurement,
        "tags": {
            "dev-id": dev_id,
        },
        "time": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # is in UTC time
        "fields": fields
    }
    if extratags is not None:
        measurement['tags'].update(extratags)
    return measurement
