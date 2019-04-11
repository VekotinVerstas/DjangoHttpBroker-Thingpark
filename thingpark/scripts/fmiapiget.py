import argparse
import datetime
import json
import logging
import math
import os
import time
import pytz
import requests
import xmltodict
from dateutil.parser import parse

time_fmt = '%Y-%m-%dT%H:%MZ'

"""
# Example request URL
https://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=urban::observations::airquality::hourly::multipointcoverage&geoId=-106948

105406 100662 101004 106948 100742 106422 100762 106950 100803 104058 100691 100723 106949 105405 104056 101001 104048 106423 105417 100763 106951

# Example measuring stations
Helsinki Eteläsatama             105406
Helsinki Kallio 2                100662
Helsinki Kumpula                 101004
Helsinki Länsisatama 4           106948
Helsinki Mannerheimint.          100742
Helsinki Mechelininkatu          106422
Helsinki Mäkelänkatu             100762  
Helsinki Pirkkola                106950  
Helsinki Vartiokylä Huivipolku   100803
Hyvinkää                         104058
Espoo Leppävaara Läkkisepänkuja  100691
Espoo Luukki                     100723
Espoo Länsiväylä Friisilä        106949    
Kauniainen Kauniaistentie        105405
Vantaa Itä-Hakkila               104056
Vantaa Kaivoksela                101001
Vantaa Lentoasema                104048
Vantaa Rekola                    106423        
Vantaa Rekola etelä              105417    
Vantaa Tikkurila Neilikkatie     100763    
Vantaa Tikkurila Talvikkitie     106951    

All stations:
https://ilmatieteenlaitos.fi/havaintoasemat

Example request for weather observations:
http://opendata.fmi.fi/wfs?request=GetFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100971&timestep=10
http://opendata.fmi.fi/wfs?request=GetFeature&storedquery_id=fmi::observations::weather::multipointcoverage&geoid=-16000150&timestep=10


"""


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", dest="log", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='ERROR', help="Set the logging level")
    parser.add_argument('-q', '--quiet', action='store_true', help='Never print a char (except on crash)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Print some informative messages')
    parser.add_argument('-o', '--outformat', required=True, choices=['csv', 'json', 'pprint'], help='Output format')
    parser.add_argument('--starttime', help='Endtime in YYYY-mm-ddTHH:MM:SSZ format. Default is endtime-24h')
    parser.add_argument('--endtime', help='Endtime in YYYY-mm-ddTHH:MM:SSZ format. Default is current time')
    parser.add_argument('--timeperiod', type=int, default=24,
                        help='Start time delta from endtime in hours (e.g. 12 (hours))')
    parser.add_argument("--timestep", dest="timestep", choices=['10', '60'],
                        default='60', help="timestep parameter value in FMI URL")
    parser.add_argument('--storedquery', help='Stored query. Must be multipointcoverage type',
                        default='urban::observations::airquality::hourly::multipointcoverage')
    parser.add_argument('--stationids', required=True, nargs='+', default=[],
                        help='FMISID, see possible values from https://ilmatieteenlaitos.fi/havaintoasemat ')
    parser.add_argument('-i', '--idfield', required=True, default='geoid', choices=['geoid', 'fmisid'],
                        help='Id parameter name')
    parser.add_argument('--extraparams', nargs='+', default=[],
                        help='Additional parameters to output json in "key1=val1 [key2=val2 key3=val3 ...]" format')
    parser.add_argument('-n', '--nocache', action='store_true', help='Do not use cached xml data')
    args = parser.parse_args()
    if args.log:
        logging.basicConfig(level=getattr(logging, args.log))
    return args


def get_fmi_api_url(geoid, storedquery, starttime, endtime, args):
    s_str = starttime.strftime(time_fmt)
    e_str = endtime.strftime(time_fmt)
    idfield = args.idfield
    timestep = args.timestep
    if idfield == 'fmisid' or geoid.startswith('-'):
        prefix = ''
    else:
        prefix = '-'
    url = f'https://opendata.fmi.fi/wfs?' \
        f'request=getFeature&storedquery_id={storedquery}&' \
        f'{idfield}={prefix}{geoid}&startTime={s_str}&endTime={e_str}&timestep={timestep}'
    logging.info(f'Fetching data from: {url}')
    return url


def get_data_from_fmi_fi(geoid, storedquery, starttime, endtime, args):
    s_str = starttime.strftime(time_fmt)
    e_str = endtime.strftime(time_fmt)
    url = get_fmi_api_url(geoid, storedquery, starttime, endtime, args)
    fname = 'fmi_{}_{}-{}.xml'.format(geoid, s_str.replace(':', ''), e_str.replace(':', ''))
    if os.path.isfile(fname) and args.nocache is False:
        logging.info(f'Cache file already exists: {fname}')
    else:
        res = requests.get(url)
        logging.info(f'Saving to cache file: {fname}')
        with open(fname, 'wt') as f:
            f.write(res.text)
    return fname


def fmi_xml_to_dict(fname):
    with open(fname, 'rt') as f:
        d = xmltodict.parse(f.read())
    return d


def get_fmi_data_week_max(geoid, storedquery, starttime, endtime, args):
    fmi_xml = get_data_from_fmi_fi(geoid, storedquery, starttime, endtime, args)
    d = fmi_xml_to_dict(fmi_xml)
    # Base element for all interesting data
    try:
        base = d["wfs:FeatureCollection"]["wfs:member"]["omso:GridSeriesObservation"]

    except KeyError as err:
        if 'ExceptionReport' in d:
            print('ERROR: FMI sent us an exception:\n')
            print('\n'.join(d['ExceptionReport']['Exception']['ExceptionText']))
            print()
            raise
        exit(1)
    # Name & nocation
    base_position = base["om:featureOfInterest"]["sams:SF_SpatialSamplingFeature"]["sams:shape"]["gml:MultiPoint"][
        "gml:pointMember"]["gml:Point"]

    name = base_position["gml:name"]
    lat, lon = [float(x) for x in base_position["gml:pos"].split(' ')]
    # Timestamps
    raw_ts = base["om:result"]["gmlcov:MultiPointCoverage"]["gml:domainSet"]["gmlcov:SimpleMultiPoint"][
        "gmlcov:positions"]
    # Datalines, values are space separated
    raw_dl = base["om:result"]["gmlcov:MultiPointCoverage"]["gml:rangeSet"]["gml:DataBlock"][
        "gml:doubleOrNilReasonTupleList"]
    # Data types, list of swe:field elements
    raw_dt = base["om:result"]["gmlcov:MultiPointCoverage"]["gmlcov:rangeType"]["swe:DataRecord"]['swe:field']
    data_names = [x['@name'] for x in raw_dt]
    timestamp_lines = [int(a.split()[2]) for a in raw_ts.strip().splitlines()]
    raw_data_lines = raw_dl.splitlines()
    data_lines = []
    for raw_data_line in raw_data_lines:
        # Convert all numeric values to floats and NaN to None
        data_values = [x if not math.isnan(float(x)) else None for x in raw_data_line.strip().split(' ')]
        # Create list of key value pairs
        keyvalues = list(zip(data_names, data_values))
        data_lines.append(keyvalues)
    return name, lat, lon, timestamp_lines, data_lines


def get_fmi_data(geoid, storedquery, starttime, endtime, args):
    name, lat, lon, t_timestamp_lines, t_data_lines = None, None, None, [], []
    temp_starttime = starttime
    timestamp_lines = []
    data_lines = []
    while temp_starttime <= endtime:
        temp_endtime = temp_starttime + datetime.timedelta(hours=7 * 24)
        if temp_endtime > endtime:
            temp_endtime = endtime
        logging.debug(f'Getting time period {temp_starttime} - {temp_endtime}')
        name, lat, lon, t_timestamp_lines, t_data_lines = get_fmi_data_week_max(geoid, storedquery, temp_starttime,
                                                                                temp_endtime, args)
        timestamp_lines += t_timestamp_lines
        data_lines += t_data_lines
        temp_starttime = temp_starttime + datetime.timedelta(hours=7 * 24)
        logging.info('Sleeping')
        time.sleep(1)
    parsed_lines = []
    for i in range(len(timestamp_lines)):
        timestmap = datetime.datetime.utcfromtimestamp(timestamp_lines[i])
        parsed_line = {
            'time': timestmap.isoformat() + 'Z',
            'data': data_lines[i]
        }
        parsed_lines.append(parsed_line)
    data = {
        'devid': str(geoid),
        'name': name,
        'location': {'type': 'Point', 'coordinates': [lon, lat]},
        'datalines': parsed_lines,
    }
    if args.extraparams:
        data.update(dict([x.split('=') for x in args.extraparams]))
    return data


def create_datetime(date_str, hourly=True):
    if date_str is None:
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    else:
        d = parse(date_str)
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        raise ValueError('Start and end time strings must contain timezone information')
    if hourly:
        d = d.replace(minute=0, second=0, microsecond=0)
    return d


def pretty_print(data):
    for dl in data['datalines']:
        print(f"{dl['time']}")
        # maxlen = len(max([x[0] for x in dl['data']], key=len))
        # print(maxlen)
        for d in dl['data']:
            print(f"    {d[0]:20} = {d[1]}")


def csv_print(data):
    row = ','.join([str(x[0]) for x in data['datalines'][0]['data']])
    print(f"time,{row}")
    for dl in data['datalines']:
        row = ','.join([str(x[1]) for x in dl['data']])
        print(f"{dl['time']},{row}")


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
        if args.outformat == 'pprint':
            pretty_print(data)
        elif args.outformat == 'csv':
            csv_print(data)
        elif args.outformat == 'json':
            print(json.dumps(data))
        else:
            raise ValueError("not implemented yet")


if __name__ == '__main__':
    main()
