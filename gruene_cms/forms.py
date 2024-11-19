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


class SearchForm(forms.Form):
    q = forms.CharField(max_length=100, help_text=_('max 100 chars'))

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs.update({'class': 'form-control form-control-lg'})


class WebDAVUploadForm(forms.Form):
    upload_file = forms.FileField(label=_('File'))
    location_dir = forms.ChoiceField(choices=[
        ['/', _('/ (root folder)')]
    ], label=_('storage location'))
    location_dir_new = forms.CharField(
        max_length=50,
        required=False,
        help_text=_('Name of a new sub storage location. Keep empty to save the file in the selected storage location.'),
        label=_('New sub storage location')

    )
    backup_existing_file = forms.BooleanField(
        initial=False,
        required=False,
        label=_('Backup'),
        help_text=_('Backups existing file if the same file exists')
    )

    def __init__(self, *args, **kwargs):
        possible_locations_dirs = kwargs.pop('possible_locations_dirs', None)
        #print("possible_locations_dirs", possible_locations_dirs)
        super(WebDAVUploadForm, self).__init__(*args, **kwargs)
        #print("self.fields['location_dir'].choices", self.fields['location_dir'].choices)
        if isinstance(possible_locations_dirs, list):
            self.fields['location_dir'].choices += possible_locations_dirs



