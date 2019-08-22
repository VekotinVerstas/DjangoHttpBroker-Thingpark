from broker.providers.decoder import DecoderProvider
from thingpark.parsers import elsys


class ElsysDecoder(DecoderProvider):
    description = 'Decode ELSYS payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = elsys.parse_elsys(hex_payload, port)
        return data
