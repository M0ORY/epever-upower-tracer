#!/usr/bin/python
import sys
import datetime
import time
import minimalmodbus
from influxdb import InfluxDBClient
from SolarTracer import *

# influx configuration - edit these
ifuser = "grafana"
ifpass = "solar"
ifdb   = "solar"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "solar"


up = SolarTracer()
if (up.connect() < 0):
	print "Could not connect to the device"
	exit -2

# get timestamps
localtime = time.localtime()
timestamp = time.strftime("%H:%M:%S", localtime)
timestamp = datetime.datetime.utcnow()

# calculate compound values
PVwatt = up.readReg(PVwattH)
PVwatt = ((int(PVwatt) << 16) + up.readReg(PVwattL));
DCwatt = up.readReg(DCwattH)
DCwatt = ((int(DCwatt) << 16) + up.readReg(DCwattL));

# We create a compund value of BAcurr becase BAamps is misleading BAamps is the output current of the buck converter including any load
# so actual battery current is BAamps minus DCamps and we round that to 2 decimal places
BAcurr = up.readReg(BAamps) - up.readReg(DCamps);
BAcurr = round(BAcurr, 2)

# form a data record
body_solar = [
    {
        "measurement": measurement_name,
        "time": timestamp,
        "fields": {
            "PVvolt": float(up.readReg(PVvolt)),
            "PVamps": float(up.readReg(PVamps)),
            "PVwatt": float(PVwatt),
            "PVkwh": float(up.readReg(PVkwhTotal)),
            "PVkwh2d": float(up.readReg(PVkwhToday)),
            "BAvolt": float(up.readReg(BAvolt)),
            "BAamps": float(up.readReg(BAamps)),
	    "BAcurr": float(BAcurr)
            "BAperc": float(up.readReg(BAperc)),
            "DCvolt": float(up.readReg(DCvolt)),
            "DCamps": float(up.readReg(DCamps)),
            "DCwatt": float(DCwatt),
            "DCkwh": float(up.readReg(DCkwhTotal)),
            "DCkwh2d": float(up.readReg(DCkwhToday)),
        }
    }
]

print body_solar

# connect to influx
ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)
# write the measurement
ifclient.write_points(body_solar)
