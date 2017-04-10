#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

#pylint: disable=C0103
#pylint: disable=C0111
#pylint: disable=C0301

# if we want to give our script parameters, we need a special library
import sys, os, re, requests, json, cgi, cgitb, codecs
from pprint import pprint


reload(sys)
sys.setdefaultencoding("utf-8")

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# FUNCTIONS

# MAIN

query = ''
normSize = 1000000
form = cgi.FieldStorage()

if form.has_key('sunitid'):
    query = str(form.getvalue('sunitid'))
else:
    query = ''

#    parsed_data = json.dumps(result)
#    sunit = json.loads(parsed_data)
#    lid = sunit['hits']['hits'][0]['_source']['localId']
#    localdict = {}
#    localdict['sunitId'] = sunit['hits']['hits'][0]['_source']['sunitId']
#    localdict['rawText'] = sunit['hits']['hits'][0]['_source']['rawText']
#    therange += 1
#    hitsarr.append(localdict.copy())

with open('resultcbf.json') as data_file:
    inputData = json.load(data_file)
inputDataSpruce = json.dumps(inputData)


with open('cbf.json') as data_file:
    allData = json.load(data_file)
allDataSpruce = json.dumps(allData)

print("Content-Type: text/html")
print("\n\n")
pprint(allDataSpruce)
print("<br/><br/>")
pprint(inputDataSpruce)
print("<br/><br/>")

inputMale = inputData['male']
allMale = allData['male']
male = (inputMale / allMale) * normSize
maleSpruce = "%.2f" % male

inputFemale = inputData['female']
allFemale = allData['female']
female = (inputFemale / allFemale) * normSize
femaleSpruce = "%.2f" % female

statsDict = dict()
statsDict['male'] = str(maleSpruce)
statsDict['female'] = str(femaleSpruce)
statsDict['Decades'] = dict()
for decade, words in inputData['Decades'].items():
    if decade in allData['Decades']:
        totDecadeWords = allData['Decades'][decade]
        ResNorm = (words / totDecadeWords) * normSize
        ResNormSpruce = "%.2f" % ResNorm
        statsDict['Decades'][decade] = str(ResNormSpruce)

jsonString = json.dumps(statsDict, indent=4, ensure_ascii=False)
print(jsonString)
