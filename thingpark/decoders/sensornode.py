from broker.providers.decoder import DecoderProvider
from thingpark.parsers import parse_sensornode


class SensornodeDecoder(DecoderProvider):
    description = 'Decode Sensornode payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = parse_sensornode(hex_payload, port)
        return data
