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
import pprint

from elasticsearch import Elasticsearch

reload(sys)
sys.setdefaultencoding("utf-8")

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)
sys.stdin = UTF8Writer(sys.stdin)

# FUNCTIONS


def get_filters(filters):

#    print(filters)

    myFilterDict = dict()

    myfilters = list()
    if re.search(" ", filters):
        myfilters = filters.split(" ")
    else:
        myfilters.append(filters)

    key = ''
    value = ''
    filters_exist = False
    if len(myfilters) > 1:
        for row in myfilters:
            myonefilter = list()
            if re.search("=", row):
                myonefilter = row.split("=")
                key = myonefilter[0]
                value = myonefilter[1]
                myFilterDict[key] = value
                filters_exist = True
    elif len(myfilters) == 1:
        myonefilter = list()
        if re.search("=", filters):
            myonefilter = filters.split("=")
            key = myonefilter[0]
            value = myonefilter[1]
            myFilterDict[key] = value
            filters_exist = True
    else:
        filters_exist = False

    return(myFilterDict)


def simple_query(es, index_name, document_type, q, max_hits, filters):

    size = '5'
    if max_hits <= 0:
        size = '10'
    else:
        size = str(max_hits)

    FilterDict = get_filters(filters)
    theFilter = ''

    if len(FilterDict) >= 1:
        theFilter = ', "filter" : [ '
        for key in FilterDict:
            theFilter = theFilter + \
                '{ "term" : { "' + key + '" : "' + FilterDict[key] + '"}},'
        theFilter = re.sub(r',$', '', theFilter)
        theFilter = theFilter + ']'

    searchstring = ''
#    q = re.sub(r'\*', r'([^\\\s.;;:!<>_~/—–‘’“”`´\"\\\?\\\)\\\()]*)', q)
#    print(q)
    regexpchar = re.compile(r'[\.\*\+\?\[\{\(\|]')
    if re.search(regexpchar, q):
        searchstring = '{"from": 0, "size": ' + size + ', "query": {"bool": {"must": [ {"regexp": {"rawText": "' + q + '"}} ]' + theFilter + \
            '}}}'
    else:
        searchstring = '{"from": 0, "size": ' + size + ', "query": {"bool": {"must": [ {"match": {"rawText": "' + q + '"}} ]' + theFilter + \
            '}}}'

#    print(searchstring)
    data = json.dumps({})
    tempdict = json.dumps(searchstring)
    data = json.loads(tempdict)

    myResult = es.search(index=index_name, doc_type=document_type, scroll="5m", body=data, request_timeout=60)

    return myResult


def complex_query(es, index_name, document_type, q, max_hits, filters):

    size = '5'
    if max_hits <= 0:
        size = '10'
    else:
        size = str(max_hits)

    mylist = list()
    if re.search(" ", q):
        mylist = q.split(" ")

    FilterDict = get_filters(filters)
    theFilter = ''

    if len(FilterDict) >= 1:
        theFilter = ' "filter" : { "bool" : {"must": [ '
        for key in FilterDict:
            theFilter = theFilter + \
                '{ "term" : { "' + key + '" : "' + FilterDict[key] + '"}},'
        theFilter = re.sub(r',$', '', theFilter)
        theFilter = theFilter + ']}}}}'
    else:
        theFilter = ''

    body_start = ''
    body_end = ''

    body_start = '{"from" : 0, "size" : ' + size + \
        ', "query" : { "bool" : { "must" : { "span_near" : { "clauses" : [ '
    if theFilter == '':
        body_end = ' ], "slop" : 0, "in_order" : "true" }}}}}'
    else:
        body_end = ' ], "slop" : 0, "in_order" : "true" }},' + theFilter + '}'

    body_middle = list()
    searchterms = list()
    regexpchar = re.compile(r'[.+?\\*\\[\\{\\(\\|]')
    splitchar = re.compile(" ")
    searchterms = re.split(splitchar, q)
    for term in searchterms:
        term = term.strip()
#        term = re.sub('_', ' ', term)
        if re.search(regexpchar, term):
            to_append = ' { "span_multi" : { "match" : { "regexp": {"rawText": "' + term + '"}}}}'
            body_middle.append(to_append)
        else:
            to_append = ' { "span_term" : { "rawText": "' + term + '" }}'
            body_middle.append(to_append)

    searchstring = ''
    for jsonpart in body_middle:
        searchstring = searchstring + jsonpart + ','

    searchstring = re.sub(r',$', '', searchstring)

    searchstring = body_start + searchstring + body_end

#    print(searchstring)

    data = json.dumps({})
    tempdict = json.dumps(searchstring)
    data = json.loads(tempdict)

    myResult = es.search(index=index_name, doc_type=document_type, scroll="5m", body=data, request_timeout=60)

    return myResult

def scrolling(es, sid):

    thescroll = '{"scroll_id" : ' + sid + '}'
    scrollresult = es.scroll(scroll="5m", scroll_id=sid, request_timeout=60)

    return scrollresult


# MAIN

query = ''
filters = ''
max_no_hits = 5000
form = cgi.FieldStorage()

if form.has_key('q'):
    query = str(form.getvalue('q').decode('utf8'))
    sys.stderr.write(query)
else:
    query = ''
if form.has_key('nohits'):
    max_no_hits = str(form.getvalue('nohits'))
else:
    max_no_hits = 5000
if form.has_key('filter'):
    filters = str(form.getvalue('filter'))
else:
    filters = ''

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

print("Content-Type: text/html; charset=utf-8")
print("\n\n")
#print(sys.stdout.encoding)

if not query:
    sys.exit()

query = query.strip()
nonwordchar = '([^\\s.,;;:!<>_~/—–‘’“”`´\"\\?\\)\\(]*)'

if re.search(" ", query):
    if re.search(r'\w\*', query):
        query = re.sub(r'(\w)\*', ur'\1(.[^\\\s.,;;:!<>_~/—–‘’“”`´\"\\\?\\\)\\\(]*)', query)
    if re.search(r' \*', query):
        query = re.sub(r' \*', ur' (.[^\\\s.,;;:!<>_~/—–‘’“”`´\"\\\?\\\)\\\(]*)', query)
    result = complex_query(es, "cbf", "cbfraw", query, max_no_hits, filters)
else:
    query = re.sub(r'\*', ur'([^\\\s.,;;:!<>_~/—–‘’“”`´\"\\\?\\\)\\\(]*)', query)
    result = simple_query(es, "cbf", "cbfraw", query, max_no_hits, filters)

parsed_data = json.dumps(result)
sunit = json.loads(parsed_data)

result = dict()
result['requestednoHits'] = max_no_hits
result['searchstring'] = query
result['numberofHits'] = sunit['hits']['total']

scrollId = sunit['_scroll_id']

para = list()
hitsarr = []
totalnumberofhits = 0
male = 0
female = 0
unknownsex = 0
numberoftexts = {}
decades = {}
delimiter = '([\\s,;:.<>!?_~/—–‘’“”`´\"\\(\\)]+?)'
query = re.sub(' ', unicode(delimiter), query)
query = re.sub('_', ' ', query)
pattern = re.compile(unicode(query), flags=re.IGNORECASE|re.UNICODE)

while sunit['hits']['hits']:
    for row in sunit['hits']['hits']:
        localDict = {}
        localDict['Title'] = row["_source"]["title"]
        localDict['Author'] = row["_source"]["author"]
        localDict['Decade'] = row["_source"]["decade"]
        localDict['Sex'] = row["_source"]["sex"]
        localDict['textId'] = row["_source"]["textId"]
        localDict['sunitId'] = row["_source"]["sunitId"]
        localDict['localId'] = row["_source"]["localId"]
        para = row["_source"]["rawText"]
# Cheats by adding an extra blank in case hit is at end of line
        para = para + ' '
        currentkey = row["_source"]["textId"]
        thisdecade = row["_source"]["decade"]
        if thisdecade == '':
            thisdecade = 'Undated'
#            print(row["_source"]["textId"])
        if currentkey in numberoftexts:
            x = 1
        else:
            numberoftexts[currentkey] = row["_source"]["sex"]
        ind = 0
        orig = ''
        rest = ''
        numberofmatches = 0
        endofqueryindex = 1000000
        for c in para:
            temp = para[ind:len(para)]
            if re.match(pattern, temp):
                numberofmatches += 1
                totalnumberofhits += 1
                stringsofar = orig + '<b>' + temp
                orig = orig + '<b>'
                rest = para[ind:len(para)]
                rest = re.sub(pattern, '', rest, 1)
                endofqueryindex = len(para) - len(rest)
            if ind == endofqueryindex:
                orig = orig + '</b>'
            orig = orig + c
            ind += 1
        if numberofmatches > 1:
            for ind in range(0, numberofmatches):
                temp = orig
                temp = temp.replace('<b>', '<c>', 1)
                temp = temp.replace('</b>', '</c>', 1)
                temp = temp.replace('<b>', '')
                temp = temp.replace('</b>', '')
                temp = temp.replace('<c>', '<b>')
                temp = temp.replace('</c>', '</b>')
                localDict['sunit'] = temp
                hitsarr.append(localDict.copy())
                orig = orig.replace('<b>', '', 1)
                orig = orig.replace('</b>', '', 1)
                if row["_source"]["sex"] == 'male':
                    male += 1
                elif row["_source"]["sex"] == 'female':
                    female += 1
                else:
                    unknownsex += 1
                if thisdecade in decades:
                    dec = decades[thisdecade]
                    dec += 1
                    decades[thisdecade] = dec
                else:
                    decades[thisdecade] = 1
        else:
            localDict['sunit'] = orig
            hitsarr.append(localDict)
            if row["_source"]["sex"] == 'male':
                male += 1
            elif row["_source"]["sex"] == 'female':
                female += 1
            else:
                unknownsex += 1
            if thisdecade in decades:
                dec = decades[thisdecade]
                dec += 1
                decades[thisdecade] = dec
            else:
                decades[thisdecade] = 1
    newresult = scrolling(es, scrollId)
    new_parsed_data = json.dumps(newresult)
    sunit = json.loads(new_parsed_data)

result['numberofHits'] = str(totalnumberofhits)
result['male'] = str(male)
result['female'] = str(female)
result['numberofTexts'] = str(len(numberoftexts.keys()))
result['Decades'] = decades
result['Hits'] = hitsarr
jsonString = json.dumps(result, indent=4, ensure_ascii=False)
print(jsonString)
#pprint.pprint(result['Decades'])