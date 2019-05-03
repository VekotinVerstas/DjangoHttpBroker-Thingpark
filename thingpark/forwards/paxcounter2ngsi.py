import json
import logging

import requests

from broker.providers.forward import ForwardProvider

logger = logging.getLogger('runforwards')

ngsi_template = {
    "id": "000773207E3FFFFF",
    "type": "PaxcounterObserved",
    "dateObserved": "2019-03-19T04:52:52.652000+00:00Z",
    "WiFi": 14,
    "Bluetooth": 3,
    "location": {
        "coordinates": [
            24.949541,
            60.189692
        ],
        "type": "Point"
    },
    "address": {
        "addressCountry": "FI",
        "addressLocality": "Helsinki",
        "streetAddress": "Park Sinebrychoff"
    }
}


class Paxcounter2NGSIForward(ForwardProvider):
    description = 'Send data to a NGSI broker, e.g. Orion'

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

    def forward_data(self, datalogger, data, config):
        # Copy template
        m = ngsi_template.copy()
        # Replace data with real values
        m['id'] = datalogger.devid
        dline = data['datalines'][0]
        m['dateObserved'] = dline['time']
        if datalogger.lon and datalogger.lat:
            m['location']['coordinates'] = [datalogger.lon, datalogger.lat]
        else:
            del m['location']
            m['WiFi'] = dline['data'].get('wifi')
            m['Bluetooth'] = dline['data'].get('ble')

        if m['WiFi'] is None and m['Bluetooth'] is None:
            logger.warning(f'Paxcounter {datalogger.devid} without wifi or ble data')
            return False
        m['address'] = {
            "addressCountry": datalogger.country,
            "addressLocality": datalogger.locality,
            "streetAddress": datalogger.street
        }
        logger.debug(json.dumps(m, indent=2))
        # POST data to an endpoint, which is defined in Forward's or DataloggerForward's config field
        # TODO: add authentication and other
        res = requests.post(config['url'], json=m)
        if 200 <= res.status_code < 300:
            logger.info(f'POST request to {config["url"]} returned success code {res.status_code}')
            return True
        else:
            logger.warning(f'POST request to {config["url"]} returned error code {res.status_code}')
            return False
