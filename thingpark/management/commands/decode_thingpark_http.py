import json
import logging

import pytz
from dateutil.parser import parse
from django.conf import settings
from influxdb.exceptions import InfluxDBClientError

from broker.management.commands import RabbitCommand
from thingpark.utils import create_influxdb_obj, get_influxdb_client

from broker.utils import (
    create_dataline, create_parsed_data_message,
    data_pack, data_unpack,
    decode_json_body, get_datalogger, decode_payload,
    create_routing_key, send_message
)

logger = logging.getLogger('thingpark')


def parse_thingpark_request(serialised_request, data):
    d = data['DevEUI_uplink']
    devid = d['DevEUI']
    port = d['FPort']
    datalogger, created = get_datalogger(devid=devid, update_activity=False)
    timestamp = parse(d['Time'])
    timestamp = timestamp.astimezone(pytz.UTC)
    payload_hex = d['payload_hex']
    rssi = d['LrrRSSI']
    payload = decode_payload(datalogger, payload_hex, port=port)
    payload['rssi'] = rssi

    # RabbitMQ part
    key = create_routing_key('thingpark', devid)
    dataline = create_dataline(timestamp, payload)
    datalines = [dataline]
    message = create_parsed_data_message(devid, datalines=datalines)
    packed_message = data_pack(message)
    logger.debug(f'exchange={settings.PARSED_DATA_EXCHANGE} key={key}  packed_message={packed_message}')
    send_message(settings.PARSED_DATA_EXCHANGE, key, packed_message)

    # FIXME: this is in forwarder now, must migrate carefully
    keys_str = 'aqburk'
    measurement = create_influxdb_obj(devid, keys_str, payload, timestamp)
    measurements = [measurement]
    dbname = 'aqburk'
    iclient = get_influxdb_client(database=dbname)
    iclient.create_database(dbname)
    try:
        iclient.write_points(measurements)
        return True
    except InfluxDBClientError as err:
        return False


def consumer_callback(channel, method, properties, body, options=None):
    serialised_request = data_unpack(body)
    ok, data = decode_json_body(serialised_request['request.body'])
    if ok and 'DevEUI_uplink' in data:
        parse_thingpark_request(serialised_request, data)
        logger.debug(json.dumps(data, indent=2))
    else:
        logger.warning(f'DevEUI_uplink was not found in data.')
    channel.basic_ack(method.delivery_tag)


class Command(RabbitCommand):
    help = 'Decode thingpark'

    def add_arguments(self, parser):
        parser.add_argument('--prefix', type=str,
                            help='queue and routing_key prefix, overrides settings.ROUTING_KEY_PREFIX')
        super().add_arguments(parser)

    def handle(self, *args, **options):
        logger.info(f'Start handling {__name__}')
        name = 'thingpark'
        # FIXME: constructing options should be in a function in broker.utils
        if options["prefix"] is None:
            prefix = settings.RABBITMQ["ROUTING_KEY_PREFIX"]
        else:
            prefix = options["prefix"]
        options['exchange'] = settings.RAW_HTTP_EXCHANGE
        options['routing_key'] = f'{prefix}.{name}.#'
        options['queue'] = f'{prefix}_decode_{name}_http_queue'
        options['consumer_callback'] = consumer_callback
        super().handle(*args, **options)
