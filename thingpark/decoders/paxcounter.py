from broker.providers.decoder import DecoderProvider


class PaxcounterDecoder(DecoderProvider):
    description = 'Decode PAXCOUNTER payload'

    def decode_payload(self, hex_payload):
        # TODO: decode payload
        return hex_payload
