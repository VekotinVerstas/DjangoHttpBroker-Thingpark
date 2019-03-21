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


def parse_aqburk(hex_str, port):
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
