import struct


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


def parse_energiaburk(hex_str, port=None):
    """
    Parse payload like "3a2c007d0003002a000000000000000000000000" float values
    :param hex_str: EnergiaBurk hex payload
    :param port: LoRaWAN port
    :return: dict containing float values
    """
    if hex_str.startswith('3a'):
        return parse_joniburk(hex_str)
    elif hex_str.startswith('09'):
        return parse_voltageburk(hex_str)


def parse_joniburk(hex_str, port=None):
    """
    Parse payload like "3a2c007d0003002a000000000000000000000000" float values
    :param hex_str: EnergiaBurk hex payload
    :param port: LoRaWAN port
    :return: dict containing float values
    """
    data = {
        'voltage': hex2value10(hex_str[4:8]),
        'current': hex2value10(hex_str[8:12]),
        'power': hex2value10(hex_str[12:16]),
    }
    return data


def parse_voltageburk(hex_str, port=None):
    """
    Parse payload like "3a2c007d0003002a000000000000000000000000" float values
    :param hex_str: EnergiaBurk hex payload
    :param port: LoRaWAN port
    :return: dict containing float values
    """
    b1 = bytes.fromhex(hex_str[-8:])
    volt = struct.unpack('<f', b1)[0]
    data = {
        'voltage': volt,
    }
    return data
