#!/bin/env python

# convert service json output to covjson
# services: vpvs[irpinia, marmara, taboo, vrancea]
# input: json service output
# output: covjson

import json
import sys
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def data_validation(json_in):
    data_check = True
    nfo = None
    ddss = None
    schema_names = ["vpvs_irpinia", "vpvs_marmara", "vpvs_taboo", "vpvs_vrancea"]
    jschemas = []

    for jschm in schema_names:
        with open("json_schema/%s.json" % jschm, 'r') as f:
            jschemas.append(json.loads(f.read()))

    for jschm, jsname in zip(jschemas, schema_names):
        try:
            # json validation, check json schema and return nfo and ddss
            validate(instance=json_in, schema=jschm)
            ddss, nfo = jsname.split('_')
            break
        except ValidationError:
            pass

    return ddss, nfo


def data_converter(json_in, ddss, nfo):
    stalat = []
    stalon = []
    time = []
    series = []  # list of series
    series_name = []
    head = 0

    # for each obj in results extract time and values
    # TODO check MARMARA FIELDS
    fields_map = {"station_latitude": {"vpvs_taboo": "station_latitude", "vpvs_irpinia": "station_latitude",
            "vpvs_vrancea": "station_latitude", "vpvs_marmara": "station_latitude"},
        "station_longitude": {"vpvs_taboo": "station_longitude", "vpvs_irpinia": "station_longitude",
            "vpvs_vrancea": "station_longitude", "vpvs_marmara": "station_longitude"},
        "time": {"vpvs_taboo": "event_origin_time", "vpvs_irpinia": "event_origin_time",
            "vpvs_vrancea": "event_origin_time", "vpvs_marmara": "event_origin_time"},
        "latitude": {"vpvs_taboo": "event_latitude", "vpvs_irpinia": "event_latitude",
            "vpvs_vrancea": "event_latitude", "vpvs_marmara": "event_latitude"},
        "longitude": {"vpvs_taboo": "event_longitude", "vpvs_irpinia": "event_longitude",
            "vpvs_vrancea": "event_longitude", "vpvs_marmara": "event_longitude"},
        "value": {"vpvs_taboo": "vpvs_value", "vpvs_irpinia": "vpvs_value",
            "vpvs_vrancea": "vpvs_value", "vpvs_marmara": "vpvs_value"},
        "error": {"vpvs_taboo": "vpvs_error", "vpvs_irpinia": "vpvs_error",
            "vpvs_vrancea": "vpvs_error", "vpvs_marmara": "vpvs_error"}}
    # list of parameters to visualize
    fields_list = [{"name": "param", "field": "value", "desc": "", "symbol": "", "id": "", "label": "Vp/Vs"}]

    for ob in json_in["results"]:
        if head == 0:
            stalat = [float(ob[fields_map["station_latitude"]["%s_%s" % (ddss, nfo)]])]
            stalon = [float(ob[fields_map["station_longitude"]["%s_%s" % (ddss, nfo)]])]
            series_name.append(ddss)
            series.append([])  # inserisce array vuoto
            head = 1
        time.append(ob[fields_map["time"]["%s_%s" % (ddss, nfo)]])
        for fl in fields_list:
            series[fields_list.index(fl)].append(float(ob[fields_map[fl["field"]]["%s_%s" % (ddss, nfo)]]))

    # insert data into covjson model
    # insert in domain: station coords and time list
    # for each series: insert parameter in parameters, range in ranges
    cj_domain = {
        "type": "Domain",
        "domainType": "PointSeries",
        "axes": {
            "x": {"values": stalat},  # longitudine stazione
            "y": {"values": stalon},  # latitudine stazione
            "t": {"values": time}  # valori dei tempi
        },
        "referencing": [
            {
                "coordinates": ["x", "y"],
                "system": {
                    "type": "GeographicCRS",
                    "id": "http://www.opengis.net/def/crs/EPSG/0/4326"
                }
            },
            {
                "coordinates": ["t"],
                "system": {
                    "type": "TemporalRS",
                    "calendar": "Gregorian"
                }
            }
        ]
    }

    cj_parameters = {}
    cj_ranges = {}
    for fl in fields_list:
        cj_parameter = {
            "type": "Parameter",
            "description": {
                "en": fl["desc"]
            },
            "unit": {
                "symbol": fl["symbol"]
            },
            "observedProperty": {
                "id": fl["id"],
                "label": {
                    "en": fl["label"]
                }
            }
        }

        cj_parameters.update({"%s" % fl["name"]: cj_parameter})  # parameter name: parameter object

        cj_range = {
            "type": "NdArray",
            "dataType": "float",
            "axisNames": ["t"],
            "shape": [len(series[fields_list.index(fl)])],
            "values": series[fields_list.index(fl)]
        }

        cj_ranges.update({"%s" % fl["name"]: cj_range})  # range_name: range_object

    cjson = {
        "type": "Coverage",
        "domain": cj_domain,
        "parameters": cj_parameters,
        "ranges": cj_ranges
    }

    return cjson


################
# ### MAIN ### #
################

# __call__ function, usare questo anziche il __main__

data_err = {"error": "errors occurred"}

if len(sys.argv) < 2:
    print("Usage: python %s input_data" % sys.argv[0])
    exit(1)

# read from input
# data_in = {"results": []}

with open(sys.argv[1]) as jfile:
    data_in = json.load(jfile)

ddss, nfo = data_validation(data_in)
if nfo is not None and ddss is not None:
    print(json.dumps(data_converter(data_in, ddss, nfo)))
else:
    print(json.dumps(data_err))

exit(0)
'''
{
  "ranges": {
    "vpvs": {

      "axisNames": ["t"], 
      "shape": [44],
      "values": [],
    },
  },
},

'''