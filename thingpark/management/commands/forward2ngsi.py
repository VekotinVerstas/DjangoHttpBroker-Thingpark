"""
Original NGSI data example can be found from here:
https://github.com/Fiware/dataModels/blob/master/specs/Environment/AirQualityObserved/doc/spec.md#key-value-pairs-example
Below is reduced and modified version, e.g. PM values added.
See also https://github.com/Fiware/dataModels/issues/292

{
  'pm25min': 0.3, 'pm25max': 0.4, 'pm25avg': 0.3, 'pm25med': 0.3,
  'pm10min': 0.3, 'pm10max': 0.5, 'pm10avg': 0.3, 'pm10med': 0.4,
  'temp': 23.6, 'humi': 11.0, 'pres': 1039.7, 'gas': 1333.3,
  'rssi': '-82.000000'
}
"""

import json
import requests
from django.conf import settings
from broker.utils import data_pack, data_unpack
from broker.management.commands import RabbitCommand
from broker.models import Forward
from thingpark.utils import get_datalogger

NGSI_DATA = json.loads("""
{
    "id": "NAME-UNIQUE_ID-TIMESTAMP",
    "type": "AirQualityObserved",
    "address": {
        "addressCountry": "FI",
        "addressLocality": "CITY",
        "streetAddress": "ADDRESS"
    },
    "dateObserved": "2016-03-15T11:00:00/2016-03-15T12:00:00",
    "location": {
        "type": "Point",
        "coordinates": [24.96000, 60.170000]
    },
    "source": "https://fvh.io/ilmanlaatu2019",
    "reliability": 0.9,
    "PM2.5": 45,
    "PM10": 500
}
""")

ORION_URL_ROOT = settings.ORION_URL_ROOT
ORION_USERNAME = settings.ORION_USERNAME
ORION_PASSWORD = settings.ORION_PASSWORD


def push_ngsi_orion(data, url_root, username, password):
    # device_id = data['id']
    res = None
    res = requests.post('{}/entities/'.format(url_root), auth=(username, password), json=data)
    try:  # ...to update the entity...
        patch_data = data.copy()
        # Remove illegal keys from patch data
        del patch_data['id']
        del patch_data['type']
        res = requests.patch('{}/entities/{}/attrs/?options=keyValues'.format(url_root, data['id']),
                             auth=(username, password), json=patch_data)
    except Exception as err:
        # logger.error('Something went wrong! Exception: {}'.format(err))
        print('Something went wrong PATCHing to Orion! Exception: {}'.format(err))
    # ...if updating failed, the entity probably doesn't exist yet so create it
    if not res or (res.status_code != 204):
        res = requests.post('{}/entities/?options=keyValues'.format(url_root), auth=(username, password), json=data)
    return res


def send_to_ngsi(data, options=None):
    devid = data.pop('devid')
    dataline = data['datalines'][0]
    timestr = dataline.pop('time')
    values = dataline.pop('data')
    datalogger, created = get_datalogger(devid=devid, update_activity=False)
    forwards = datalogger.forwards.filter(handler='thingpark.AQBurk2NGSIForward')
    if forwards.count() == 0:
        return False
    # NOTE: this Forward is not currently used, url, user and password are taken from local_settings.py
    f: Forward = forwards[0]
    assert isinstance(NGSI_DATA, dict)
    # print(values)
    if 'pm25avg' not in values:
        return False
    NGSI_DATA['id'] = devid
    NGSI_DATA['PM2.5'] = values['pm25avg']
    NGSI_DATA['PM10'] = values['pm10avg']
    NGSI_DATA['reliability'] = 0.5
    NGSI_DATA['dateObserved'] = timestr
    if datalogger.lon and datalogger.lat:
        NGSI_DATA['location']['coordinates'] = [datalogger.lon, datalogger.lat]
    else:
        return False
    if datalogger.country and datalogger.locality and datalogger.street:
        NGSI_DATA['address']['addressCountry'] = datalogger.country
        NGSI_DATA['address']['addressLocality'] = datalogger.locality
        NGSI_DATA['address']['streetAddress'] = datalogger.street
    else:
        NGSI_DATA['address']['addressCountry'] = ''
        NGSI_DATA['address']['addressLocality'] = ''
        NGSI_DATA['address']['streetAddress'] = ''

    # ngsi_json = json.dumps(NGSI_DATA)
    # print(json.dumps(NGSI_DATA, indent=2))
    res = push_ngsi_orion(NGSI_DATA, ORION_URL_ROOT, ORION_USERNAME, ORION_PASSWORD)
    return res


def consumer_callback(channel, method, properties, body, options=None):
    data = data_unpack(body)
    res = send_to_ngsi(data, options=options)
    if res:
        print(res, res.text)
    else:
        print('No Forwards found!')
    # res.status_code should be 201 or 204
    channel.basic_ack(method.delivery_tag)


class Command(RabbitCommand):
    help = 'Decode thingpark'

    def add_arguments(self, parser):
        # parser.add_argument('keys', nargs='+', type=str)
        super().add_arguments(parser)
        pass

    def handle(self, *args, **options):
        options['exchange'] = settings.PARSED_DATA_EXCHANGE
        options['routing_key'] = f'{settings.RABBITMQ["ROUTING_KEY_PREFIX"]}.#'
        options['queue'] = 'forward2ngsi_queue'
        options['consumer_callback'] = consumer_callback
        super().handle(*args, **options)
