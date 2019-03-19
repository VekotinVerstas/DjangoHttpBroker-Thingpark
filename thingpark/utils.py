import base64
import json
import datetime
import influxdb
import pytz
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.timezone import get_default_timezone


def get_influxdb_client(host='127.0.0.1', port=8086, database='mydb'):
    iclient = influxdb.InfluxDBClient(host=host, port=port, database=database)
    return iclient


def create_influxdb_obj(devid, measurement, fields, timestamp=None, extratags=None):
    # Make sure timestamp is timezone aware and in UTC time
    if timestamp is None:
        timestamp = pytz.UTC.localize(datetime.datetime.utcnow())
    elif timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        timestamp = get_default_timezone().localize(timestamp)
    timestamp = timestamp.astimezone(pytz.UTC)
    for k, v in fields.items():
        fields[k] = float(v)
    measurement = {
        "measurement": measurement,
        "tags": {
            "dev-id": devid,
        },
        "time": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # is in UTC time
        "fields": fields
    }
    if extratags is not None:
        measurement['tags'].update(extratags)
    return measurement


def basicauth(request):
    """Check for valid basic auth header."""
    uname, passwd, user = None, None, None
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == "basic":
                a = auth[1].encode('utf8')
                s = base64.b64decode(a)
                uname, passwd = s.decode('utf8').split(':')
                user = authenticate(username=uname, password=passwd)
    return uname, passwd, user


def get_datalogger(devid, name='', update_activity=False):
    # FIXME: Shit, this import can't be in the beginning of the file or we'll get:
    # "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet."
    # It can be imported if you run django.setup() before import, but it messes up loading
    # import django
    # django.setup()
    from broker.models import Datalogger

    datalogger, created = Datalogger.objects.get_or_create(devid=devid)
    changed = False
    if created:
        datalogger.name = name
        changed = True
    if update_activity:
        datalogger.activity_at = timezone.now()
        changed = True
    if changed:
        datalogger.save()
    return datalogger, created


def decode_json_body(body):
    body_str = body.decode('utf8', "backslashreplace")
    try:
        data = json.loads(body_str)
        return True, data
    except json.decoder.JSONDecodeError as err:
        return False, err
