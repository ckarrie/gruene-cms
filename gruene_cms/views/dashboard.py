from django.urls import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from gruene_cms import models
from gruene_cms import forms
from gruene_cms.views.base import AppHookConfigMixin


class AuthenticatedOnlyMixin(LoginRequiredMixin):
    #raise_exception = True
    login_url = '/dashboard/'


class TaskCreateView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.CreateView):
    model = models.TaskItem
    template_name = 'gruene_cms/apps/dashboard/task_form.html'
    form_class = forms.TaskCreateForm

    #def form_valid(self, form):
    #    if we want to manipulate save
    #    cd = form.cleaned_data
    #    self.object = form.save()
    #    return HttpResponseRedirect('/tasks/')

    def get_success_url(self):
        return reverse('gruene_cms_dashboard:task_list')


class TaskListView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.ListView):
    model = models.TaskItem
    template_name = 'gruene_cms/apps/dashboard/task_list.html'


class TaskEditView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.UpdateView):
    model = models.TaskItem
    template_name = 'gruene_cms/apps/dashboard/task_form.html'
    form_class = forms.TaskUpdateForm

    def get_success_url(self):
        return reverse('gruene_cms_dashboard:task_list')
