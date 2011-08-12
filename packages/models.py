# TODO CharField max_length ara degerleri
# TODO source.packager.name gibi bir kisayol ara.

from django.db import models
from django.contrib.auth.models import User

class Package(models.Model):
    name = models.CharField(max_length=200)
    pub_date = models.DateField('date published')
    isA = models.ManyToManyField('isA')
    partOf = models.ForeignKey('partOf', related_name='packages')
    license = models.ManyToManyField('License', related_name='packages')
    build_host = models.ForeignKey('BuildHost', related_name='packages')
    distribution = models.ForeignKey('Distribution', related_name='packages')
    architecture = models.ForeignKey('Architecture', related_name='packages')
    installed_size = models.IntegerField()
    package_size = models.IntegerField()
    package_hash = models.CharField(max_length=256)  # FIXME
    package_format = models.CharField(max_length=100)
    # source_name = models.CharField(max_length=255)
    homepage = models.URLField()
    packager = models.ForeignKey(User)
    dependencies = models.ManyToManyField('self', symmetrical=False)

    @property
    def last_packager(self):
        packager = Update.objects.filter(package=self)[0].packager.username
        return packager if packager else self.packager.username

    def last_update(self):
        return Update.objects.filter(package=self)[0].date

    @property
    def pkgdesc(self):
        return Description.objects.filter(package=self).get(lang="en")

    @property
    def pkgname(self):
        return self.name

    @property
    def groups(self):
        return self.partOf

    @property
    def maintainer(self):
        return self.packager

    @property
    def pkgbase(self):
        return self.name

    @property
    def licenses(self):
        return [license.name for license in self.license.all()]

    @property
    def url(self):
        return self.homepage

    @property
    def full_version(self):
        return ""

    @property
    def repo(self):
        return "%s_%s" % (self.distribution, self.architecture)

    @property
    def arch(self):
        return self.architecture

    @property
    def flag_date(self):
        return ""



    def __unicode__(self):
        return self.name

class Dependency(models.Model):
    pass

class Update(models.Model):
    release = models.IntegerField()
    version = models.CharField(max_length=256)
    comment = models.TextField()
    packager = models.ForeignKey(User)
    package = models.ForeignKey(Package)
    date = models.DateField()

    def __unicode__(self):
        return "%s_%s" % (self.release, self.version)

class Description(models.Model):
    package = models.ForeignKey(Package)
    lang = models.CharField(max_length=2)
    desc = models.CharField(max_length=1000)

    def __unicode__(self):
        return self.desc[:255] + '...'

class Summary(models.Model):
    package = models.ForeignKey(Package)
    lang = models.CharField(max_length=2)
    sum = models.CharField(max_length=255)

    def __unicode__(self):
        return self.sum

class OneToMany(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        abstract = True

class partOf(OneToMany):
    pass

class isA(OneToMany):
    pass

class License(OneToMany):
    pass

class BuildHost(OneToMany):
    pass

class Distribution(OneToMany):
    pass

class Architecture(OneToMany):
    pass
