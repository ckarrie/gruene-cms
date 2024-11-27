# Beispielkonfiguration
## der `settings.py`

```shell
djangocms gruene_web
nano gruene_web/gruene_web/settings.py
```

```python
ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'YOUR_PUBLIC_IP']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://gruene.tld']

INSTALLED_APPS = [
    ...
    'django.contrib.sitemaps',    
    ...
    'django_bootstrap5',
    'markdownify.apps.MarkdownifyConfig',
    'gruene_cms',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gruene',
        'USER': 'gruene',
        'PASSWORD': 'gruene',
        'HOST': 'localhost',
        'PORT': '',
    }
}
LANGUAGE_CODE = 'de'

AUTHENTICATION_BACKENDS = ['gruene_cms.backends.CaseInsensitiveModelBackend']

LANGUAGES = [
    ("de", _("German")),
    ("en", _("English")),
]

TIME_ZONE = 'Europe/Berlin'

SITE_ID = 1

CMS_TEMPLATES = (
    ("base.html", _("Standard")),
    ("gruene_v1.html", _("GRUENE v1")),
)

CMS_PERMISSION = True
FILER_ENABLE_PERMISSIONS = True

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            'a',
            'abbr',
            'acronym',
            'b',
            'blockquote',
            'em',
            'i',
            'li',
            'ol',
            'p',
            'strong',
            'ul',
            'code',
            'span',
            'div', 'class',
            'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ],
        "STRIP": False,
        "MARKDOWN_EXTENSIONS": [
            "markdown.extensions.fenced_code",
            'markdown.extensions.extra',
            "markdown.extensions.codehilite",
            "markdown.extensions.toc",
        ],
        "WHITELIST_ATTRS": [
            'href',
            'src',
            'alt',
            'class',
        ],
        "WHITELIST_PROTOCOLS": [
            'http',
            'https',
        ]
    },
}
```

## der `urls.py`

```python
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from django.contrib.sitemaps.views import sitemap
from gruene_cms.views import seo

urlpatterns = i18n_patterns(
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', admin.site.urls),
    path('filer/', include('filer.urls')),
    path('', include('cms.urls')),
)

urlpatterns += [
    path('robots.txt', seo.RobotsTxtView.as_view(), name='seo_robotstxt'),
    path('sitemap.xml', sitemap, {'sitemaps': {'cmspages': seo.GrueneCMSSitemap}}, name='seo_sitemapxml'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Setup GruenenCMS

```shell
python gruene_web/manage.py migrate
python gruene_web/manage.py gruenecms_setup
python gruene_web/manage.py runserver
```

if `gruenecms_setup` fails:

```shell
rm gruene_web/db.sqlite3 
python gruene_web/manage.py migrate
python gruene_web/manage.py gruenecms_setup
```

