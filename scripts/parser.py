#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import piksemel
import bz2
import os
import pisi



baseurl = "http://packages.pardus.org.tr/pardus/"
version = ("2011/",)
repos = ("devel/",)
architecture = ("i686",)


pkglist = dict()
pkgdict = dict()

def loadUrlData(_url):
    
    if os.path.exists('xml-index'):
        with open('xml-index') as f: 
            return piksemel.parseString(f.read())
    
    try:
        downloaded_data = urllib2.urlopen(_url).read()
    except urllib2.URLError:
        print "trying to download uncompressed version of pisi-index.xml"
        try:
            _url.replace('.xz', '')
            downloaded_data = urllib2.urlopen(_url).read()
        except urllib2.URLError:
            print "There is no valid address named %s", _url
            
    f = open('xml-index', 'w')
    f.write(downloaded_data)
    f.close()

    print "Remote file %s has been downloaded." % _url

    if _url.endswith(".xz"):
        rawData = bz2.decompress(downloaded_data)
        return piksemel.parseString(rawData)
    else:
        return piksemel.parseString(downloaded_data)


def getXmlData(_file):
    if os.path.exists(_file):
        return piksemel.parse(_file)
    elif os.path.exists("%s.xz" % _file):
        indexdata = bz2.decompress(file("%s.xz" % _file).read())
        return piksemel.parseString(indexdata)
    else:
        print "please give the index file as a parameter or go to that folder."
        print "    Can it be a remote file?"
        sys.exit(1)

def parseXmlData(_index):
    

    for pkg in _index.tags("Package"):
      pkglist[pkg.getTagData("Name")] = pkg.getTagData("Description")
##        pkglist.append(pkg.getTagData("Name"))
##        pkglist.append(pkg.getTagData("Summary"))
    return pkglist



def parseXmlData2(_index):
  pisi_index = pisi.index.Index()
  pisi_index.decode(_index, [])
  for i in pisi_index.packages:
    print i.name
  



def main():
    xmldata = ""
    for i in version:
        for j in repos:
            for k in architecture:
                url = baseurl + i + j +k
                url= url + '/pisi-index.xml.xz'
                xmldata = loadUrlData(url)
                packagesIndex = parseXmlData(xmldata)
                for i in packagesIndex:
                    print i

xmldata = loadUrlData('http://packages.pardus.org.tr/pardus/2011/devel/i686/pisi-index.xml')
x = parseXmlData2(xmldata)
f = open('xmldeneme', 'w')
for i, v in pkglist.items():
  f.write("Package Name: " + i + "\n")
  f.write("Description: " + v + "\n\n\n")
f.close()

