from broker.providers.decoder import DecoderProvider
from thingpark.parsers import parse_decentlab


class DecentlabDecoder(DecoderProvider):
    description = 'Decode Decentlab payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = parse_decentlab(hex_payload, port)
        return data
