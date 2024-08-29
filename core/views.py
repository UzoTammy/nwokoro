from collections.abc import Sequence
import json
import datetime
from typing import Any

from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http.response import HttpResponse as HttpResponse
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from .forms import NumberInputForm, ProfileForm, UpdateProfileForm, MyFormSet
from .tinyproject.numtoword import convert
from .tinyproject.taxes import CanadaIncomeTaxCalculator as TaxCalc
from .models import StudentProfile


def read_profile():
    with open('./profile.json', 'r') as rf:
        content = json.load(rf)
    return content



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
    template_name = 'core/homepage.html'


class AboutMe(TemplateView):
    template_engine = 'django'

    def get_template_names(self) -> list[str]:

        return ['core/new_about_mex.html', 'core/aboutme.html']

class ResumeView(TemplateView):
    template_name = 'core/resume.html'

class TinyProjectView(TemplateView):
    template_name = 'core/portfolio/root.html'

class PortfolioScushView(TemplateView):
    template_name = 'core/portfolio/scush.html'


class PortfolioFinuelView(TemplateView):
    template_name = 'core/portfolio/finuel.html'
    

class TextingView(TemplateView):
    template_name = 'core/texting.html'


class NumberToWordView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/numtoword.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = NumberInputForm()
        
        if 'submit' in self.request.GET:
            figure = self.request.GET['enter_number'].replace(',', '')
            context['figure'] = figure
            try:
                context['word'] = convert(figure)
            except OverflowError as err:
                context['word'] = f'{err}: only number less than or equal to 999 Trillion allowed'
            
        context['form'] = form
        return context
    
class DatabaseLearningView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/databaselearning.html'

class AutomaticEmailView(TemplateView):
    template_name = 'core/portfolio/tinyprojects/auto_email.html'
    
class NewHomeView(TemplateView):
    template_name = 'core/home.html'

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