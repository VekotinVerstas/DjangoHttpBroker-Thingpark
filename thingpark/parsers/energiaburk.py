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
    data = {
        'voltage': hex2value10(hex_str[4:8]),
        'current': hex2value10(hex_str[8:12]),
        'power': hex2value10(hex_str[12:16]),
    }
    print(data)
    return data
