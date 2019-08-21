from broker.providers.decoder import DecoderProvider
from thingpark.parsers import mcf88


class Mcf88Decoder(DecoderProvider):
    description = 'Decode MCF88 payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = mcf88.parse_mcf88(hex_payload, port)
        return data
