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

def calcLLratio(singleFile, spath, refCorpusLines, totLemmasRefCorpus, rpath):
    
   antOutput = 100

   calcCorpusLines = dict()
   totLemmasCalcCorpus = 0
   singleFile = spath + singleFile
   with open(singleFile) as file:
      for line in file: 
         line = line.strip()
         (lem, freq) = line.split("\t")
         totLemmasCalcCorpus = totLemmasCalcCorpus + int(freq)
         calcCorpusLines[lem] = line

   totCalcCorpus = len(calcCorpusLines)
   #Unsure whether this makes sense
   #removeTotCalcFromTotRef = totLemmasRefCorpus - totLemmasCalcCorpus

   LLSorted = dict()
   numbOutputLines = 0
   for line in calcCorpusLines:
   #   print(line, calcCorpusLines[line])
      values = str(calcCorpusLines[line])
      (lem, freq) = values.split("\t")
      freqInt = int(freq)
      currenttotLemmasCalcCorpus = totLemmasCalcCorpus - freqInt # = corpus size minus what's been just counted
      if (freqInt >= 5): #Change according to gram size 1 - n
   #      print(lem, freq)
         if lem in refCorpusLines:
   #         print(refCorpusLines[lem])
            refvalues = str(refCorpusLines[lem])
            (reflem, reffreq) = refvalues.split("\t")
#            removeCalcFromRef = int(reffreq) - freqInt
            removeLemmaFreqFromRef = totLemmasRefCorpus - int(reffreq)
   #Call the R script
            a = str(freqInt) #Frequency of X in current file/corpus
            b = str(currenttotLemmasCalcCorpus) #Frequency of everything else in file/corpus minus frequency of X
            c = str(reffreq) #Frequency of X in reference corpus
            d = str(removeLemmaFreqFromRef) #Frequency of everything else in reference corpus minus frequency of X in ref. corpus
            ps = subprocess.Popen(['Rscript', scriptpath+LLtest, a, b, c, d], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, stderror = ps.communicate()
            outputline = str(output)
#           print(lem, a,b,c,d,outputline)
            outputline = outputline.replace('[1] ', '')
            outputline = outputline.replace("\n", '')
            valueSpruce = float(outputline)
            valueSpruce = "%.2f" % valueSpruce
            newValue = str(valueSpruce)
            while newValue in LLSorted:
                  tempValue = float(newValue)
                  tempValue = tempValue + 0.01
                  newValue = str(tempValue)
            LLSorted[newValue] = values
            numbOutputLines += 1
         else:
            reffreq = 1
            removeLemmaFreqFromRef = totLemmasRefCorpus - int(reffreq)
   #Call the R script
            a = str(freqInt)
            b = str(totLemmasCalcCorpus)
            c = str(reffreq)
            d = str(removeLemmaFreqFromRef )
            ps = subprocess.Popen(['Rscript', scriptpath+LLtest, a, b, c, d], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, stderror = ps.communicate()
            outputline = str(output)
            outputline = outputline.replace('[1] ', '')
            outputline = outputline.replace("\n", '')
            valueSpruce = float(outputline)
            valueSpruce = "%.2f" % valueSpruce
            newValue = str(valueSpruce)
            while newValue in LLSorted:
                  tempValue = float(newValue)
                  tempValue = tempValue + 0.01
                  newValue = str(tempValue)
            LLSorted[newValue] = values
            numbOutputLines += 1

   intLLSorted = {float(k) : v for k, v in LLSorted.items()}
   intLLSorted = OrderedDict(sorted(intLLSorted.items(), key=lambda t: t[0], reverse = True))

   negativeKey = numbOutputLines - (antOutput + 1)
   print(numbOutputLines)
   print(negativeKey)
   print(len(intLLSorted))
   singleFile = singleFile.replace(spath, "")
   htmlFile = singleFile.replace('.txt', '.html')
   sourceFile = htmlFile.replace('-WLL.html', '_header.xml')
   linkFile = sourceFile
   linkFile = linkFile.replace('_header.xml', '')
   sourceFile = 'https://nabu.usit.uio.no/hf/ilos/cbf/source/' + sourceFile
   outFile = open(rpath + htmlFile, "w")

   outFile.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>')
   outFile.write(htmlFile)
   outFile.write('</title></head><body><table style="width:600px">')
   caption = '<caption style="font-size:125%"><span style="font-weight:bold">Log-likelihood keyword statistic, <a href="' + sourceFile + '">' + linkFile + '</a></span><br/>(see Levshina, N. 2015. <i>How to do linguistics with R</i>, p. 223<i>ff</i>)</caption>'
   outFile.write(caption)
   outFile.write('<tr style="text-align:center"><th>Lemma_POS</th><th>Raw freq.</th><th>Log-likelihood ratio<br/>(positive and negative keywords)</th></tr>')
   index = 0
   for item in intLLSorted:
      index += 1
      if (index <= antOutput):
         cols1_2 = intLLSorted[item]
         cols1_2 = cols1_2.replace("\t", "</td><td style='text-align:right'>")
         theOutput = "<tr><td>" + cols1_2 + "</td><td style='text-align:right'>" + str(item) + "</td></tr>"
         outFile.write(theOutput)
      if (index >= negativeKey):
         cols1_2 = intLLSorted[item]
         cols1_2 = cols1_2.replace("\t", "</td><td style='text-align:right'>")
#         theOutput = intLLSorted[item] + "\t" + str(item) + "\n"
         theOutput = "<tr><td>" + cols1_2 + "</td><td style='text-align:right'>" + str(item) + "</td></tr>"
         outFile.write(theOutput)

   outFile.write('</table></body></html>')
   outFile.close()
   return totCalcCorpus

#MAIN
fileExtention = re.compile("\.txt", flags=re.IGNORECASE)

referenceCorpus = 'WLL-refCorpus.txt'
scriptpath = '/home/jarlee/prog/R/script/'
LLtest = 'scriptLog-likelihood.R'
Rscript = 'Rscript '

if (len(sys.argv) <= 1):
   print('Need path to the individual files.')
   exit()

startPath = sys.argv[1]
resultPath = 'results/'

#Read references corpus
refCorpusLines = dict()
totLemmasRefCorpus = 0;
with open(referenceCorpus) as file:
   for line in file: 
      line = line.strip()
      (lem, freq) = line.split("\t")
      totLemmasRefCorpus = totLemmasRefCorpus + int(freq)
      refCorpusLines[lem] = line

totRefCorpus = len(refCorpusLines)

print("Tot. numb. of unique lemmas in reference corpus: ", totRefCorpus)
print("Tot. numb. of lemmas in reference corpus: ", totLemmasRefCorpus)
totfiles = 0
for dirpath, dirs, files in os.walk(startPath):
   for fil in files:
      if re.search(fileExtention, fil):
         print(fil)
         totfiles += 1
         return_value = calcLLratio(fil, startPath, refCorpusLines, totLemmasRefCorpus, resultPath)
