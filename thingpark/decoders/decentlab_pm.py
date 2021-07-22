from broker.providers.decoder import DecoderProvider
from thingpark.parsers import parse_decentlab_pm


class DecentlabPmDecoder(DecoderProvider):
    description = 'Decode Decentlab PM payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = parse_decentlab_pm(hex_payload, port)
        return data
