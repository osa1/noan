import os
import pisi
import time
import urllib2
import hashlib
import piksemel
import itertools

from packages.models import *
from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist


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
            print "downloading done."
            break
        f.write(data)

def createAttr(model, attrList):
    for attr in attrList:
        try:
            model.objects.get(name = attr)
        except ObjectDoesNotExist:
            model(name=attr).save()


product = itertools.product(version, repos, architecture)
try:
    while True:
        xml = product.next()
        base = baseurl + '/'.join(xml) + '/pisi-index.xml'
        print "base:", base
        url = baseurl + ''.join(xml)

        filename = "index" + ''.join(xml) + '.xml'
        fpath = os.path.join(os.getcwd(), filename)

        print "fpath:", fpath
        try:
            urlretrieve(urllib2.urlopen(base), fpath)
            sha1 = hashlib.sha1(str(os.path.getsize(fpath)) + "\0" + open(fpath, "rb").read())
            hex = sha1.hexdigest()
            try:
                filehash = XmlHash.objects.get(name=filename)
                if filehash.hash == hex:
                    print "%s hash ayni" % filename
                    continue
                else:
                    filehash.hash = hex
            except XmlHash.DoesNotExist:
                filehash = XmlHash(name=filename, hash=hex)
        except urllib2.HTTPError:
            continue
        dist = xml[0] + '-' + xml[1]

        pisi_index = pisi.index.Index()
        pisi_index.decode(piksemel.parseString(open(fpath, 'r').read()), [])
        print "piksemel parsing done."

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

            args = dict([('name', _name),
                         #('pub_date', _pub_date),
                         #('build_host', _build_host),
                         ('distribution', _dist),
                         ('architecture', _arch),
                         #('installed_size', _installed_size),
                         #('package_size', _package_size),
                         #('package_hash', _package_hash),
                         #('package_format', _package_format),
                         #('homepage', _homepage),
                         #('packager', _packager),
                         #('pkgbase', _pkgbase)])
                         ])
            try:
                p = Package.objects.get(**args)  # paket zaten var
                if (p.package_hash != package.packageHash):
                    p.pub_date = _pub_date
                    p.build_host = _build_host
                    p.installed_size =_installed_size
                    p.package_size = _package_size
                    p.package_hash = _package_hash
                    p.package_format = _package_format
                    p.homepage = _homepage
                    p.packager = _packager
                    p.pkgbase = _pkgbase
                    p.save()
                    print package.name, "updated"
            except Package.DoesNotExist:
                args.update({'pub_date': _pub_date,
                             'partOf': _partOf,
                             'build_host': _build_host,
                             'installed_size': _installed_size,
                             'package_size': _package_size,
                             'package_hash': _package_hash,
                             'package_format': _package_format,
                             'homepage': _homepage,
                             'packager': _packager,
                             'pkgbase': _pkgbase})
                p = Package(**args)
                p.save()
                print package.name, "added"

            for isa in package.isA:
                p.isA.add(isA.objects.get(name=isa))

            for license in package.license:
                p.license.add(License.objects.get(name=license))

            descriptions = Description.objects.filter(package=p)
            for desc in descriptions:
                desc.delete()

            for key, item in package.description.items():
                d = Description(lang=key, desc=item, package=p)
                d.save()

            summaries = Summary.objects.filter(package=p)
            for sum in summaries:
                sum.delete()

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

        filehash.save()

        # Second pass for dependencies
        #continue  # XXX for debug purposes
        for package in pisi_index.packages:
            pack = Package.objects.get(name=package.name, distribution=_dist, architecture=_arch)
            print "adding deps of", pack.name
            _deps = [Package.objects.get(name=p.package, distribution=_dist, architecture=_arch) for p in package.runtimeDependencies()]
            for dep in _deps:
                try:
                    pack.dependencies.get(package=dep)
                except ObjectDoesNotExist:
                    pack.dependencies.add(dep)

        print time.time()-t
except StopIteration:
    pass
