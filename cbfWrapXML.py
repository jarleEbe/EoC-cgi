#!/usr/bin/python
# -*- coding: utf-8 -*-

#pylint: disable=C0103
#pylint: disable=C0111

from __future__ import print_function

# if we want to give our script parameters, we need a special library
import sys
import os
import re
import json
import xmltodict
import pprint
import datetime

#from xml.etree import ElementTree as ET

reload(sys)
sys.setdefaultencoding("utf-8")

# FUNCTIONS
def find_decade(year):

    decade = ''

    try:
        intyear = int(year)
    except ValueError:
        print(year, end="\n")
        decade = 'unknown'
        return decade

    if isinstance(intyear, int):
        if intyear >= 1900 and intyear < 1910:
            decade = '1900'
        elif intyear > 1909 and intyear < 1920:
            decade = '1910'
        elif intyear > 1919 and intyear < 1930:
            decade = '1920'
        elif intyear > 1929 and intyear < 1940:
            decade = '1930'
        elif intyear > 1939 and intyear < 1950:
            decade = '1940'
        elif intyear > 1949 and intyear < 1960:
            decade = '1950'
        elif intyear > 1959 and intyear < 1970:
            decade = '1960'
        elif intyear > 1969 and intyear < 1980:
            decade = '1970'
        elif intyear > 1979 and intyear < 1990:
            decade = '1980'
        elif intyear > 1989 and intyear < 2000:
            decade = '1990'
        elif intyear > 1999 and intyear < 2010:
            decade = '2000'
        elif intyear > 2009 and intyear < 2030:
            decade = '2010'
        elif intyear > 2019 and intyear < 2040:
            decade = '2020'
        else:
            decade = 'unknown'
    else:
        decade = 'unknown'

    return decade


def parse_bnc_header(xmltext):

#    local_file = directory + text
#    local_file = directory + '/' + text

#    local_file = local_file.replace("clean", headerDir)
#   print(local_file)

   # open the file for reading
    with open(xmltext, 'rb') as infile:
        d = xmltodict.parse(infile, xml_attribs=True)

    myJSON = json.dumps(d)
    jsonXML = json.loads(myJSON)

    idNo = ''
    title = ''
    publicationPlace = ''
    publisher = ''
    dateofPublication = ''
    sex = ''
    dateofBirth = ''
    decade = ''
    genre = ''

    if "idno" in myJSON:
        idNo = jsonXML["TEI"]["teiHeader"]["fileDesc"]["publicationStmt"]["idno"]

    if "author" in myJSON:
        author = jsonXML["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["monogr"]["author"]

    if "monogr" in myJSON:
        title = jsonXML["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["monogr"]["title"]

    if "pubPlace" in myJSON:
        publicationPlace = jsonXML["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["monogr"]["imprint"]["pubPlace"]

    if "publisher" in myJSON:
        publisher = jsonXML["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["monogr"]["imprint"]["publisher"]

    if "imprint" in myJSON:
        dateofPublication = jsonXML["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["monogr"]["imprint"]["date"]["#text"]

    if "sex" in myJSON:
        sex = jsonXML["TEI"]["teiHeader"]["profileDesc"]["particDesc"]["person"]["sex"]

    if "birth" in myJSON:
        dateofBirth = jsonXML["TEI"]["teiHeader"]["profileDesc"]["particDesc"]["person"]["birth"]["date"]["#text"]

    if "factuality" in myJSON:
        genre = jsonXML["TEI"]["teiHeader"]["profileDesc"]["textDesc"]["factuality"]["#text"]

    sex = sex.strip()
    if sex != 'male' and sex != 'female':
        print('Wrong sex:', end="")
        print(sex, end=", ")
        print(idNo, end="\n")

    myLocalDict = dict()
    myLocalDict['textId'] = idNo
    myLocalDict['author'] = author
    myLocalDict['title'] = title
    myLocalDict['pubDate'] = dateofPublication
    myLocalDict['sex'] = sex
    myLocalDict['genre'] = genre
    myLocalDict['birthDate'] = dateofBirth

    decade = find_decade(dateofPublication)
    if decade == '' or decade == 'unknown':
        print("Cannot find decade")
        print(str(myLocalDict['textId']))
    myLocalDict['decade'] = decade

    return myLocalDict


def add_xml_text(taggeddir, text, headerdir, outdir):
    local_file = taggeddir + text

    headerf = text
    headerf = headerf.replace("_clean_cwb.txt", "_header.xml")
    headerf = headerf.replace("_cwb.txt", "_header.xml")
    headerf = headerdir + headerf
    sunitDict = dict()
    sunitDict = parse_bnc_header(headerf)

    textid = sunitDict['textId']
    decade = sunitDict['decade']
    sex = sunitDict['sex']
    genre = sunitDict['genre']

    # Generate output file (new_file)
    outfile = text
    outfile = outfile.replace("_tagged.txt", "_xml.xml")
    outfile = outdir + outfile
    new_file = open(outfile, 'w')

#    new_file.write('<?xml version="1.0" encoding="UTF-8"?>')
#    new_file.write("\n")
    novel = '<text id="' + textid + '" gender="' + sex + '" genre="' + genre + '" decade="' + decade + '">'
    print(novel, end="\n")

    new_file.write(novel)
    new_file.write("\n")

#    print(local_file)
#    print(headerf)
#    print(outfile, "\n")

    # open the file for reading
    with open(local_file, 'r') as infile:
        content = infile.readlines()

    for line in content:
        new_file.write(line)

    new_file.write('</text>')
    new_file.write("\n")
    new_file.close()

    return decade, sex


# MAIN

if len(sys.argv) < 3:
    print("Need tagged, header and output directories")
    sys.exit()

mystartdir = sys.argv[1]
myheaderdir = sys.argv[2]
myoutputdir = sys.argv[3]

tagged_files = re.compile(r"\_cwb.txt$", flags=re.IGNORECASE)
#header_files = re.compile(r"_header\.xml", flags=re.IGNORECASE)
#segmented = re.compile("segmented", flags=re.IGNORECASE)
tiaar = dict()
texts = dict()
newtext = dict()
jsontextstring = ''
print ("Start creating XML headers to CWB files ...")
totwords = 0
totfiles = 0
maleorfemale = ''
totnumberofmale = 0
totnumberoffemale = 0
totnumberofunknown = 0
for dirpath, dirs, files in os.walk(mystartdir):
    for fil in files:
        if re.search(tagged_files, fil):
#            print (fil)
#            print (dirpath)
            totfiles += 1
            return_value = add_xml_text(dirpath, fil, myheaderdir, myoutputdir)

print("Total number of texts: ")
print(str(totfiles))
print("Number of unknown sex:")
print(str(totnumberofunknown))
