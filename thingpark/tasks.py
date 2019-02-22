from celery import shared_task
from .utils import get_datalogger


@shared_task
def process_data(devid, data):
    datalogger, created = get_datalogger(devid)
    print(data)
