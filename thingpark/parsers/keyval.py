import binascii


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
