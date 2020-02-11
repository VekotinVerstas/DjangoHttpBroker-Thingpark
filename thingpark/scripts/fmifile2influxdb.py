import sys
import json
import influxdb
from influxdb.exceptions import InfluxDBClientError


# from broker.utils.influxdb import get_influxdb_client, create_influxdb_objects


def get_influxdb_client(database, host='127.0.0.1', port=8086):
    iclient = influxdb.InfluxDBClient(host=host, port=port, database=database)
    iclient.create_database(database)
    return iclient


def create_influxdb_objects(data, measurement_name, extratags=None):
    """
    Convert a "parsed data object" (example below) to an InfluxDB object.

    data =
    {
        "devid": "373773207E33011C",
        "datalines": [
            {
                "time": "2019-03-11T12:49:09.239162+00:00",
                "data": {
                    'pm25min': 0.2, 'pm25max': 0.3, 'pm25avg': 0.2, 'pm25med': 0.2,
                    'pm10min': 0.2, 'pm10max': 1.3, 'pm10avg': 0.7, 'pm10med': 0.6,
                    'temp': 22.5, 'humi': 22.0, 'pres': 1021.6, 'gas': 826.6,
                    'rssi': '-81.000000'
                }
            }
        ]
    }

    Specially note that "data" may be also a list of key-value pairs: [
        ["t2m", "4.5"], ["ws_10min", "7.3"], ["wg_10min", "13.2"], ["wd_10min", "199.0"],
        ["rh", "97.0"], ["td", "4.1"], ["r_1h", "0.5"], ["ri_10min", "0.0"], ["snow_aws", "0.0"],
        ["p_sea", "964.2"], ["vis", "19643.0"], ["n_man", "8.0"], ["wawa", "81.0"]
    ]

    :param dict data: Data object, see example above
    :param str measurement_name: Measurement's name
    :param dict extratags: Additional InfluxDB measurement tags
    :return: InfluxDB measurement object
    """
    devid = data['devid']
    measurements = []
    for d in data['datalines']:
        measurement_obj = {
            "measurement": measurement_name,
            "tags": {
                "dev-id": devid,
            },
            "time": d['time'],
            "fields": dict(d['data'])  # Data may be a list of key-value lists / tuples
        }
        if extratags is not None:
            measurement_obj['tags'].update(extratags)
        measurements.append(measurement_obj)
    return measurements


if __name__ == '__main__':

    with open(sys.argv[1]) as f:
        lines = f.readlines()

    iclient = get_influxdb_client('fmisaa')

    for line in lines:
        d = json.loads(line)
        measurements = create_influxdb_objects(d, 'fmisaa', extratags={})
        try:
            iclient.write_points(measurements)
            print('wrote {} measurements'.format(len(measurements)))
        except InfluxDBClientError as err:
            err_msg = f'InfluxDB error: {err}'
            print(err_msg)
            # logger.error(f'devid={devid} {err_msg}')
        # print(json.dumps(measurements, indent=1))
        # exit()
