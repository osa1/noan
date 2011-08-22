from urllib import urlencode, quote as urlquote
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from django import template
from django.utils.html import escape
from django.template.defaultfilters import stringfilter

register = template.Library()

class BuildQueryStringNode(template.Node):
    def __init__(self, sortfield):
        self.sortfield = sortfield

    def render(self, context):
        qs = parse_qs(context['current_query'])
        if qs.has_key('sort') and self.sortfield in qs['sort']:
            if self.sortfield.startswith('-'):
                qs['sort'] = [self.sortfield[1:]]
            else:
                qs['sort'] = ['-' + self.sortfield]
        else:
            qs['sort'] = [self.sortfield]
        return urlencode(qs, True)

@register.tag(name='buildsortqs')
def do_buildsortqs(parser, token):
    try:
        tagname, sortfield = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
                "%r tag requires a single argument" % tagname)
    if not (sortfield[0] == sortfield[-1] and sortfield[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
                "%r tag's argument should be in quotes" % tagname)
    return BuildQueryStringNode(sortfield[1:-1])

@register.simple_tag
def userpkgs(user):
    if user:
        # TODO don't hardcode
        title = escape('View packages maintained by ' + user.username)
        return '<a href="/packages/?maintainer=%s" title="%s">%s</a>' % (
                user.username,
                title,
                user.username,
        )
    return ''


def svn_link(package, svnpath):
    '''Helper function for the two real SVN link methods.'''
    parts = (package.repo.svn_root, package.pkgbase, svnpath)
    parts = ("", "", "")  # TODO
    linkbase = "http://projects.archlinux.org/svntogit/%s.git/tree/%s/%s/"
    return linkbase % tuple(urlquote(part) for part in parts)

@register.simple_tag
def svn_arch(package):
    distribution = package.repo.name.lower()
    return svn_link(package, "repos/%s-%s" % (distribution, package.architecture.name))

@register.simple_tag
def svn_trunk(package):
    return svn_link(package.name, "trunk")

@register.simple_tag
def bugs_list(package):
    data = {
        #'project': package.repo.bugs_project,
        'project': "",
        'string': package.name,
    }
    return "https://bugs.archlinux.org/?%s" % urlencode(data)

@register.simple_tag
def bug_report(package):
    data = {
        #'project': package.repo.bugs_project,
        'project': "",
        #'product_category': package.repo.bugs_category,
        'product_category': "",
        'item_summary': '[%s]' % package.name,
    }
    return "https://bugs.archlinux.org/newtask?%s" % urlencode(data)

@stringfilter
def replace(name, char):
    #print  "replace: ", name, char
    return name.replace(char, '/')

@stringfilter
def split(name, delimiter):
    #print  "split:", name, delimiter
    return name.split(delimiter)

def getVersion(value, lang='en'):
    if value[0].startswith('2'):
        return value[0] 
    else:
        value = value[0]
        if lang == 'tr':
            return "Kurumsal" + value[-1]
        else:
            return "Corporate" + value[-1]

@stringfilter
def dist_replace(value):
    parts = value.split('-')
    if parts[1] == 'stable':
        parts[1] = 'testing'
    return '/'.join(parts)


register.filter('getVersion', getVersion)
#register.filter('indexAt', indexAt)
register.filter('replace', replace)
register.filter('split', split)
register.filter('dist_replace', dist_replace)

# vim: set ts=4 sw=4 et:
