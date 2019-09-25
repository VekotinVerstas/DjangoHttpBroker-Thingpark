from broker.providers.decoder import DecoderProvider
from thingpark.parsers import parse_energiaburk


class EnergiaBurkDecoder(DecoderProvider):
    description = 'Decode EnergiaBurk payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = parse_energiaburk(hex_payload, port)
        return data
