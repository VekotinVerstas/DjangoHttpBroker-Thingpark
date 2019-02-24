from django.db import models
from broker.providers.decoder import DecoderProvider

decoders = DecoderProvider.get_plugins()
DECODER_HANDLER_CHOICES = [(f'{a.app}.{a.name}', f'{a.app}.{a.name}') for a in decoders]


class Datalogger(models.Model):
    devid = models.CharField(db_index=True, unique=True, max_length=256)
    name = models.CharField(max_length=256, blank=True)
    description = models.CharField(max_length=10000, blank=True)
    decoder = models.CharField(max_length=128, blank=True, choices=DECODER_HANDLER_CHOICES)
    activity_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.devid} ({self.decoder})'


class LorawanMsg(models.Model):
    datalogger = models.ForeignKey(Datalogger, on_delete=models.CASCADE)
    rssi = models.CharField(max_length=256, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.datalogger}'
