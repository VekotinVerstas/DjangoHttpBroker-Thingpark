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
    elif hex_str.startswith('0a00'):
        return parse_victron(hex_str)


def parse_victron(hex_str, port=None):
    """
    Parse payload like "0a00000000e83c4600a83b4600000000000000000000ba42000000000000000000008041000081430000000000000000" struct of mixed values
    :param hex_str: Victron hex payload
    :param port: LoRaWAN port
    :return: dict containing values
    """

    b = bytes.fromhex(hex_str)
    val = struct.unpack('<Bbxxfffffffffii', b)

    data = {
        # 2  float mainVoltage_V;      // mV
        # 3  float panelVoltage_VPV;   // mV
        # 4  float panelPower_PPV;     // W
        # 5  float batteryCurrent_I;   // mA
        # 6  float yieldTotal_H19;     // 0.01 kWh
        # 7  float yieldToday_H20;     // 0.01 kWh
        # 8  float maxPowerToday_H21;  // W
        # 9  float yieldYesterday_H22; // 0.01 kWh
        # 10  float maxPowerYesterday_H23; // W
        # 11  int errorCode_ERR;
        # 12  int stateOfOperation_CS;
        'mainvoltage': val[2],
        'panelvoltage': val[3],
        'panelpower': val[4],
        'batterycurrent': val[5],
        'errorcode': val[11],  # int
        'state': val[12],  # int
    }
    return data


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
