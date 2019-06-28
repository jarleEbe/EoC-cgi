#!/usr/bin/python
#pylint: disable=C0103
#pylint: disable=C0111

# -*- coding: utf-8 -*-

from __future__ import print_function
import sys, os, re
from pprint import pprint

def isDialogueInlineType1(sequence):
      
#   print(sequence)

#TYPE: "_Started_having_children_"_?
   type0DS = re.compile(r"^\"_([\w',; -]+)_(\.|\!|\?)_#_([^\"]+)\"$", flags=re.IGNORECASE)
   if re.search(type0DS, sequence):
      return True
   
   return False

def isDialogueInlineType2(sequence):

   return False

#TYPE: "_Do_you_know_?_"
   type0DS = re.compile(r"^\"_([\w' -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type0DS, sequence):
      return True

   type0DSa = re.compile(r"^\"_([^\"]+?)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type0DSa, sequence):
      return True

#TYPE: "_Actually_,_"_said_Angie_,_"_it_will_be_Manjusha_who_'s_looking_after_him_._"
   type5DS = re.compile(r"^(.*)_:_\"_([^\"]+?)\"_VV._NP1(_,|_;|_.*)_\"_([\w', -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type5DS, sequence): 
      return True

#TYPE: "_Mr_Pollitt_,_"_she_said_,_"_did_you_ever_see_anyone_visiting_Krystian_Zalewski_?_"
   type6DS = re.compile(r"^\"_([^\"]+?)\"_(PPHS\d|PPIS\d)_VV.(_,|_;|_.*)_\"_([\w', -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type6DS, sequence): 
      return True
   #else:
   
   return False


def isDialogueInlineType3(sequence):

#Similar to type 1/2 but with a sentence start and a colon

   return False

   type0DS = re.compile(r"^(.*)_:_\"_([\w' -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type0DS, sequence):
      return True

   type0DSa = re.compile(r"^(.*)_:_\"_([^\"]+?)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type0DSa, sequence):
      return True

   type5DS = re.compile(r"^(.*)_:_\"_([^\"]+?)\"_VV._NP1(_,|_;|_.*)_\"_([\w', -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type5DS, sequence): 
      return True

   type6DS = re.compile(r"^(.*)_:_\"_([^\"]+?)\"_(PPHS\d|PPIS\d)_VV.(_,|_;|_.*)_\"_([\w', -]+)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type6DS, sequence): 
      return True

#TYPE: ... from_London_,_Tash_said_,_"_So_you_do_n't_know_people_in_this_part_of_the_world_?_"
   type7DS = re.compile(r"^([\w',; -]+)_VV._,_\"_([^\"]+?)_(\.|\!|\?)_\"$", flags=re.IGNORECASE)
   if re.search(type7DS, sequence): 
      return True
   #else:
   
   return False


def findDirectSpeech(singleFile, spath, rpath):
    
   dialogueSequences = dict()

   singleFile = spath + singleFile
   countS = 0
   localCounter = 0
   currentItem = ''
   sentence = ''
   with open(singleFile) as file:
      for line in file: 
         line = line.strip()
         if (re.search('<text ', line) or re.search('</text>', line)):
#            print(line)
            temp = 'n'
         elif re.search('<s>', line):
            countS += 1
            localCounter += 1
            currentItem = 'S' + str(countS)
         elif re.search('</s>', line) and localCounter == 2:
#            print(currentItem)
            sentence = sentence.strip()
#            print(sentence, "\n")
            dialogueSequences[currentItem] = sentence
            sentence = ''
            localCounter = 0
         elif re.search('</s>', line):
            temp = 2
            sentence = sentence + "#\t#\t#" + "\n"
         else:
            sentence = sentence + line + "\n"

   countS = 1000000
   localCounter = 1
   currentItem = ''
   sentence = 'NILL'
   with open(singleFile) as file:
      for line in file: 
         line = line.strip()
         if (re.search('<text ', line) or re.search('</text>', line)):
#            print(line)
            temp = 'n'
         elif re.search('<s>', line):
            countS += 1
            localCounter += 1
            currentItem = 'S' + str(countS)
         elif re.search('</s>', line) and localCounter == 2:
#            print(currentItem)
            sentence = sentence.strip()
#            print(sentence, "\n")
            dialogueSequences[currentItem] = sentence
            sentence = ''
            localCounter = 0
         elif re.search('</s>', line):
            temp = 2
            sentence = sentence + "#\t#\t#" + "\n"
         else:
            sentence = sentence + line + "\n"

   singleFile = singleFile.replace(spath, "")
   singleFile = singleFile.replace("_cwb", "")
   outFile = open(rpath + singleFile, "w")

   numbDS = 0;
   for item in sorted(dialogueSequences):
#      outFile.write(item)
#      outFile.write("\n")
#      outFile.write(dialogueSequences[item])
#      print(item)
      sTriplet = dialogueSequences[item]
      aTriplet = sTriplet.split("\n")
      wSeq = ''
      lSeq = ''
      pSeq = ''
      print(sTriplet)
      for unit in aTriplet:
         word, pos, lemma = unit.split("\t")
         word = word.strip()
         pos = pos.strip()
         lemma = lemma.strip()
#         outFile.write(lemma)
         wSeq = wSeq + ' ' + word
         pSeq = pSeq + ' ' + pos
         lSeq = lSeq + ' ' + lemma
      pSeq = pSeq.strip()
      pSeq = pSeq.replace(" ", "_")
      lSeq = lSeq.strip()
      lSeq = lSeq.replace(" ", "_")
      wSeq = wSeq.strip()
      wSeq = wSeq.replace(" ", "_")
      print(wSeq)
      print(pSeq)
      if isDialogueInlineType1(pSeq):
#         print(wSeq, end="\n")
         numbDS += 1
         outFile.write(wSeq)
         outFile.write("\t")
         outFile.write(pSeq)
         outFile.write("\t")
         outFile.write(singleFile)
         outFile.write("\n")
      elif isDialogueInlineType2(pSeq):
#         print(wSeq, end="\n")
         numbDS += 1
         outFile.write(wSeq)
         outFile.write("\t")
         outFile.write(pSeq)
         outFile.write("\t")
         outFile.write(singleFile)
         outFile.write("\n")
      elif isDialogueInlineType3(pSeq):
#         print(wSeq, end="\n")
         numbDS += 1
         outFile.write(wSeq)
         outFile.write("\t")
         outFile.write("\t")
         outFile.write(pSeq)
         outFile.write(singleFile)
         outFile.write("\n")
 
   outFile.close()
   return numbDS, countS

#MAIN
fileExtention = re.compile(r"\.txt", flags=re.IGNORECASE)
if (len(sys.argv) <= 1):
   print('Need path to the individual files.')
   exit()

startPath = sys.argv[1]
resultPath = 'result/'

totfiles = 0
for dirpath, dirs, files in os.walk(startPath):
   for fil in files:
      if re.search(fileExtention, fil):
         print(fil, end=": ")
         totfiles += 1
         (return_value, tot) = findDirectSpeech(fil, startPath, resultPath)
         percent = float(return_value)
         temptot = float(tot)
         percent = (percent / temptot) * 100
         percent = "%.2f" % percent
         print(return_value, tot, percent)
print("Number of files processed: ", totfiles)