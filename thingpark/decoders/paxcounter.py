from broker.providers.decoder import DecoderProvider
from thingpark.parsers.paxcounter import parse_paxcounter


class PaxcounterDecoder(DecoderProvider):
    description = 'Decode PAXCOUNTER payload'

    def decode_payload(self, payload_hex, **kwargs):
        return parse_paxcounter(payload_hex, port=kwargs['port'])
