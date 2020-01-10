from .aqburk import parse_aqburk
from .clickey import parse_clickey_tempsens
from .keyval import parse_keyval
from .paxcounter import parse_paxcounter
from .energiaburk import parse_energiaburk
from .sensornode import parse_sensornode
from .decentlab import parse_decentlab


def parse(payload_hex):
    """
    Try to guess payload format and return parsed data as a dict or None
    :param payload_hex: hex character string
    :return: dict data or None
    """
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
