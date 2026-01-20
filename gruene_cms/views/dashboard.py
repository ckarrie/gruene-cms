import datetime
import mimetypes
import os
import re

import vobject
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone, decorators
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic
from django.views.decorators.cache import never_cache
from odf.odf2xhtml import ODF2XHTML
import icalendar
from gruene_cms import forms, models
from gruene_cms.views.base import AppHookConfigMixin


def _get_folders(d):
    folders = []
    for ti in d.get('content', []):
        if ti['type'] == 'folder':
            folders.append((ti['path'], ti['path']))
            folders.extend(_get_folders(ti))
    return folders


class AuthenticatedOnlyMixin(LoginRequiredMixin):
    # raise_exception = True
    login_url = "/dashboard/"


class TaskCreateView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.CreateView):
    model = models.TaskItem
    template_name = "gruene_cms/apps/dashboard/task_form.html"
    form_class = forms.TaskCreateForm

    # def form_valid(self, form):
    #    if we want to manipulate save
    #    cd = form.cleaned_data
    #    self.object = form.save()
    #    return HttpResponseRedirect('/tasks/')

    def get_success_url(self):
        return reverse("gruene_cms_dashboard:task_list")


class TaskListView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.ListView):
    model = models.TaskItem
    template_name = "gruene_cms/apps/dashboard/task_list.html"

    def get_queryset(self):
        qs = super(TaskListView, self).get_queryset()
        return qs.order_by("created_at")


class TaskEditView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.UpdateView):
    model = models.TaskItem
    template_name = "gruene_cms/apps/dashboard/task_form.html"
    form_class = forms.TaskUpdateForm

    def get_success_url(self):
        return reverse("gruene_cms_dashboard:task_list")


@decorators.method_decorator(never_cache, name="dispatch")
class WebDAVViewLocalFileView(
    AppHookConfigMixin, AuthenticatedOnlyMixin, generic.DetailView
):
    model = models.WebDAVClient
    template_name = "gruene_cms/apps/dashboard/webdav_local_files.html"

    def get_queryset(self):
        qs = super(WebDAVViewLocalFileView, self).get_queryset()
        qs = qs.filter(
            Q(user=self.request.user) | Q(access_groups__user=self.request.user)
        )
        qs = qs.distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(WebDAVViewLocalFileView, self).get_context_data(**kwargs)
        requested_file = self.request.GET.get("path") or ""
        # Normalize and constrain the requested path to stay within local_path
        base_path = os.path.abspath(self.object.local_path)
        # Ensure requested_file is treated as relative (strip leading slashes)
        relative_path = requested_file.lstrip("/")
        full_path_candidate = os.path.normpath(os.path.join(base_path, relative_path))
        # Verify that the normalized path is still inside the base_path
        if os.path.commonpath([base_path, full_path_candidate]) != base_path:
            # Fallback to base_path if an invalid or unsafe path was supplied
            full_path = base_path
            safe_requested_file = ""
        else:
            full_path = full_path_candidate
            safe_requested_file = "/" + relative_path if relative_path else ""
        full_path_splitted = safe_requested_file.split('/') if safe_requested_file else []
        file_exists = os.path.isfile(full_path)
        is_dir = os.path.isdir(full_path)
        is_image = False
        is_embed = False
        is_audio = False
        html_content = None
        is_markdown = False
        calendar_events = []
        contacts = []
        embeddable = [
            #'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            #'application/vnd.oasis.opendocument.spreadsheet',
            "application/pdf"
        ]

        if self.object.force_mimetype:
            content_type = self.object.force_mimetype
        else:
            content_type = mimetypes.guess_type(full_path)[0]

        if content_type and content_type.startswith("image/"):
            is_image = True
        if content_type and "pdf" in content_type:
            is_embed = True
        if content_type in embeddable:
            is_embed = True
        if content_type in ["text/markdown", "text/plain"]:
            content = open(full_path).read()
            # print(content)
            # html_content = '<h2>Dateiinhalt</h2>'
            # html_content += markdownify(content)
            # print(html_content)
            html_content = content
            is_markdown = True

        if content_type in [
            #'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # docx
            "application/vnd.oasis.opendocument.spreadsheet",  # ods
            "application/vnd.oasis.opendocument.text",  # odt
        ]:
            # for docx use this: https://github.com/thalescr/django-docx-import/blob/master/core/utils.py
            odhandler = ODF2XHTML(generate_css=False, embedable=True)
            result = odhandler.odf2xhtml(full_path)
            # result = result.replace('<table>', '<table class="table">')
            html_content = result

        if content_type in [
            'audio/mpeg',
            'audio/ogg',
            'audio/aac',
        ]:
            is_audio = True

        if content_type == 'text/x-vcalendar':
            with open(full_path) as f:
                calendar = icalendar.Calendar.from_ical(f.read())
                for event in calendar.walk('VEVENT'):
                    calendar_events.append(event)

        if content_type == 'text/x-vcard':
            f = open(full_path).read()
            for stack in vobject.readComponents(f):
                contacts.append(stack)

        tree_items = self.object.get_tree_items()
        folders = _get_folders(tree_items)
        if is_dir:
            current_folder = requested_file
        else:
            current_folder = os.path.dirname(requested_file)

        upload_form = forms.WebDAVUploadForm(possible_locations_dirs=folders, initial={
            'location_dir':  current_folder
        })

        ctx.update(
            {
                "requested_file": requested_file,
                "full_path": full_path,
                "file_exists": file_exists,
                "is_image": is_image,
                "is_embed": is_embed,
                "is_audio": is_audio,
                "is_markdown": is_markdown,
                "is_dir": is_dir,
                "content_type": content_type,
                "tree_items": tree_items,
                "webdav_client_object": self.object,
                "html_content": html_content,
                "calendar_events": calendar_events,
                "contacts": contacts,
                "upload_form": upload_form,
                "full_path_splitted": full_path_splitted,
            }
        )
        return ctx


@decorators.method_decorator(never_cache, name="dispatch")
class WebDAVServeLocalFileView(WebDAVViewLocalFileView):
    model = models.WebDAVClient
    template_name = "gruene_cms/apps/dashboard/webdav_local_files.html"

    def render_to_response(self, context, **response_kwargs):
        requested_file = self.request.GET.get("path")
        is_embed = self.request.GET.get("is_embed", "") == "on"
        full_path = os.path.join(self.object.local_path + "/", requested_file[1:])
        filename = os.path.basename(full_path)
        file_exists = os.path.isfile(full_path)
        if file_exists:
            content_type = mimetypes.guess_type(full_path)[0]
            file_data = open(full_path, "rb").read()
            response = HttpResponse(file_data, content_type=content_type)
            if not is_embed:
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse()


@decorators.method_decorator(never_cache, name="dispatch")
class WebDAVUploadView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.FormView):
    form_class = forms.WebDAVUploadForm
    template_name = 'gruene_cms/apps/dashboard/webdav_upload_file.html'

    def get_form_kwargs(self):
        kwargs = super(WebDAVUploadView, self).get_form_kwargs()
        webdav_obj = models.WebDAVClient.objects.get(pk=self.kwargs.get('pk'))
        kwargs.update({'possible_locations_dirs': _get_folders(webdav_obj.get_tree_items())})
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(WebDAVUploadView, self).get_context_data(**kwargs)
        ctx.update({
            'webdav_obj': models.WebDAVClient.objects.get(pk=self.kwargs.get('pk'))
        })
        return ctx

    def form_valid(self, form):
        webdav_obj = models.WebDAVClient.objects.filter(pk=self.kwargs.get('pk')).first()
        if not webdav_obj:
            form.add_error(None, "WebDAV nicht gefunden")
            return self.form_invalid(form=form)

        cd = form.cleaned_data
        file_obj = cd.get('upload_file')
        file_name = file_obj.name
        location_dir_without_leading_slash = re.sub("^/|/$", "", cd['location_dir'])
        location_dir_new_without_leading_slash = re.sub("^/|/$", "", cd['location_dir_new'])

        if cd['location_dir_new']:
            full_path_new_dir = os.path.join(webdav_obj.local_path, location_dir_without_leading_slash, location_dir_new_without_leading_slash)
            if not os.path.exists(full_path_new_dir):
                os.makedirs(full_path_new_dir, exist_ok=True)
            full_path_new_file = os.path.join(webdav_obj.local_path, location_dir_without_leading_slash, location_dir_new_without_leading_slash, file_name)
        else:
            full_path_new_file = os.path.join(webdav_obj.local_path, location_dir_without_leading_slash, file_name)

        if os.path.exists(full_path_new_file):
            if cd['backup_existing_file']:
                dt = timezone.now().strftime('%Y-%m-%d-%H-%m-%S')
                backup_file_name = f'backup-{dt}-{file_name}'
                full_path_backup_file = os.path.join(webdav_obj.local_path, location_dir_without_leading_slash, backup_file_name)
                os.rename(full_path_new_file, full_path_backup_file)
            else:
                os.remove(full_path_new_file)

        with open(full_path_new_file, 'wb+') as disc_file_obj:
            for chunk in file_obj.chunks():
                disc_file_obj.write(chunk)

        relative_full_path_new_file = full_path_new_file.replace(webdav_obj.local_path, "")
        url = reverse('gruene_cms_dashboard:webdav_view_local_file', kwargs={'pk': self.kwargs.get('pk')}) + f'?path={relative_full_path_new_file}'
        return HttpResponseRedirect(url)

    def get_success_url(self):
        url = reverse('gruene_cms_dashboard:webdav_view_local_file', kwargs={'pk': self.kwargs.get('pk')}) + '?path=/'
        return url


class CalendarItemCreateView(AppHookConfigMixin, AuthenticatedOnlyMixin, generic.CreateView):
    form_class = forms.CreateCalendarItemModelForm
    model = forms.CalendarItem
    template_name = 'gruene_cms/apps/dashboard/calendaritem_form.html'

    def form_valid(self, form):
        cd = form.cleaned_data
        #print(cd)
        form_date = cd.get('date')
        form_time = cd.get('time')
        form_duration = cd.get('duration')

        dt_until = None
        dt_from = timezone.now().replace(
            year=form_date.year,
            month=form_date.month,
            day=form_date.day,
            hour=form_time.hour,
            minute=form_time.minute,
            second=0,
            microsecond=0,
            tzinfo=None
        )
        dt_from = timezone.make_aware(dt_from, timezone=timezone.get_current_timezone())

        if form_duration:
            dt_until = dt_from + datetime.timedelta(hours=form_duration.hour, minutes=form_duration.minute)

        if dt_from < timezone.now():
            form.add_error('date', 'Datum/Uhrzeit muss in der Zukunft liegen')
            form.add_error('time', 'Datum/Uhrzeit muss in der Zukunft liegen')
            return self.form_invalid(form=form)

        cd.pop('date')
        cd.pop('time')
        cd.pop('duration')

        new_calendaritem = form.save(commit=False)
        new_calendaritem.dt_from = dt_from
        new_calendaritem.dt_until = dt_until
        new_calendaritem.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        next_param = self.request.GET.get('next')
        if next_param and url_has_allowed_host_and_scheme(
                url=next_param,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
        ):
            return next_param
        return '/'


class DashboardLoginView(AppHookConfigMixin, LoginView):
    template_name = 'gruene_cms/apps/login.html'

    def get_context_data(self, **kwargs):
        ctx = super(DashboardLoginView, self).get_context_data(**kwargs)
        error_msgs = {
            'share': 'Share-Link ungültig oder abgelaufen'
        }
        defalt_message = 'Zugangsdaten erforderlich'

        error_code = self.request.GET.get('code', None)
        if error_code and error_code in error_msgs.keys():
            error_msg = error_msgs.get(error_code) or defalt_message
        else:
            error_msg = defalt_message

        ctx['error_msg'] = error_msg

        return ctx

