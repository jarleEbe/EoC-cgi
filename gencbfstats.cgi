#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division

#pylint: disable=C0103
#pylint: disable=C0111
#pylint: disable=C0301

# if we want to give our script parameters, we need a special library
#import urllib3
import sys, os, re, json, cgi, cgitb, codecs, subprocess
import requests
from pprint import pprint
from subprocess import Popen, PIPE

reload(sys)
sys.setdefaultencoding("utf-8")

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# FUNCTIONS
def getPRloglikelihood(args):

    raysonPath = 'http://ucrel.lancs.ac.uk/cgi-bin/llsimple.pl?' + args #f1=511&f2=1848&t1=1578549&t2=16494070"
#    http = urllib3.PoolManager()
#    result = http.request('GET', raysonPath)
    result = requests.get(raysonPath)
    if result.status_code != 200:
        raise Exception(result.status_code)
    textcontent = result.text
    content = textcontent.splitlines()
    overunder = ''
    for myline in content:
        if re.search('Word', myline):
            therow = re.sub(r'\s+', ' ', myline).strip()
            thecols = therow.split(" ")
            overunder = str(thecols[5])

    return overunder

# MAIN

scriptpath = '/home/jarlee/prog/R/script/'
chi2test = 'scriptchi2Test.R'
Rscript = 'Rscript '

jsonParam = ''
normSize = 1000000
form = cgi.FieldStorage()

if form.has_key('json'):
    jsonParam = str(form.getvalue('json'))
else:
    jsonParam = ''

inputData = json.loads(jsonParam)
#inputDataSpruce = json.dumps(inputData)
inputtotnoWords = inputData['totnoWords']
#with open('resultcbf.json') as data_file:
#    inputData = json.load(data_file)
#inputDataSpruce = json.dumps(inputData)

with open('cbf.json') as data_file:
    allData = json.load(data_file)
#allDataSpruce = json.dumps(allData)
alltotnoWords = allData['totnoWords']

inputMale = inputData['male']
allMale = allData['male']
male = (inputMale / allMale) * normSize
maleSpruce = "%.2f" % male

inputFemale = inputData['female']
allFemale = allData['female']
female = (inputFemale / allFemale) * normSize
femaleSpruce = "%.2f" % female

#print("Content-Type: text/html")
#print("\n\n")

statsDict = dict()
statsDict['male'] = str(maleSpruce)
statsDict['noMaleWords'] = str(allMale)
statsDict['noFemaleWords'] = str(allFemale)
statsDict['female'] = str(femaleSpruce)
statsDict['Decades'] = dict()
statsDict['Pvalues'] = dict()
for decade, words in inputData['Decades'].items():
    if decade in allData['Decades']:
        totDecadeWords = allData['Decades'][decade]
        ResNorm = (words / totDecadeWords) * normSize
        ResNormSpruce = "%.2f" % ResNorm
        statsDict['Decades'][decade] = str(ResNormSpruce)
        noWords = alltotnoWords - totDecadeWords
        noHits = inputtotnoWords - words
        arguments = 'f1=' + str(words) + '&f2=' + str(noHits) + '&t1=' + str(totDecadeWords) + '&t2=' + str(noWords)
        plusminus = getPRloglikelihood(arguments)
        arg1 = str(words)
        arg2 = str(totDecadeWords)
        arg3 = str(noHits)
        arg4 = str(noWords)
        ps = subprocess.Popen(['Rscript', scriptpath+chi2test, arg1, arg2, arg3, arg4], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, stderror = ps.communicate()
        outputlines = str(output)
        outputarr = outputlines.splitlines()
        pValue = ''
        for line in outputarr:
            if re.search('p-value', line):
                pValue = line
                pValue = re.sub(r'^(.*)p-value = ', '', pValue)
        if re.search('e', pValue):
            pValue = '< 0.001' + plusminus
        else:
            pValueSpruce = float(pValue)
            pValueSpruce = "%.3f" % pValueSpruce
            pValue = str(pValueSpruce) + ' ' + plusminus
        statsDict['Pvalues'][decade] = pValue

jsonString = json.dumps(statsDict, indent=4, ensure_ascii=False)

print("Content-Type: text/html")
print("\n\n")
print(jsonString)
