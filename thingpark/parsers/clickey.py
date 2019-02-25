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
