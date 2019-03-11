import json
from django.db import models
from django.core.exceptions import ValidationError
from broker.providers.decoder import DecoderProvider
from broker.models import Forward

decoders = DecoderProvider.get_plugins()
DECODER_HANDLER_CHOICES = [(f'{a.app}.{a.name}', f'{a.app}.{a.name}') for a in decoders]


class Datalogger(models.Model):
    devid = models.CharField(db_index=True, unique=True, max_length=256)
    name = models.CharField(max_length=256, blank=True)
    description = models.CharField(max_length=10000, blank=True)
    decoder = models.CharField(max_length=128, blank=True, choices=DECODER_HANDLER_CHOICES)
    forwards = models.ManyToManyField(Forward,
                                      blank=True,
                                      through="DataloggerForward",
                                      related_name="thingpark_dataloggers",
                                      verbose_name="Data to forward")
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    country = models.CharField(max_length=256, blank=True)
    locality = models.CharField(max_length=256, blank=True)
    street = models.CharField(max_length=256, blank=True)
    activity_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.devid} ({self.decoder})'


class DataloggerForward(models.Model):
    datalogger = models.ForeignKey(Datalogger, on_delete=models.CASCADE)
    forward = models.ForeignKey(Forward, on_delete=models.CASCADE, related_name='thingpark_forwards')
    config = models.TextField(default='{}', help_text='All required configuration parameters in JSON format')

    def __str__(self):
        return f'{self.datalogger} -> {self.forward}'

    def clean(self, exclude=None):
        try:
            config = json.loads(self.config)
        except json.JSONDecodeError as err:
            raise ValidationError(f'JSON error in config: {err}')
        self.config = json.dumps(config, indent=1)


# class LorawanMsg(models.Model):
#     datalogger = models.ForeignKey(Datalogger, on_delete=models.CASCADE)
#     rssi = models.CharField(max_length=256, blank=True)
#     received_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f'{self.datalogger}'
