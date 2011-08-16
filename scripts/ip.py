import urllib2
import os
import pisi
import time
import piksemel

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from packages.models import *

baseurl = "http://packages.pardus.org.tr/pardus/"
version = ("2011", "2011.1", "corporate2", "2009")
repos = ("devel", "testing", "stable")
architecture = ("i686", "x86_64")

t = time.time()

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

def createAttr(model, attrList):
    for attr in attrList:
        try:
            model.objects.get(name = attr)
        except ObjectDoesNotExist:
            model(name=attr).save()


for xml in zip(version, repos, architecture):
    base = baseurl + '/'.join(xml) + '/pisi-index.xml'
    print "base:", base
    url = baseurl + ''.join(xml)

    fpath = '/home/pars/packages_pardus/xml_index' + ''.join(xml) + '.xml'
    print "fpath:", fpath
    if not os.path.exists(fpath):
        urlretrieve(urllib2.urlopen(base), fpath)
    dist = xml[0] + '-' + xml[1]

    pisi_index = pisi.index.Index()
    pisi_index.decode(piksemel.parseString(open(fpath, 'r').read()), [])

    #max_packs = 10  # number of packages to import for testing
    for package in pisi_index.packages:
        #max_packs -= 1
        #if max_packs == 0:
            #break
        allAttr = ('isA', 'partOf', 'license', 'buildHost', 'distribution', 'architecture', 'packager')
        modelList = (isA, partOf, License, BuildHost, Distribution, Architecture, User)
        for model, attribute in zip(modelList, allAttr):
            if attribute == 'packager':
                packager = package.source.packager
                try:
                    User.objects.get(username=packager.name, password="1234")
                except ObjectDoesNotExist:
                    User(username=packager.name, password="1234", email=packager.email).save()  # TODO
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
        _arch = Architecture.objects.get(name=package.architecture)
        _installed_size = package.installedSize
        _package_size = package.packageSize
        _package_hash = package.packageHash
        _package_format = package.packageFormat
        _homepage = package.source.homepage
        _packager = User.objects.get(username=package.source.packager.name)
        _pkgbase = package.source.name
        try:
            _dist = Distribution.objects.get(name=dist)
        except Distribution.DoesNotExist:
            _dist = Distribution(name=dist)
            _dist.save()

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
                packager=_packager,
                pkgbase=_pkgbase)
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

        username = package.source.packager.name
        try:
            user = User.objects.get(username=username)
        except user.DoesNotExist:
            user = User(username=username)
            user.save()

        first = True
        for update in package.history:
            #try:
                #user = User.objects.get(username=update.name)
            #except ObjectDoesNotExist:
                #user = User(username=update.name, password="1234")
                #user.save()
            u = Update(version=update.version, release=update.release,
                    comment=update.comment,
                    packager=update.name,
                    package=p,
                    date=update.date)
            u.save()
            if first:
                p.last_update = u.date
                p.save()
                first = False

        print package.name, "added"

    # Second pass for dependencies
    for package in pisi_index.packages:
        pack = Package.objects.get(name=package.name)
        print "adding deps of", pack.name
        _deps = [Package.objects.get(name=p.package) for p in package.runtimeDependencies()]
        for dep in _deps:
            pack.dependencies.add(dep)

    print time.time()-t

