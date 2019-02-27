from broker.providers.forward import ForwardProvider


class AQBurk2NGSIForward(ForwardProvider):
    description = 'Send data to a NGSI broker, e.g. Orion'

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

    def forward_data(self, data):
        print(data)
        return True
