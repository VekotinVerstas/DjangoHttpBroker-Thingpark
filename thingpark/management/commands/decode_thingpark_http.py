import pytz
from dateutil.parser import parse
from influxdb.exceptions import InfluxDBClientError
from django.conf import settings
from broker.utils import data_pack, data_unpack
from broker.utils import send_message
from broker.management.commands import RabbitCommand
from thingpark.utils import create_influxdb_obj, get_influxdb_client
from broker.utils import decode_json_body, get_datalogger, decode_payload


def parse_thingpark_request(serialised_request, data):
    d = data['DevEUI_uplink']
    devid = d['DevEUI']
    port = d['FPort']
    datalogger, created = get_datalogger(devid=devid, update_activity=False)
    timestamp = parse(d['Time'])
    timestamp = timestamp.astimezone(pytz.UTC)
    payload_hex = d['payload_hex']
    rssi = d['LrrRSSI']
    idata = decode_payload(datalogger, payload_hex, port)
    idata['rssi'] = rssi

    # RabbitMQ part
    pre = settings.RABBITMQ['ROUTING_KEY_PREFIX']
    KEY_PREFIX = f'{pre}.thingpark'
    key = f'{KEY_PREFIX}.{devid}'
    # FIXME: use create_dataline()
    message = {
        'time': timestamp.isoformat() + 'Z',
        'devid': devid,
        'data': idata,
    }
    packed_message = data_pack(message)
    print(settings.PARSED_DATA_EXCHANGE, key, packed_message)
    send_message(settings.PARSED_DATA_EXCHANGE, key, packed_message)

    keys_str = 'aqburk'
    measurement = create_influxdb_obj(devid, keys_str, idata, timestamp)
    measurements = [measurement]
    # print(json.dumps(measurements, indent=1))
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
    if 'DevEUI_uplink' in data:
        parse_thingpark_request(serialised_request, data)
    print(data)
    channel.basic_ack(method.delivery_tag)


class Command(RabbitCommand):
    help = 'Decode thingpark'

    def add_arguments(self, parser):
        # parser.add_argument('keys', nargs='+', type=str)
        super().add_arguments(parser)
        pass

    def handle(self, *args, **options):
        options['exchange'] = settings.RAW_HTTP_EXCHANGE
        options['routing_key'] = f'{settings.RABBITMQ["ROUTING_KEY_PREFIX"]}.thingpark.#'
        options['queue'] = 'decode_thingpark_http_queue'
        options['consumer_callback'] = consumer_callback
        super().handle(*args, **options)
