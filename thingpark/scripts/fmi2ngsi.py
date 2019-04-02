import django
import os
import sys
import datetime
import json
import requests
import urllib
from dateutil.parser import parse

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "httpbroker.settings")
django.setup()

from django.conf import settings
from thingpark.scripts.fmiapiget import get_fmi_data, get_args, get_fmi_api_url, create_datetime


def get_ngsi_template():
    return {
        "id": "NAME-UNIQUE_ID-TIMESTAMP",
        "type": "AirQualityObserved",
        "address": {
            "addressCountry": "FI",
            "addressLocality": "CITY",
            "streetAddress": "ADDRESS"
        },
        "location": {
            "type": "Point",
            "coordinates": [24.96000, 60.170000]
        },
        "source": "https://fvh.io/ilmanlaatu2019",
        "reliability": 1.0
    }


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


def add_key(ngsidata, ngsikey, fmidata, fmikey):
    # if fmikey in fmidata and fmidata[fmikey] is not None:
    if fmikey in fmidata:
        ngsidata[ngsikey] = fmidata[fmikey]
    else:
        ngsidata[ngsikey] = None


def send_to_ngsi(data, options=None):
    dataline = data.pop('datalines')[-1]
    values = dict(dataline['data'])
    NGSI_DATA = get_ngsi_template()
    assert isinstance(NGSI_DATA, dict)
    # TODO: this needs mapping from values keys to NGSI data
    NGSI_DATA['id'] = f"fmi-{data['devid']}"
    print(data['source'])
    source = urllib.parse.quote_plus(data['source'])
    # source = 'https://opendata.fmi.fi/wfs?-request=getFeature'
    NGSI_DATA['source'] = source
    NGSI_DATA['location'] = data['location']
    name_split = data['name'].split(' ')
    NGSI_DATA['address']['addressLocality'] = name_split[0]
    NGSI_DATA['address']['streetAddress'] = ' '.join(name_split[1:])
    # Mapp
    add_key(NGSI_DATA, 'PM2.5', values, 'PM25_PT1H_avg')
    add_key(NGSI_DATA, 'PM10', values, 'PM10_PT1H_avg')
    add_key(NGSI_DATA, 'SO2', values, 'SO2_PT1H_avg')
    add_key(NGSI_DATA, 'NO2', values, 'NO2_PT1H_avg')
    add_key(NGSI_DATA, 'NO', values, 'NO_PT1H_avg')
    add_key(NGSI_DATA, 'O3', values, 'O3_PT1H_avg')
    NGSI_DATA['reliability'] = 1.0
    ts = parse(dataline['time'])
    NGSI_DATA['dateObservedFrom'] = (ts - datetime.timedelta(hours=1)).isoformat()
    NGSI_DATA['dateObservedTo'] = ts.isoformat()
    # print(json.dumps(NGSI_DATA, indent=1))
    res = push_ngsi_orion(NGSI_DATA, ORION_URL_ROOT, ORION_USERNAME, ORION_PASSWORD)
    return res


def main():
    args = get_args()
    storedquery = args.storedquery
    endtime = create_datetime(args.endtime, hourly=True)
    if args.starttime is not None:
        starttime = create_datetime(args.starttime, hourly=True)
    else:
        starttime = endtime - datetime.timedelta(hours=args.timeperiod)
    for stationid in args.stationids:
        data = get_fmi_data(stationid, storedquery, starttime, endtime, args)
        data['source'] = get_fmi_api_url(stationid, storedquery, starttime, endtime, args)
        res = send_to_ngsi(data)
        print(res.status_code, res.text)


if __name__ == '__main__':
    main()
