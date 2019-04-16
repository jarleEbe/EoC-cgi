#!/usr/bin/python
#pylint: disable=C0103
#pylint: disable=C0111

# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division

import sys, os, re, subprocess
from pprint import pprint
from subprocess import Popen, PIPE
from collections import OrderedDict

#MAIN
#singleFiles = re.compile("\.txt", flags=re.IGNORECASE)
referenceCorpus = 'WLL-refCorpus.txt'
scriptpath = '/home/jarlee/prog/R/script/'
LLtest = 'scriptLog-likelihood.R'
Rscript = 'Rscript '

if (len(sys.argv) <= 1):
   print('Need at least one inputfile.')
   exit()

singleFile = sys.argv[1]
print(singleFile)

refCorpusLines = dict()
totLemmasRefCorpus = 0;
with open(referenceCorpus) as file:
   for line in file: 
      line = line.strip()
      (lem, freq) = line.split("\t")
      totLemmasRefCorpus = totLemmasRefCorpus + int(freq)
      refCorpusLines[lem] = line


calcCorpusLines = dict()
totLemmasCalcCorpus = 0
with open(singleFile) as file:
   for line in file: 
      line = line.strip()
      (lem, freq) = line.split("\t")
      totLemmasCalcCorpus = totLemmasCalcCorpus + int(freq)
      calcCorpusLines[lem] = line

totRefCorpus = len(refCorpusLines)
totCalcCorpus = len(calcCorpusLines)

removeTotCalcFromTotRef = totLemmasRefCorpus - totLemmasCalcCorpus

LLSorted = dict()
for line in calcCorpusLines:
#   print(line, calcCorpusLines[line])
   values = str(calcCorpusLines[line])
   (lem, freq) = values.split("\t")
   freqInt = int(freq)
   if (freqInt >= 100):
#      print(lem, freq)
      if lem in refCorpusLines:
#         print(refCorpusLines[lem])
         refvalues = str(refCorpusLines[lem])
         (reflem, reffreq) = refvalues.split("\t")
         removeCalcFromRef = int(reffreq) - freqInt
#Call the R script
         a = str(freqInt)
         b = str(totLemmasCalcCorpus)
         c = str(removeCalcFromRef)
         d = str(removeTotCalcFromTotRef)
         ps = subprocess.Popen(['Rscript', scriptpath+LLtest, a, b, c, d], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         output, stderror = ps.communicate()
         outputline = str(output)
         outputline = outputline.replace('[1] ', '')
         outputline = outputline.replace("\n", '')
         valueSpruce = float(outputline)
         valueSpruce = "%.3f" % valueSpruce
         newValue = str(valueSpruce)
#         print(newValue)
         LLSorted[newValue] = values
#         outputarr = outputlines.splitlines()
#         pValue = ''
#         for line in outputarr:
#            if re.search('p-value', line):
#               pValue = line
#               pValue = re.sub(r'^(.*)p-value = ', '', pValue)
#         if re.search('e', pValue):
#            pValue = '< 0.001'
#         else:
#            pValueSpruce = float(pValue)
#            pValueSpruce = "%.3f" % pValueSpruce
#            pValue = str(pValueSpruce)


print("Tot. numb. of unique lemmas in reference corpus: ", totRefCorpus)
print("Tot. numb. of unique lemmas in single file: ", totCalcCorpus)

print("Tot. numb. of lemmas in reference corpus: ", totLemmasRefCorpus)
print("Tot. numb. of lemmas in single file: ", totLemmasCalcCorpus)

intLLSorted = {float(k) : v for k, v in LLSorted.items()}
intLLSorted = OrderedDict(sorted(intLLSorted.items(), key=lambda t: t[0], reverse = True))
for item in intLLSorted:
   print(intLLSorted[item], item)
#calcFile = open(singleFile, "r")
#referenceCorpus.close()
#singleFile.close()