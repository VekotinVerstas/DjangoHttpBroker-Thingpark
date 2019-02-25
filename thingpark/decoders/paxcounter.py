from broker.providers.decoder import DecoderProvider
from thingpark.parsers.paxcounter import parse_paxcounter


class PaxcounterDecoder(DecoderProvider):
    description = 'Decode PAXCOUNTER payload'

    def decode_payload(self, hex_payload):
        # TODO: decode payload
        return parse_paxcounter(hex_payload)
