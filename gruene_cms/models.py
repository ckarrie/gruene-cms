import requests
from lxml import etree
from cms.models.pluginmodel import CMSPlugin
from cms.models import Page
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from filer.fields.image import FilerImageField
from filer.fields.multistorage_file import MultiStorageFileField
from djangocms_text_ckeditor.fields import HTMLField
from djangocms_text_ckeditor.models import AbstractText


TOKEN_CHOICES = (
    ('BEARER', 'BEARER'),
)
AGGREGATION_METHODS = (
    ('sum', 'Summary'),
    ('mead', 'Mean'),
)

DATATYPE_CHOICES = (
    ('float', 'Float'),
    ('int', 'Int'),
    ('text', 'Text'),
)
DEBUG_NEWS = True


class DataSource(models.Model):
    token = models.CharField(max_length=255, null=True, blank=True)
    token_type = models.CharField(choices=TOKEN_CHOICES, max_length=10, default=TOKEN_CHOICES[0][0])
    rest_api_url = models.CharField(max_length=255, help_text="http://IP_ADDRESS:8123/api/states/sensor.helper_pv_sum_yaml")
    json_attr = models.CharField(max_length=255, null=True, blank=True, help_text='For HomeAssistant use "state"')
    value_convert = models.CharField(choices=DATATYPE_CHOICES, max_length=10, default=DATATYPE_CHOICES[0][0])

    def fetch_data(self):
        url = self.rest_api_url
        headers = {}
        if self.token and self.token_type in ['BEARER']:
            headers.update({
                "Authorization": f"Bearer {self.token}",
                "content-type": "application/json",
            })
        response = requests.get(url, headers=headers)
        resp_json = response.json()
        value = 0
        if self.json_attr:
            value = resp_json.get(self.json_attr, 0)

        if self.value_convert == 'float':
            value = float(value)
        elif self.value_convert == 'int':
            value = int(float(value))
        elif self.value_convert == 'text':
            value = str(value)

        return value

    def __str__(self):
        return self.rest_api_url


class AggregatedData(models.Model):
    name = models.CharField(max_length=255)
    data_sources = models.ManyToManyField(DataSource)
    unit = models.CharField(max_length=5)
    agg_method = models.CharField(choices=AGGREGATION_METHODS, max_length=10, default=AGGREGATION_METHODS[0][0])

    def aggregate_datasources(self):
        agg_value = 0
        valid_datapoints = 0
        for ds in self.data_sources.all():
            ds_value = ds.fetch_data()
            if ds_value is not None:
                valid_datapoints += 1
                if self.agg_method in ['sum', 'mean']:
                    agg_value += ds_value

        if self.agg_method == 'mean':
            v = agg_value / valid_datapoints
        else:
            v = agg_value

        AggregatedDataHistory(value=v, agg_datasource=self).save()

        return agg_value

    def last_history(self):
        l = AggregatedDataHistory.objects.filter(agg_datasource=self).last()
        if l:
            return l
        return {'value': 'NO HISTORY DATA', 'timestamp': None}

    def __str__(self):
        return self.name


class AggregatedDataHistory(models.Model):
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    agg_datasource = models.ForeignKey(AggregatedData, on_delete=models.CASCADE)

    def __str__(self):
        return self.agg_datasource.name


class AggregatedDataNode(CMSPlugin):
    agg_datasource = models.ForeignKey(AggregatedData, on_delete=models.SET_NULL, null=True)
    display_history = models.BooleanField(default=False)
    display_unit = models.BooleanField(default=True)


class GrueneCMSImageBackgroundNode(CMSPlugin):
    background_image = FilerImageField(on_delete=models.CASCADE, related_name='+')


class GrueneCMSAnimateTypingNode(CMSPlugin):
    animated_text = models.CharField(max_length=500, help_text='Separated by |. i.e. "bla1|bla2|bla3|"')
    enable_animation = models.BooleanField(default=True)
    type_speed = models.PositiveIntegerField(default=200, help_text='Type speed in ms')
    type_delay = models.PositiveIntegerField(default=1200, help_text='Type delay in ms')
    remove_speed = models.PositiveIntegerField(default=30, help_text='Remove speed in ms')
    remove_delay = models.PositiveIntegerField(default=1500, help_text='Remove delay in ms')
    cursor_speed = models.PositiveIntegerField(default=500, help_text='Cursor speed in ms')
    
    def save(self, *args, **kwargs):
        if self.animated_text and not self.animated_text.endswith('|'):
            self.animated_text = f'{self.animated_text}|'
        super(GrueneCMSAnimateTypingNode, self).save(*args, **kwargs)


class LimitUserGroupNode(CMSPlugin):
    logged_in = models.BooleanField(default=True)
    logged_in_groups = models.ManyToManyField("auth.Group", blank=True)

    def __str__(self):
        return 'Logged in' if self.logged_in else 'Logged out'


class LoginFormNode(CMSPlugin):
    display_form = models.BooleanField(default=True)
    display_greeting = models.BooleanField(default=True)
    display_button = models.BooleanField(default=False)


class ChartJSNode(CMSPlugin):
    agg_datasource = models.ForeignKey(AggregatedData, on_delete=models.SET_NULL, null=True)
    chart_title = models.CharField(max_length=100)
    chart_width = models.PositiveIntegerField(default=500)
    chart_height = models.PositiveIntegerField(default=500)
    dataset_label = models.CharField(max_length=100)
    dataset_history_hours = models.PositiveIntegerField(default=2)


class Calendar(models.Model):
    title = models.CharField(max_length=100)
    visible_groups = models.ManyToManyField("auth.Group", blank=True, related_name='calendar_visible_groups_set')
    edit_groups = models.ManyToManyField("auth.Group", blank=True, related_name='calendar_edit_groups_set')

    def __str__(self):
        return self.title


class CalendarItem(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    dt_from = models.DateTimeField()
    dt_until = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    # link_page =

    def __str__(self):
        return self.title


class CalendarNode(CMSPlugin):
    calendars = models.ManyToManyField(Calendar, related_name='calendar_calendarnode_set')
    labeled_calendars = models.ManyToManyField(Calendar, blank=True, related_name='calendar_labeled_set')
    max_entries = models.PositiveIntegerField(default=5)
    history_entries_days = models.PositiveIntegerField(default=0)
    show_more_button = models.BooleanField(default=False)
    render_template = models.CharField(max_length=255, choices=(
        ('default', "Default"),
        ('table', "Table"),
        ('table_editable', "Table (editable)"),
    ), default='default')
    #link_detail_page =

    def copy_relations(self, oldinstance):
        # see https://docs.django-cms.org/en/latest/how_to/09-custom_plugins.html#for-foreign-key-relations-from-other-objects
        self.calendars.set(oldinstance.calendars.all())
        self.labeled_calendars.set(oldinstance.labeled_calendars.all())


class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField()

    def __str__(self):
        return self.title


class NewsImage(models.Model):
    item = models.ForeignKey("NewsItem", on_delete=models.CASCADE)
    image = FilerImageField(on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.title


class NewsItem(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    categories = models.ManyToManyField(Category)
    subtitle = HTMLField(blank=True)
    authors = models.ManyToManyField("auth.User", blank=True)
    keywords = models.CharField(max_length=255)
    summary = HTMLField(blank=True)
    content = HTMLField(blank=True)
    content_rendered = models.TextField(null=True, blank=True, editable=DEBUG_NEWS)
    published_from = models.DateTimeField()
    published_until = models.DateTimeField(null=True, blank=True)
    insert_images = models.CharField(max_length=255, default='inside-hr', choices=(
        ('inside-hr', _('Inside HRs')),
        ('replace-marker', _('Replace Marker')),
    ))

    @property
    def is_public(self):
        return True

    def __str__(self):
        return self.title

    def is_published(self):
        if self.published_until:
            return self.published_from <= timezone.now() <= self.published_until
        return self.published_from <= timezone.now()
    
    def save(self, *args, **kwargs):
        super(NewsItem, self).save(*args, **kwargs)
        if self.content:
            if DEBUG_NEWS:
                print("Start render content")
            self.content_rendered = self._render_content()
            if DEBUG_NEWS:
                print("End render content")
        super(NewsItem, self).save(*args, **kwargs)

    def _render_content(self):
        body = self.content
        news_images = list(self.newsimage_set.all().order_by('position'))
        body = body.replace('<hr>', '<hr />')
        body = f'<?xml version="1.0"?><div class="news-content">{body}</div>'
        tree = etree.ElementTree(etree.fromstring(body))
        root = tree.getroot()
        current_image_index = 0

        def create_img_tag(index):
            try:
                _news_image = news_images[index]
                _img_tag = etree.Element('img', attrib={
                    'src': _news_image.image.url,
                    'alt': _news_image.title,
                    'title': _news_image.title,
                    'class': 'news-image'
                })
                return _img_tag
            except IndexError:
                return None

        if self.insert_images == 'inside-hr':
            for hr_tag in root.iter('hr'):
                img_tag = create_img_tag(current_image_index)
                if DEBUG_NEWS:
                    print("render img_tag", hr_tag, img_tag)
                if img_tag:
                    hr_tag.addnext(img_tag)
                    root.remove(hr_tag)
                    current_image_index += 1

        elif self.insert_images == 'replace-marker':
            marker_tags = root.xpath("//span[@class='marker']")
            for marker_tag in marker_tags:
                img_tag = create_img_tag(current_image_index)
                if DEBUG_NEWS:
                    print("render img_tag", marker_tag, img_tag)
                if img_tag is not None:
                    marker_tag.getparent().replace(marker_tag, img_tag)
                    current_image_index += 1

        body = etree.tostring(root).decode()
        print("rendered body", body)
        return body


class NewsListNode(CMSPlugin):
    categories = models.ManyToManyField(Category)
    render_template = models.CharField(max_length=20, choices=(
        ('tiles', "Tiles, Image and Summary"),
        ('table', "Table, Image and Summary"),
        ('full', "Full"),
    ), default='tiles')
    max_entries = models.PositiveIntegerField(default=10)
    show_outdated = models.BooleanField(default=False)
    news_page = models.ForeignKey(Page, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'News {self.pk}'

    def get_news_items(self):
        categories = list(self.categories.all())
        news_items = NewsItem.objects.all()
        condition = models.Q(categories__in=categories)
        news_items = news_items.filter(condition).order_by('-published_from').distinct()
        return news_items

    def copy_relations(self, oldinstance):
        # see https://docs.django-cms.org/en/latest/how_to/09-custom_plugins.html#for-foreign-key-relations-from-other-objects
        self.categories.set(oldinstance.categories.all())
