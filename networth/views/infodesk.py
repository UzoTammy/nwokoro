from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from ..forms import InfoNoteForm, InfoNoteResolveForm
from ..models import InfoNote


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class InfoDeskListView(StaffRequiredMixin, ListView):
    model = InfoNote
    template_name = 'networth/infodesk.html'
    context_object_name = 'notes'

    def get_queryset(self):
        qs = InfoNote.objects.filter(owner=self.request.user)
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        category = self.request.GET.get('category')
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InfoNoteForm()
        context['status_choices'] = InfoNote.STATUS_CHOICES
        context['priority_choices'] = InfoNote.PRIORITY_CHOICES
        context['category_choices'] = InfoNote.CATEGORY_CHOICES
        all_notes = InfoNote.objects.filter(owner=self.request.user)
        context['open_count'] = all_notes.filter(status__in=['pending', 'in_progress']).count()
        context['status_stats'] = [
            {'label': label, 'count': all_notes.filter(status=val).count()}
            for val, label in InfoNote.STATUS_CHOICES
        ]
        context['active_filters'] = {
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'category': self.request.GET.get('category', ''),
        }
        return context


class InfoNoteCreateView(StaffRequiredMixin, CreateView):
    model = InfoNote
    form_class = InfoNoteForm
    success_url = reverse_lazy('infodesk-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Note added to InfoDesk.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Could not save note. Check the form for errors.')
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        return redirect('infodesk-list')


class InfoNoteUpdateView(StaffRequiredMixin, UpdateView):
    model = InfoNote
    form_class = InfoNoteForm
    template_name = 'networth/infodesk_form.html'
    success_url = reverse_lazy('infodesk-list')

    def get_queryset(self):
        return InfoNote.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        # auto-stamp resolved_at when status flips to resolved
        instance = form.save(commit=False)
        if instance.status == 'resolved' and not instance.resolved_at:
            instance.resolved_at = timezone.now()
        elif instance.status != 'resolved':
            instance.resolved_at = None
        instance.save()
        messages.success(self.request, 'Note updated.')
        return super().form_valid(form)


class InfoNoteResolveView(StaffRequiredMixin, UpdateView):
    model = InfoNote
    form_class = InfoNoteResolveForm
    template_name = 'networth/infodesk_resolve.html'
    success_url = reverse_lazy('infodesk-list')

    def get_queryset(self):
        return InfoNote.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.status = 'resolved'
        instance.resolved_at = timezone.now()
        instance.save()
        messages.success(self.request, f'"{instance.title}" marked as resolved.')
        return super().form_valid(form)


class InfoNoteDeleteView(StaffRequiredMixin, DeleteView):
    model = InfoNote
    success_url = reverse_lazy('infodesk-list')

    def get_queryset(self):
        return InfoNote.objects.filter(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('infodesk-list')
