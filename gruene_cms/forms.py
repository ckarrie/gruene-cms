from django import forms
from gruene_cms.models import TaskItem
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class TaskCreateForm(forms.ModelForm):
    assigned_to_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Assign Task to")
    )

    class Meta:
        model = TaskItem
        fields = ["category", "summary", "assigned_to_users"]


class TaskUpdateForm(forms.ModelForm):
    assigned_to_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Assign Task to")
    )
    progress = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={'type': 'range', 'step': '10'}
        ),
        label=_('Progress')
    )
    priority = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={'type': 'range', 'step': '1', 'max': 2}
        ),
        label=_('Task Priority')
    )

    class Meta:
        model = TaskItem
        fields = ["category", "summary", "assigned_to_users", "progress", "priority"]

