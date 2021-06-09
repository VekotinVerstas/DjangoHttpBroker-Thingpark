from broker.providers.decoder import DecoderProvider
from fvhiot.parsers.dlmbx import decode_hex

class DlmbxDecoder(DecoderProvider):
    description = 'Decode Digital matter MBX payload'

    def decode_payload(self, hex_payload, port, **kwargs):
        data = decode_hex(hex_payload, port)
        # TODO: remove dl_id, protocol keys?
        return data
