from django import forms
from gruene_cms.models import TaskItem
from django.contrib.auth.models import User


class TaskCreateForm(forms.ModelForm):
    assigned_to_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = TaskItem
        fields = ["category", "summary", "assigned_to_users"]


class TaskUpdateForm(forms.ModelForm):
    assigned_to_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    progress = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'range', 'step': '10'}))

    class Meta:
        model = TaskItem
        fields = ["category", "summary", "assigned_to_users", "progress"]

