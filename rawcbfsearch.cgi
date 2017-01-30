#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

#pylint: disable=C0103
#pylint: disable=C0111

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
    regexpchar = re.compile(r'[\.\*\+\?\[\{\(\|]')
    if re.search(regexpchar, q):
        searchstring = '{"from": 0, "size": ' + size + ', "query": {"bool": {"must": [ {"regexp": {"rawText": "' + q + '"}} ]' + theFilter + \
            '}}}'
    else:
        searchstring = '{"from": 0, "size": ' + size + ', "query": {"bool": {"must": [ {"match": {"rawText": "' + q + '"}} ]' + theFilter + \
            '}}}'

    data = json.dumps({})
    tempdict = json.dumps(searchstring)
    data = json.loads(tempdict)

    result = es.search(index=index_name, doc_type=document_type, body=data)

    return result


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
        term = re.sub('_', ' ', term)
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

    result = es.search(index=index_name, doc_type=document_type, body=data)

    return result


# MAIN

query = ''
filters = ''
max_no_hits = 1000
form = cgi.FieldStorage()

if form.has_key('q'):
    query = str(form.getvalue('q'))
else:
    query = ''
if form.has_key('nohits'):
    max_no_hits = str(form.getvalue('nohits'))
else:
    max_no_hits = 1000
if form.has_key('filter'):
    filters = str(form.getvalue('filter'))
else:
    filters = ''

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

print("Content-Type: text/html")
print("\n\n")
if not query:
    sys.exit()

#query = input
#print(query)
query = query.strip()
if re.search(" ", query):
    result = complex_query(es, "cbf", "cbfraw", query, max_no_hits, filters)
else:
    result = simple_query(es, "cbf", "cbfraw", query, max_no_hits, filters)

# print(result)
# print("\n")

parsed_data = json.dumps(result)

#print(parsed_data)
#print("\n")

sunit = json.loads(parsed_data)

#print(json.dumps(sunit, indent=4))
# print("\n")

result = dict()
result['requestednoHits'] = max_no_hits
result['searchstring'] = query
result['numberofHits'] = sunit['hits']['total']

#print(sunit['hits']['total'])

# print(sunit['hits']['hits'][0]['highlight']['sunit'])
# print("\n")

para = list()
hitsarr = []
totalnumberofhits = 0
delimiter = '([\\s,;:.<>!?_~/—–‘’“”`´\"\\(\\)]+?)'
#    query = ' ' + query + ' '
query = re.sub(' ', unicode(delimiter), query)
query = re.sub('_', ' ', query)
#print(query)
#    if re.search('—', query):
#        print(query)
pattern = re.compile(query, flags=re.IGNORECASE|re.UNICODE)
for row in sunit["hits"]["hits"]:
    localDict = {}
    localDict['Title'] = row["_source"]["title"]
    localDict['Author'] = row["_source"]["author"]
    localDict['Decade'] = row["_source"]["decade"]
    localDict['Sex'] = row["_source"]["sex"]
    localDict['textId'] = row["_source"]["textId"]
    localDict['sunitId'] = row["_source"]["sunitId"]
    localDict['localId'] = row["_source"]["localId"]
    para = row["_source"]["rawText"]
#    print(para)
    ind = 0
#    pattern": "([\\s.,;:<>$=!?#_@%+~/—–‘’“”§¶…`´\"\\{\\}\\[\\]\\(\\)\\*]+)"
#"—
#    delimiter = '([\\s,;:.<>!?_~/—–‘’“”`´\"\\(\\)]+?)'
#    query = ' ' + query + ' '
#    query = re.sub(' ', unicode(delimiter), query)
#    query = re.sub('_', ' ', query)
#    print(query)
#    if re.search('—', query):
#        print(query)
#    pattern = re.compile(query, flags=re.IGNORECASE|re.UNICODE)
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
#           print(rest)
#           print(str(len(rest)))
            rest = re.sub(pattern, '', rest, 1)
#           print(rest)
#           print(str(len(rest)))
#           print(str(len(para)))
            endofqueryindex = len(para) - len(rest)
#           print(str(endofqueryindex))
#            print(temp)
#            print(stringsofar)
#            print(rest)
        if ind == endofqueryindex:
            orig = orig + '</b>'
        orig = orig + c
        ind += 1
#    print(str(numberofmatches))
#    print("\n")
    if numberofmatches > 1:
        for ind in range(0, numberofmatches):
            temp = orig
            temp = temp.replace('<b>', '<c>', 1)
            temp = temp.replace('</b>', '</c>', 1)
            temp = temp.replace('<b>', '')
            temp = temp.replace('</b>', '')
            temp = temp.replace('<c>', '<b>')
            temp = temp.replace('</c>', '</b>')
#            print(temp)
            localDict['sunit'] = temp
            hitsarr.append(localDict.copy())
#            jsontemp = json.dumps(localDict, indent=4)
#            print(jsontemp)
#            print(orig)
            orig = orig.replace('<b>', '', 1)
            orig = orig.replace('</b>', '', 1)
    else:
        localDict['sunit'] = orig
        hitsarr.append(localDict)
#        print(orig)
result['numberofHits'] = str(totalnumberofhits)
result['Hits'] = hitsarr
jsonString = json.dumps(result, indent=4)
print(jsonString)
