import django
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "httpbroker.settings")
django.setup()

from thingpark.models import Datalogger
from thingpark.utils import get_datalogger

print("""
Currently this script import certain set of Dataloggers and is not intended to any other use.
TODO: make more generic.
exit()
""")
exit()

"""
Add CSV as first argument, contents like
0111;373773207E330111;Tallberginkatu 1;Helsinki;60.161745,24.903632
"""

# Reference datalogger 
dl = Datalogger.objects.get(devid='373773207E33011C')
d = dl.decoder
fo = dl.forwards.all()[0]
print(dl, fo, d)

with open(sys.argv[1], 'rt') as f:
    lines = f.readlines()
    lines = [x.strip() for x in lines]

for l in lines:
    fields = l.split(';')
    if fields[1] == dl.devid:
        continue
    dn, created = get_datalogger(devid=fields[1], update_activity=False)
    dn.name = fields[0]
    dn.street = fields[2] if fields[2] else ''
    dn.locality = fields[3] if fields[3] else ''
    dn.lat = float(fields[4].split(',')[0]) if fields[4] else None
    dn.lon = float(fields[4].split(',')[1]) if fields[4] else None
    dn.decoder = dl.decoder
    dn.save()
    dn.forwards.add(fo)
    print(l)
