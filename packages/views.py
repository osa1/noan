from django import forms
from django.db.models import Q
from django.contrib.admin.widgets import AdminDateWidget
from packages.models import Package, Description, Architecture, Distribution
from django.contrib.auth.models import User

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, redirect, render_to_response

from django.views.generic import list_detail

from django.views.generic.simple import direct_to_template

make_choice = lambda l: [(str(m), str(m)) for m in l]

def details(request, name='', dist='', arch=''):
    if all([name, dist, arch]):
        try:
            pkg = Package.objects.select_related(
                    'architecture', 'distribution').get(name=name,
                            distribution__name__iexact=dist, architecture__name=arch)
            print name, dist, arch
            #pkg = Package.objects.get(name="ogmtools")
            #return direct_to_template(request, '/packages/details.html',
                    #{'pkg': pkg, })
            return render_to_response('packages/details.html', {'pkg': pkg})
        except Exception as e:
            print e
            pass
    else:
        context = {'packages': Package.objects.order_by('name')[:30],
                'name': 'test',
                'list_title': 'Package Details',
                'arch': 'arch test'}
        return direct_to_template(request, 'packages/packages_list.html', context)
        raise Http404


def coerce_limit_value(value):
    if not value:
        return None
    if value == 'all':
        # negative value indicates show all results
        return -1
    value = int(value)
    if value < 0:
        raise ValueError
    return value

class LimitTypedChoiceField(forms.TypedChoiceField):
    def valid_value(self, value):
        try:
            coerce_limit_value(value)
            return True
        except (ValueError, TypeError):
            return False

class PackageSearchForm(forms.Form):
    repo = forms.MultipleChoiceField(required=False)
    arch = forms.MultipleChoiceField(required=False)
    q = forms.CharField(required=False)
    maintainer = forms.ChoiceField(required=False)
    packager = forms.ChoiceField(required=False)
    last_update = forms.DateField(required=False, widget=AdminDateWidget(),
            label='Last Updated After')
    flagged = forms.ChoiceField(
            choices=[('', 'All')] + make_choice(['Flagged', 'Not Flagged']),
            required=False)
    limit = LimitTypedChoiceField(choices=make_choice([50, 100, 250]) + [('all', 'All')], coerce=coerce_limit_value,
            required=False,
            initial=50)

    def __init__(self, *args, **kwargs):
        super(PackageSearchForm, self).__init__(*args, **kwargs)
        self.fields['repo'].choices = make_choice(
                        [repo.name for repo in Distribution.objects.all()])
        self.fields['arch'].choices = make_choice(
                        [arch.name for arch in Architecture.objects.all()])
        self.fields['q'].widget.attrs.update({"size": "30"})
        maints = User.objects.filter(is_active=True).order_by('username')
        self.fields['maintainer'].choices = \
                [('', 'All'), ('orphan', 'Orphan')] + \
                [(m.username, m.username) for m in maints]
        self.fields['packager'].choices = \
                [('', 'All'), ('unknown', 'Unknown')] + \
                [(m.username, m.username) for m in maints]


def search(request, page=None):
    limit = 50
    packages = Package.objects.normal()

    if request.GET:
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            if form.cleaned_data['repo']:
                packages = packages.filter(distribution__name__in=form.cleaned_data['repo'])

            if form.cleaned_data['arch']:
                packages = packages.filter(architecture__name__in=form.cleaned_data['arch'])

            if form.cleaned_data['maintainer']:
                packages = packages.filter(packager__name__in=form.cleaned_data['maintainer'])

            if form.cleaned_data['q']:
                query = form.cleaned_data['q']
                desc = Description.objects.filter(desc__icontains=query)  # TODO
                packages = packages.filter(name__icontains=query)

            asked_limit = form.cleaned_data['limit']
            if asked_limit and asked_limit < 0:
                limit = None
            elif asked_limit:
                limit = asked_limit
        else:
            packages = Package.objects.none()
    else:
        form = PackageSearchForm()

    current_query = request.GET.urlencode()
    page_dict = {
            'search_form': form,
            'current_query': current_query
    }
    #allowed_sort = ["arch", "repo", "pkgname", "pkgbase",
            #"compressed_size", "installed_size",
            #"build_date", "last_update", "flag_date"]
    allowed_sort = []
    allowed_sort += ["-" + s for s in allowed_sort]
    sort = request.GET.get('sort', None)
    # TODO: sorting by multiple fields makes using a DB index much harder
    if sort in allowed_sort:
        packages = packages.order_by(
                request.GET['sort'], 'repo', 'arch', 'pkgname')
        page_dict['sort'] = sort
    else:
        packages = packages.order_by('name')

    return list_detail.object_list(request, packages,
            template_name="packages/search.html",
            page=page,
            paginate_by=limit,
            template_object_name="package",
            extra_context=page_dict)



