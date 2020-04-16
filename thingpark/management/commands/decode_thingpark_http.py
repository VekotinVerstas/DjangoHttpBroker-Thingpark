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
    get_datalogger_decoder,
    save_parse_fail_datalogger_message,
    decode_json_body, get_datalogger, decode_payload,
    create_routing_key, send_message
)

logger = logging.getLogger('thingpark')


def send_to_exchange(devid, datalogger, datalines, override_measurement=None):
    # RabbitMQ part
    key = create_routing_key('thingpark', devid)
    message = create_parsed_data_message(devid, datalines=datalines)
    packed_message = data_pack(message)
    exchange = settings.PARSED_DATA_HEADERS_EXCHANGE
    logger.debug(f'exchange={settings.PARSED_DATA_EXCHANGE} key={key}  packed_message={packed_message}')
    config = {}
    # TODO: implement and use get_datalogger_config()
    if datalogger.application:
        config = json.loads(datalogger.application.config)
    # TODO: get influxdb variables from Application / Datalogger / Forward etc config
    if 'influxdb_database' in config and 'influxdb_measurement' in config:
        config['influxdb'] = '1'
        if override_measurement is not None:
            config['influxdb_measurement'] = override_measurement
    send_message(exchange, '', packed_message, headers=config)


def parse_thingpark_request(serialised_request, data):
    d = data['DevEUI_uplink']
    devid = d['DevEUI']
    port = d['FPort']
    datalogger, created = get_datalogger(devid=devid, update_activity=False)
    timestamp = parse(d['Time'])
    timestamp = timestamp.astimezone(pytz.UTC)
    payload_hex = d['payload_hex']
    rssi = d['LrrRSSI']
    # TODO: This may fail, so prepare to handle exception properly
    # Test it by configuring wrong decoder for some Datalogger
    try:
        payload = decode_payload(datalogger, payload_hex, port, serialised_request=serialised_request)
    except ValueError as err:
        decoder = get_datalogger_decoder(datalogger)
        err_msg = f'Failed to parse "{payload_hex}" using "{decoder}" for "{devid}": {err}'
        logger.warning(err_msg)
        serialised_request['parse_fail'] = {
            'error_message': str(err),
            'decoder': get_datalogger_decoder(datalogger)
        }
        save_parse_fail_datalogger_message(devid, data_pack(serialised_request))
        return True
    logging.debug(payload)

    # Some sensors may already return a dict of lists of datalines
    if isinstance(payload, dict):
        parsed_data = payload
        for k in parsed_data.keys():
            datalines = parsed_data[k]['datalines']
            if len(datalines) > 0:
                datalines[-1]['data']['rssi'] = float(rssi)  # Add rssi value to the latest dataline
                send_to_exchange(devid, datalogger, datalines, override_measurement=k)
    else:  # Some sensors may already return a list of datalines
        if isinstance(payload, list):
            datalines = payload  # Use payload as datalines (which already have timestamps)
        else:
            dataline = create_dataline(timestamp, payload)  # Create dataline from LoRaWAN timestamp and payload
            datalines = [dataline]
        datalines[-1]['data']['rssi'] = float(rssi)  # Add rssi value to the latest dataline
        send_to_exchange(devid, datalogger, datalines)
    return True


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
