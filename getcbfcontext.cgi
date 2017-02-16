#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

#pylint: disable=C0103
#pylint: disable=C0111
#pylint: disable=C0301

# if we want to give our script parameters, we need a special library
import sys
import os
import re
import codecs
import requests
import json
import cgi
import cgitb

from elasticsearch import Elasticsearch

reload(sys)
sys.setdefaultencoding("utf-8")

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# FUNCTIONS



def localidquery(es, index_name, document_type, tid, lid):

    searchstring = '{"query": {"bool": {"must": [ {"term": {"textId": "' + tid + '"}}, {"term": {"localId": ' + str(lid) + '}}]}}}'

    data = json.dumps({})
    tempdict = json.dumps(searchstring)
    data = json.loads(tempdict)

    myResult = es.search(index=index_name, doc_type=document_type, body=data)

    return myResult

# MAIN

query = ''
form = cgi.FieldStorage()

if form.has_key('sunitid'):
    query = str(form.getvalue('sunitid'))
else:
    query = ''

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

print("Content-Type: text/html")
print("\n\n")
if not query:
    sys.exit()

query = query.strip()
templist = list()
templist = query.split('.')
textid = str(templist[0])
tempid = str(templist[1])
tempid = re.sub(r'^s', '', tempid)
localid = int(tempid)
startid = localid - 4
endid = localid + 5

if startid < 1:
    startid = 1
hitsarr = []
resultdict = dict()
therange = 0
for ind in range(startid, endid):
    result = localidquery(es, "cbf", "cbfraw", textid, ind)
    parsed_data = json.dumps(result)
    sunit = json.loads(parsed_data)
    lid = sunit['hits']['hits'][0]['_source']['localId']
    localdict = {}
    localdict['sunitId'] = sunit['hits']['hits'][0]['_source']['sunitId']
    localdict['rawText'] = sunit['hits']['hits'][0]['_source']['rawText']
    therange += 1
    hitsarr.append(localdict.copy())

resultdict['Range'] = therange
resultdict['Context'] = hitsarr
jsonString = json.dumps(resultdict, indent=4)
print(jsonString)

#hitsarr = []
#totalnumberofhits = 0
