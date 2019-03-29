import requests
import json
from broker.providers.forward import ForwardProvider

n = {
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
        m = n.copy()
        # Replace data with real values
        m['id'] = datalogger.devid
        m['dateObserved'] = data['time']
        if datalogger.lon and datalogger.lat:
            m['location']['coordinates'] = [datalogger.lon, datalogger.lat]
        else:
            del m['location']
        m['WiFi'] = data['data']['wifi']
        m['Bluetooth'] = data['data']['ble']
        m['address'] = {
            "addressCountry": datalogger.country,
            "addressLocality": datalogger.locality,
            "streetAddress": datalogger.street
        }
        # POST data to an endpoint, which is defined in Forward's or DataloggerForward's config field
        # TODO: add authentication and other
        res = requests.post(config['url'], json=m)
        # TODO: log result, status should be 200-204
        # print(json.dumps(m, indent=2))
        return True
