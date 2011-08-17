#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import pisi
import lzma
import time
import urllib2
import hashlib
import piksemel
import itertools

from guppy import hpy
h = hpy()


location = os.path.dirname(os.path.join(os.getcwd(), __file__)).rsplit('/', 1)[0]
os.chdir(location)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(location)

from packages.models import *
from django.contrib.auth.models import User


BASEURL = "http://packages.pardus.org.tr/pardus/"
VERSION = ("2011", "corporate2")
REPOS = ("devel", "testing", "stable")
ARCHITECTURE = ("i686", "x86_64")

t = time.time()


def createAttr(pisi_package, model, attribute):
    """attrList'deki attribute'lari, eger modelde zaten yoksa, modele ekle."""
    attrList = getattr(pisi_package, attribute)
    if not isinstance(attrList, list):
        attrList = [attrList]
    for attr in attrList:
        try:
            model.objects.get(name=attr)
        except model.DoesNotExist:
            model(name=attr).save()


def check_sha1sum(xml_url, sha1sum):
    """xml_url adresindeki sha1sum'i veritabaninda kayitli ve sha1sum ile
    ayniysa True don."""
    try:
        filehash = XmlHash.objects.get(name=xml_url)
        if filehash.hash == sha1sum:
            print "%s hash is identical." % xml_url
            return True
    except XmlHash.DoesNotExist:
        return False


def parse_index(filepath):
    pisi_index = pisi.index.Index()
    pisi_index.decode(piksemel.parseString(filepath), [])
    print "piksemel parsing done."
    return pisi_index


def create_package(pisi_package, dist):
    # keys: her bir paketin sahip olmasi gereken fieldlar
    # values: fieldlarin gosterdigi modeller
    attributes = {'isA': isA, 'partOf': partOf, 'license': License, 'buildHost': BuildHost,
            'distribution': Distribution, 'architecture': Architecture, 'packager': User}

    for attribute, model in attributes.iteritems():
        if attribute == 'packager':
            packager = pisi_package.source.packager
            try:
                User.objects.get(username=packager.name)
            except User.DoesNotExist:
                # Paket sahibi henuz olusturulmamis
                User(username=packager.name, password="1234", email=packager.email).save()
        else:
            createAttr(pisi_package, model, attribute)

    _name = pisi_package.name
    _pub_date = pisi_package.history[0].date
    #_isA = isA.objects.get(name=pisi_package.isA)
    _partOf = partOf.objects.get(name=pisi_package.partOf)
    #_license = License.objects.get(name=pisi_package.license)
    _build_host = BuildHost.objects.get(name=pisi_package.buildHost)
    _arch = Architecture.objects.get(name=pisi_package.architecture)
    _installed_size = pisi_package.installedSize
    _package_size = pisi_package.packageSize
    _package_hash = pisi_package.packageHash
    _package_format = pisi_package.packageFormat
    _homepage = pisi_package.source.homepage
    _packager = User.objects.get(username=pisi_package.source.packager.name)
    _pkgbase = pisi_package.source.name
    try:
        _dist = Distribution.objects.get(name=dist)
    except Distribution.DoesNotExist:
        _dist = Distribution(name=dist)
        _dist.save()


    # arayacagimiz paketin ozellikleri
    kwargs = {'name': _name, 'distribution': _dist, 'architecture': _arch}
    try:
        p = Package.objects.get(**kwargs)
        if (p.package_hash != pisi_package.packageHash):
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
    except Package.DoesNotExist:
        kwargs.update({'pub_date': _pub_date,
                     'partOf': _partOf,
                     'build_host': _build_host,
                     'installed_size': _installed_size,
                     'package_size': _package_size,
                     'package_hash': _package_hash,
                     'package_format': _package_format,
                     'homepage': _homepage,
                     'packager': _packager,
                     'pkgbase': _pkgbase})
        p = Package(**kwargs)
        p.save()
        print pisi_package.name, "added"

    for isa in pisi_package.isA:  # XXX
        p.isA.add(isA.objects.get(name=isa))

    for license in pisi_package.license:
        p.license.add(License.objects.get(name=license))

    descriptions = Description.objects.filter(package=p)
    for desc in descriptions:
        desc.delete()

    for key, item in pisi_package.description.items():
        d = Description(lang=key, desc=item, package=p)
        d.save()

    for key, item in pisi_package.summary.items():
        s = Summary(lang=key, sum=item, package=p)
        s.save()

    username = pisi_package.source.packager.name
    try:
        user = User.objects.get(username=username)
    except user.DoesNotExist:
        user = User(username=username, email=pisi_package.source.packager.email)
        user.save()

    first = True
    for update in package.history:
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

    p.save()


def link_dependencies(pisi_package, dist):
    _name = pisi_package.name
    _dist = Distribution.objects.get(name=dist)
    _arch = Architecture.objects.get(name=pisi_package.architecture)

    pack = Package.objects.get(name=_name, distribution=_dist, architecture=_arch)
    print "adding deps of", pack.name
    _deps = [Package.objects.get(name=p.package, distribution=_dist, architecture=_arch)
                    for p in pisi_package.runtimeDependencies()]
    for dep in _deps:
        try:
            pack.dependencies.get(package=dep)
        except ObjectDoesNotExist:
            pack.dependencies.add(dep)


if __name__ == '__main__':
    product = itertools.product(VERSION, REPOS, ARCHITECTURE)
    for xml in product:
        xml_url = BASEURL + '/'.join(xml) + '/pisi-index.xml.xz'
        sha1url = BASEURL + '/'.join(xml) + '/pisi-index.xml.xz.sha1sum'
        try:
            raw_data = urllib2.urlopen(xml_url)
            sha1sum = urllib2.urlopen(sha1url).read()
        except urllib2.HTTPError:
            continue  # bir sonraki dosyadan devam et

        pisi_index = parse_index(lzma.decompress(raw_data.read()))

        if not check_sha1sum(xml_url, sha1sum):  # sha1sum'lar farkli
            dist = xml[0] + '-' + xml[1]
            print dist
            count = 0
            for package in pisi_index.packages:
                create_package(package, dist)

            try:
                xmlhash = XmlHash.objects.get(name=xml_url)
                xmlhash.hash = sha1sum
                xmlhash.save()
            except XmlHash.DoesNotExist:
                XmlHash(name=xml_url, hash=sha1sum).save()
            for package in pisi_index.packages:
                link_dependencies(package, dist)
