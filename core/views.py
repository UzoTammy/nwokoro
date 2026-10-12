from collections.abc import Sequence
import inspect
import json
import datetime
import re
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.http.response import HttpResponse as HttpResponse
from django.views.generic.base import View, TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .forms import NumberInputForm, ProfileForm, ActivateRegistrationForm, UpdateProfileForm, MyFormSet, PreferenceForm
from .tinyproject import numtoword, rota as rota_engine
from .tinyproject.numtoword import convert, normalise
from .tinyproject.taxes import CanadaIncomeTaxCalculator as TaxCalc
from .tinyproject.registry import get_projects
from .models import StudentProfile
from account.models import User, Preference



def read_profile():
    with open('./profile.json', 'r') as rf:
        content = json.load(rf)
    return content

def prosecute(preferences, action, subject, value=None, new_value=None):
    preference = preferences.get()

    if subject in preference.networth:
        subjects = preference.networth[subject]

    if action == 'remove':
        subjects.remove(value)
        preference.networth[subject] = subjects
    if action == 'update':
        indx = subjects.index(value)
        subjects[indx] = new_value
        preference.networth[subject] = subjects
    if action == 'add':
        if subject in preference.networth:
            subjects.append(new_value)
            preference.networth[subject] = subjects
        else:
            preference.networth[subject] = [new_value]

    preference.save() 

class MeHome(LoginRequiredMixin, TemplateView):
    template_name = 'core/me_home.html'

class PracticeView(View):
    
    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        formset = MyFormSet()
        return render(request, 'core/tutorial.html', {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = MyFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                print(f"Name: {form.cleaned_data['name']} & Email: {form.cleaned_data['email']}")
            return redirect('index')
        
        return render(request, 'core/tutorial.html', {'formset': formset})
        
# Create your views here.
class MainView(TemplateView):
    template_name = 'core/home_v2.html'
    extra_context = {'is_home': True}


class PreferenceView(LoginRequiredMixin, FormView):
    template_name = 'core/preference.html'
    form_class = PreferenceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preferences = Preference.objects.filter(user=self.request.user)
        if not preferences.exists(): 
            Preference.objects.create(user=self.request.user)
        
        if self.request.GET:
            get_key = list(self.request.GET.keys())[0]
            
            action, subject = get_key.split('-')[0], get_key.split('-')[1]
            value = self.request.GET[get_key]
            
            new_value = self.request.session.get('new_value', None)
            if subject == 'countries':
                if len(new_value) == 2:
                    prosecute(preferences, action, subject, value, new_value)
                else:   
                    messages.info(self.request, "Use country's 2-letter code")
        
            elif subject == 'currencies':
                if len(new_value) == 3:
                    prosecute(preferences, action, subject, value, new_value)
                else:
                    messages.info(self.request, "Use currency's 3-letter code")
            else:
                prosecute(preferences, action, subject, value, new_value)

        context['preferences'] = preferences.get()
        data = self.request.session.get('networth', None)
        
        if data:
            context['message'] = (data['networth'], data['new_value'])
            del self.request.session['networth']
        return context
    

    def post(self, request, *args, **kwargs):

        key, action, value = request.POST['networth'], request.POST['action'], request.POST['new_value']

        preference = Preference.objects.get(user=self.request.user)
        if key == 'holders':
            if action == 'Add':
                preference.networth['holders'].append(value)
                preference.save()
            if action == 'Update':
                request.session['networth'] = request.POST
            
        return redirect('preference')

class ActivateRegistrationView(FormView):
    template_name = 'core/activate_registration.html'
    form_class = ActivateRegistrationForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        
        # config = Config.objects.first()
        # config.activate_registration=form.cleaned_data['activate_registration']
        # config.save()

        return super().form_valid(form)

class ErrorView(TemplateView):
    template_name = 'core/error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = ''
        return context

class AboutMe(TemplateView):
    template_engine = 'django'

    def get_template_names(self) -> list[str]:

        return ['core/about_v2.html']

class ResumeView(TemplateView):
    template_name = 'core/resume_v2.html'

class TinyProjectView(TemplateView):
    template_name = 'core/portfolio/tinyprojects_v2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = get_projects()
        context['projects'] = projects
        categories = sorted({p['category'] for p in projects})
        for p in projects:
            p['tone'] = categories.index(p['category']) % 6  # colour per category
        context['categories'] = [
            {'name': c, 'count': sum(p['category'] == c for p in projects)} for c in categories
        ]
        context['live_count'] = sum(p['status'] == 'live' for p in projects)
        return context

class PortfolioScushView(TemplateView):
    template_name = 'core/portfolio/scush_v2.html'

class CPDevotionalCaseStudyView(TemplateView):
    template_name = 'core/portfolio/cp_devotional.html'

class AdvisorCaseStudyView(TemplateView):
    template_name = 'core/portfolio/ai_advisor.html'

class PortfolioFinuelView(TemplateView):
    template_name = 'core/portfolio/finuel.html'
    
class TextingView(TemplateView):
    template_name = 'core/texting.html'

class NumberToWordView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/numtoword_v2.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        raw = self.request.GET.get('enter_number', '').strip()
        context['raw'] = raw
        context['source'] = inspect.getsource(numtoword)  # docs always show the real code

        if raw:
            try:
                context['figure'] = normalise(raw)
                context['word'] = convert(raw)
            except (ValueError, OverflowError) as err:
                context['error'] = str(err)
        return context
    
SAMPLE_WRITERS = [
    {'id': 'ada', 'name': 'Ada', 'capacity': 12, 'unavailable': []},
    {'id': 'ben', 'name': 'Ben', 'capacity': 6, 'unavailable': []},
    {'id': 'chi', 'name': 'Chi', 'capacity': 10, 'unavailable': []},
    {'id': 'dayo', 'name': 'Dayo', 'capacity': 10, 'unavailable': []},
]
SAMPLE_REVIEWERS = [{'id': 'grace', 'name': 'Grace'}, {'id': 'femi', 'name': 'Femi'}]


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RotaView(TemplateView):
    """Fair Rota Scheduler tiny project: the page; the rota itself comes from rota_api."""
    template_name = 'core/portfolio/tinyprojects/rota.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['setup'] = {'start': datetime.date.today().isoformat(), 'reserve': 5,
                            'writers': SAMPLE_WRITERS, 'reviewers': SAMPLE_REVIEWERS}
        context['source'] = inspect.getsource(rota_engine)
        return context


class RotaInputError(ValueError):
    pass


def _rota_people(items, kind, limit, with_capacity):
    if not isinstance(items, list) or not 1 <= len(items) <= limit:
        raise RotaInputError(f'Between 1 and {limit} {kind} are needed.')
    people, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            raise RotaInputError(f'Each of the {kind} must be an object.')
        pid = str(item.get('id', ''))[:20]
        name = str(item.get('name', '')).strip()[:30]
        if not re.fullmatch(r'[a-z0-9-]{1,20}', pid) or pid in seen or not name:
            raise RotaInputError(f'Every one of the {kind} needs a unique id and a name.')
        seen.add(pid)
        person = rota_engine.Person(pid, name)
        if with_capacity:
            try:
                person.capacity = int(item.get('capacity', 8))
            except (TypeError, ValueError):
                raise RotaInputError('Capacity must be a whole number.')
            if not 1 <= person.capacity <= 28:
                raise RotaInputError('Capacity must be between 1 and 28 slots per 28 days.')
            days = item.get('unavailable') or []
            if not isinstance(days, list) or len(days) > 28:
                raise RotaInputError('Up to 28 unavailable days per person.')
            try:
                person.unavailable = {datetime.date.fromisoformat(str(d)) for d in days}
            except ValueError:
                raise RotaInputError('Unavailable days must be dates (YYYY-MM-DD).')
        people.append(person)
    return people


@require_POST
def rota_api(request):
    """Rebuild the rota from the posted setup and actions (stateless, deterministic)."""
    try:
        body = json.loads(request.body or b'{}')
        if not isinstance(body, dict):
            raise RotaInputError('Expected a JSON object.')
        try:
            start = datetime.date.fromisoformat(str(body.get('start', '')))
        except ValueError:
            raise RotaInputError('start must be a date (YYYY-MM-DD).')
        if abs((start - datetime.date.today()).days) > 366:
            raise RotaInputError('start must be within a year of today.')
        writers = _rota_people(body.get('writers'), 'writers', 8, True)
        reviewers = _rota_people(body.get('reviewers'), 'reviewers', 4, False)
        if {w.id for w in writers} & {r.id for r in reviewers}:
            raise RotaInputError('Writers and reviewers need different ids.')
        try:
            reserve = int(body.get('reserve', 5))
        except (TypeError, ValueError):
            raise RotaInputError('reserve must be a whole number.')
        if not 0 <= reserve <= 20:
            raise RotaInputError('reserve must be between 0 and 20.')
        actions = body.get('actions') or []
        if not isinstance(actions, list) or len(actions) > 150                 or sum(1 for a in actions if isinstance(a, dict) and a.get('type') == 'advance') > 60:
            raise RotaInputError('Too many actions: up to 60 days of simulation.')
        actions = [a for a in actions if isinstance(a, dict)]
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
    except RotaInputError as err:
        return JsonResponse({'detail': str(err)}, status=400)

    result = rota_engine.replay(writers, reviewers, start, actions, reserve=reserve)
    return JsonResponse(result.to_dict())


class DatabaseLearningView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/databaselearning.html'

class AutomaticEmailView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/auto_email.html'
    
class NewHomeView(RedirectView):
    # the redesign now lives at '/'; keep the old staging URL working
    pattern_name = 'index'

class NewAboutMeView(TemplateView):
    template_name = 'core/new_about_me.html'

class ProfileView(View):
    
    def get(self, request, **kwargs):
        form = ProfileForm()
        
        if request.GET.get('action') == 'clear':
            # this is to clear content of json file
            with open('./profile.json', 'r+') as wf:
                wf.truncate(0)
                json.dump({}, wf)
                profile = {}
        elif request.GET.get('action') == 'new':
            # this is to save to database
            data = read_profile()
            
            student = StudentProfile(
                first_name = data['first_name'],
                last_name = data['last_name'],
                middle_name = data['middle_name'],
                gender = data['gender'],
                date_of_birth = datetime.datetime.strptime(data['date_of_birth'], '%d-%b-%Y'),
                email = data['email'],
                age = data['age'],
                age_status = data['age_status']
            )
            student.save()
            profile = {}
            return redirect(reverse('profile-list', kwargs={'filter_by': 'All'}))
        else:
            profile = read_profile()
        context = {
            'form': form,
            'profile': profile
        }

        return render(request, 'core/portfolio/tinyprojects/profile.html', context)
    
    def post(self, request, **kwargs):
        form = ProfileForm(request.POST)
        
        if form.is_valid():
            with open('./profile.json', 'w') as wf:
                json.dump(form.cleaned_data, wf, indent=2)
            return redirect('tinyproject-profile')
        context = {
            'form': form,
        }
        return render(request, 'core/portfolio/tinyprojects/profile.html', context)

class TinyProjectTaxCanadaView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/tax_canada_home.html'  

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.GET:
            income = float(self.request.GET.get('income'))
            stack = list()
            income_tax = TaxCalc()
            for i in range(1, 10):
                federal_tax = income_tax.federal_tax_calculator(income * i)
                prov_tax = income_tax.ns_tax_calculator(income * i)
                stack.append({"I": f'x{i}', 
                            'income': income * i, 
                            'fed_tax': federal_tax, 'fed_rate': federal_tax/(income * i),
                            'prov_tax': prov_tax, 'prov_rate': prov_tax/(income*i),
                            'tax': federal_tax + prov_tax,
                            'rate': 100*(federal_tax + prov_tax)/(income * i),
                            'net_income': income * i - federal_tax - prov_tax
                            })
            context['stack'] = stack
        return context
    
class StudentProfileView(ListView):
    model = StudentProfile
    # paginate_orphans = 1

    def get_queryset(self) -> QuerySet[Any]:
        if self.kwargs.get('filter_by') == 'Male':
            qs = StudentProfile.objects.filter(gender='Male')
        elif self.kwargs.get('filter_by') == 'Female':   
            qs = StudentProfile.objects.filter(gender='Female')
        else:
            qs = StudentProfile.objects.all()
        return qs.order_by(self.get_ordering())
    
    
    def get_ordering(self) -> Sequence[str]:
        ordering = self.request.GET.get('ordering', '-pk')
        if ordering == 'name':
            ordering = 'last_name'
        return ordering
    
    def get_paginate_by(self, queryset):
        # Custom logic to determine paginate_by based on the size of the queryset
        queryset_size = queryset.count()
        if queryset_size < 50:
            paginate_by = 2  # If less than 50 items, show 5 per page
        elif queryset_size < 200:
            paginate_by = 20  # If less than 200 items, show 10 per page
        else:
            paginate_by = 30  # If 200 or more items, show 20 per page
        return paginate_by
    
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['ordering'] = self.get_ordering()
        return context
    
class StudentProfileUpdateView(UpdateView):
    model = StudentProfile
    form_class = UpdateProfileForm
    success_url = '/portfolio/miniproject/All/?page=1'
    template_name = 'core/portfolio/tinyprojects/profile.html'

    def form_valid(self, form) -> HttpResponse:
        form.instance.age = form.cleaned_data['age'] 
        form.instance.age_status = form.cleaned_data['age_status']
        form.instance.middle_name = form.cleaned_data['middle_name']
        form.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['profile'] = {}
        
        return context