# Beispiel der `settings.py`

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
