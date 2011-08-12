import urllib2
import os
import pisi
import time

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from packages.models import *

#baseurl = "http://packages.pardus.org.tr/pardus/"
#version = ("2011/",)
#repos = ("devel/",)
#architecture = ("i686",)

t = time.time()
base = 'http://packages.pardus.org.tr/pardus/2011/devel/i686/pisi-index.xml'
fpath = '/home/pars/packages_pardus/xml_index'


def urlretrieve(urlfile, fpath):
    # Tum dosyayi okumak aci verici oluyor(memory)
    # 4096 byte'lik parcalar halinde okuyup yazar
    chunk = 4096
    f = open(fpath, "w")
    while 1:
        data = urlfile.read(chunk)
        if not data:
            print "done."
            break
        f.write(data)

if not os.path.exists(fpath):
    urlretrieve(urllib2.urlopen(base), fpath)

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

# Second pass for dependencies
for package in pisi_index.packages:
    p = Package.objects.get(name=package.name)
    _deps = [Package.objects.get(name=p.package) for p in package.runtimeDependencies()]
    for dep in _deps:
        p.dependencies.add(dep)

print time.time()-t
