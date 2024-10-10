from django.urls import Resolver404, resolve
from django.utils.translation import override

from cms.apphook_pool import apphook_pool
from cms.utils import get_language_from_request

# from https://docs.django-cms.org/en/latest/how_to/12-namespaced_apphooks.html#apphook-configurations

def get_app_instance(request):
    namespace, config = "", None
    if getattr(request, "current_page", None) and request.current_page.application_urls:
        app = apphook_pool.get_apphook(request.current_page.application_urls)
        if app and app.app_config:
            try:
                config = None
                with override(get_language_from_request(request)):
                    if hasattr(request, "toolbar") and hasattr(request.toolbar, "request_path"):
                        path = request.toolbar.request_path  # If v4 endpoint take request_path from toolbar
                    else:
                        path = request.path_info
                    namespace = resolve(path).namespace
                    config = app.get_config(namespace)
            except Resolver404:
                pass
    return namespace, config


class AppHookConfigMixin:
    cms_page = None

    def dispatch(self, request, *args, **kwargs):
        # get namespace and config
        self.namespace, self.config = get_app_instance(request)
        request.current_app = self.namespace
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs
        #return qs.filter(app_config__namespace=self.namespace)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'current_page': self.cms_page,
        })
        return ctx

