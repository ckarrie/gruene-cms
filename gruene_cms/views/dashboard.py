import mimetypes
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from odf.odf2xhtml import ODF2XHTML

from gruene_cms import forms, models
from gruene_cms.views.base import AppHookConfigMixin


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
        requested_file = self.request.GET.get("path")
        full_path = os.path.join(self.object.local_path + "/", requested_file[1:])
        file_exists = os.path.isfile(full_path)
        is_image = False
        is_embed = False
        html_content = None
        is_markdown = False
        embeddable = [
            #'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            #'application/vnd.oasis.opendocument.spreadsheet',
            "application/pdf"
        ]
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

        ctx.update(
            {
                "requested_file": requested_file,
                "full_path": full_path,
                "file_exists": file_exists,
                "is_image": is_image,
                "is_embed": is_embed,
                "is_markdown": is_markdown,
                "content_type": content_type,
                "tree_items": self.object.get_tree_items(),
                "webdav_client_object": self.object,
                "html_content": html_content,
            }
        )
        return ctx


class WebDAVServeLocalFileView(WebDAVViewLocalFileView):
    model = models.WebDAVClient
    template_name = "gruene_cms/apps/dashboard/webdav_local_files.html"

    def render_to_response(self, context, **response_kwargs):
        requested_file = self.request.GET.get("path")
        full_path = os.path.join(self.object.local_path + "/", requested_file[1:])
        filename = os.path.basename(full_path)
        file_exists = os.path.isfile(full_path)
        if file_exists:
            content_type = mimetypes.guess_type(full_path)[0]
            file_data = open(full_path, "rb").read()
            response = HttpResponse(file_data, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse()
