import urllib2
import piksemel
import os
import pisi
import bz2

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from packages.models import *

#baseurl = "http://packages.pardus.org.tr/pardus/"
#version = ("2011/",)
#repos = ("devel/",)
#architecture = ("i686",)

base = 'http://packages.pardus.org.tr/pardus/2011/devel/i686/pisi-index.xml'

def loadUrlData(_url):

    if os.path.exists('/home/pars/packages_pardus/xml-index'):
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

xmldata = loadUrlData(base)
pisi_index = pisi.index.Index()
pisi_index.decode(xmldata, [])

def createAttr(model, attrList):
    for attr in attrList:
        try: 
            model.objects.get(name = attr)
        except ObjectDoesNotExist:
            model(name=attr).save()
            print attr

for package in pisi_index.packages:
    allAttr = ('isA', 'partOf', 'license', 'buildHost', 'distribution', 'architecture', 'packager')
    modelList = (isA, partOf, License, BuildHost, Distribution, Architecture, User)
    for model, attribute in zip(modelList, allAttr):
        if attribute == 'packager':
            packager = package.source.packager
            try:
                User.objects.get(username=packager.name, password="1234")
            except ObjectDoesNotExist:
                User(username=packager.name, password="1234").save()
        else:
            attrList = getattr(package, attribute)
            if isinstance(attrList, list):
                createAttr(model, attrList)
            else:
                createAttr(model, [attrList])

    _name = package.name
    _pub_date = package.history[0].date
    #_isA = isA.objects.get(name=package.isA)
    _partOf = partOf.objects.get(name=package.partOf)
    #_license = License.objects.get(name=package.license)
    _build_host = BuildHost.objects.get(name=package.buildHost)
    _dist = Distribution.objects.get(name=package.distribution)
    _arch = Architecture.objects.get(name=package.architecture)
    _installed_size = package.installedSize
    _package_size = package.packageSize
    _package_hash = package.packageHash
    _package_format = package.packageFormat
    _homepage = package.source.homepage
    _packager = User.objects.get(username=package.source.packager.name)

    p = Package(name=_name,
            pub_date=_pub_date,
            partOf=_partOf,
            build_host=_build_host,
            distribution=_dist,
            architecture=_arch,
            installed_size=_installed_size,
            package_size=_package_size,
            package_hash=_package_hash,
            package_format=_package_format,
            homepage=_homepage,
            packager=_packager)
    p.save()

    for isa in package.isA:
        p.isA.add(isA.objects.get(name=isa))

    for license in package.license:
        p.license.add(License.objects.get(name=license))

    for key, item in package.description.items():
        d = Description(lang=key, desc=item, package=p)
        d.save()

    for key, item in package.summary.items():
        s = Summary(lang=key, sum=item, package=p)
        s.save()

    for update in package.history:
        try:
            user = User.objects.get(username=update.name)
        except ObjectDoesNotExist:
            user = User(username=update.name, password="1234")
            user.save()
        u = Update(version=update.version, release=update.release,
                comment=update.comment,
                packager=user,
                package=p)
        u.save()
