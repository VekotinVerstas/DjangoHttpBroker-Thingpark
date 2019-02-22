import datetime
from django.http.response import HttpResponse
from broker.endpoint import EndpointProvider
from broker.utils import serialize_django_request, data_pack
from thingpark.utils import get_datalogger, decode_json_body
from thingpark.tasks import process_data
from broker.utils import send_message

class ThingparkEndpoint(EndpointProvider):
    description = 'Receive HTTP POST requests from Actility Thingpark system'

    def handle_request(self, request):
        serialised_request = serialize_django_request(request)
        devid = request.GET.get('LrnDevEui', 'unknown')
        serialised_request['devid'] = devid
        serialised_request['time'] = datetime.datetime.utcnow().isoformat() + 'Z'
        packed_request = data_pack(serialised_request)
        KEY_PREFIX = 'fvh.digita'  # TODO: from settings or endpoint config
        key = f'{KEY_PREFIX}.{devid}'
        send_message(packed_request, key)

        ok, body = decode_json_body(serialised_request['request.body'])
        if ok is False:
            return HttpResponse(f'JSON ERROR: {body}', status=400, content_type='text/plain')
        uplink = body.get('DevEUI_uplink')
        if uplink is not None:
            # devid = uplink.get('DevEUI')
            datalogger, created = get_datalogger(devid=devid, update_activity=True)
            if devid is not None:
                process_data.delay(devid, serialised_request)
                # process_data.delay(devid, packed_request)
        return HttpResponse('OK', content_type='text/plain')
