# gruene-cms

## Installation Grundsystem
```shell
cd ~/venvs
python3 -m venv gruene_venv
cd gruene_venv/
source bin/activate
pip install --upgrade pip
pip install psycopg2-binary
pip install django-cms
```

## Installation grunen-cms

```shell
cd ~/src/
git clone https://github.com/ckarrie/gruene-cms
pip install -e gruene-cms
```

## Pro Instanz
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
```

### Setup Database
`sudo -u postgres psql`

```sql
CREATE DATABASE gruene;
CREATE USER gruene WITH PASSWORD 'gruene';
ALTER ROLE gruene SET client_encoding TO 'utf8';
ALTER ROLE gruene SET default_transaction_isolation TO 'read committed';
ALTER ROLE gruene SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE gruene TO gruene;
GRANT postgres TO gruene;
```

```shell
python gruene_web/manage.py migrate
python gruene_web/manage.py createsuperuser
python gruene_web/manage.py runserver 127.0.0.1:9100
```

# Models

## external Datasources

```python
from gruene_cms.models import DataSource, AggregatedData
ds = DataSource.objects.first()
ds.fetch_data()

ag = AggregatedData.objects.first()
ag.aggregate_datasources()

```

# README Todo

- add doc for management command `gruenecms_setup` and `update_datasources`
- requirements fpr django-bootstrap5, pip install webdavclient3, django-markdownify, pip install pygments
- update settings.py

# Useful commands

- `manage.py cms -h`
- `manage.py cms fix-tree`
- `manage.py cms delete-orphaned-plugins`


# Contribution
## generating codehilite_styles.css

```
cd workspace/src/github/gruene-cms/gruene_cms/static/
pygmentize -S default -f html -a .codehilite > codehilite_styles.css
```

Add it to `gruenen_v1.html` Template

```html
<head>
    <link rel="stylesheet" href="{% static 'codehilite_styles.css' %}">
</head>
```