import mimetypes
import os
import time
from collections import OrderedDict

import feedparser
import requests
from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from django.conf import settings
from django.core.files import File
from django.db import models
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djangocms_text_ckeditor.fields import HTMLField
from djangocms_text_ckeditor.models import AbstractText
from filer.fields.file import FilerFileField
from filer.fields.image import FilerImageField
from filer.models import Folder as FilerFolder, File as FilerFile, Image as FilerImage
from lxml import etree
from bs4 import BeautifulSoup
import metadata_parser


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

NEWS_COL_CONFIG_CHOICES = (
    (None, _('All same width')),
    ("4", _('All 4 cols')),
    ("6", _('All 6 cols')),
    ("12", _('All 12 cols')),
    ("12,6", _('First 12, others 6 cols')),
    ("12,8,4,6", _('First 12, second 8, third 4, others 6 cols')),
    ("12,4,8,6", _('First 12, second 4, third 8, others 6 cols')),
    ("12,9,3,6", _('First 12, second 9, third 3, others 6 cols')),
    ("12,4,4,4,6", _('First 12, second 4 (until fourth), others 6 cols')),
)

DEBUG_NEWS = True


class DataSource(models.Model):
    token = models.CharField(max_length=255, null=True, blank=True)
    token_type = models.CharField(choices=TOKEN_CHOICES, max_length=10, default=TOKEN_CHOICES[0][0])
    rest_api_url = models.CharField(max_length=255, help_text="http://IP_ADDRESS:8123/api/states/sensor.helper_pv_sum_yaml")
    json_attr = models.CharField(max_length=255, null=True, blank=True, help_text='For HomeAssistant use "state"')
    value_convert = models.CharField(choices=DATATYPE_CHOICES, max_length=10, default=DATATYPE_CHOICES[0][0])
    enable_for_auto_update = models.BooleanField(default=False, help_text=_('If checked, data source will be downloaded automatically'))

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

    class Meta:
        verbose_name = _('Data source')
        verbose_name_plural = _('Data sources')


class AggregatedData(models.Model):
    name = models.CharField(max_length=255)
    data_sources = models.ManyToManyField(DataSource)
    unit = models.CharField(max_length=5)
    agg_method = models.CharField(choices=AGGREGATION_METHODS, max_length=10, default=AGGREGATION_METHODS[0][0])

    def aggregate_datasources(self, limit_enable_for_auto_update=False):
        agg_value = 0
        valid_datapoints = 0
        ds_qs = self.data_sources.all()
        if limit_enable_for_auto_update:
            ds_qs = ds_qs.filter(enable_for_auto_update=True)
        for ds in ds_qs:
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
        last_adh = AggregatedDataHistory.objects.filter(agg_datasource=self).last()
        if last_adh:
            return last_adh
        return {'value': 'NO HISTORY DATA', 'timestamp': None}

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Data sources - aggregated data')
        verbose_name_plural = _('Data sources - aggregated data')


class AggregatedDataHistory(models.Model):
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    agg_datasource = models.ForeignKey(AggregatedData, on_delete=models.CASCADE)

    def __str__(self):
        return self.agg_datasource.name

    class Meta:
        verbose_name = _('Data sources - aggregated data history')
        verbose_name_plural = _('Data sources - aggregated data histories')


class AggregatedDataNode(CMSPlugin):
    agg_datasource = models.ForeignKey(AggregatedData, on_delete=models.SET_NULL, null=True)
    display_history = models.BooleanField(default=False)
    display_unit = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Data sources - aggregated data node')
        verbose_name_plural = _('Data sources - aggregated data nodes')


class GrueneCMSImageBackgroundNode(CMSPlugin):
    background_image = FilerImageField(on_delete=models.CASCADE, related_name='+')
    background_size = models.CharField(max_length=10, default="cover", choices=(
        ('auto', "Auto"),
        ('contain', "Contain"),
        ('cover', "Cover"),
    ))
    background_pos_x = models.CharField(max_length=10, default="center", choices=(
        ('center', "Center"),
        ('left', "Left"),
        ('right', "Right"),
    ))
    background_pos_y = models.CharField(max_length=10, default="top", choices=(
        ('center', "Center"),
        ('top', "Top"),
        ('bottom', "Bottom"),
    ))


class GrueneCMSAnimateTypingNode(CMSPlugin):
    animated_text = models.CharField(max_length=500, help_text='Separated by |. i.e. "bla1|bla2|bla3"')
    animation = models.CharField(max_length=20, choices=(
        ('animatetyping', 'Animate Typing'),
        #('textroll', 'Text roll'),
        ('wordsrotator', 'Wordsrotator'),
        ('rotatingtext', "Rachel Smith's rotatingtext"),
    ), default='animatetyping')
    enable_animation = models.BooleanField(default=True)
    type_speed = models.PositiveIntegerField(default=200, help_text='Type speed in ms')
    type_delay = models.PositiveIntegerField(default=1200, help_text='Type delay in ms')
    remove_speed = models.PositiveIntegerField(default=30, help_text='Remove speed in ms')
    remove_delay = models.PositiveIntegerField(default=1500, help_text='Remove delay in ms')
    cursor_speed = models.PositiveIntegerField(default=500, help_text='Cursor speed in ms')
    wordsrotator_stoponhover = models.BooleanField(default=False)
    wordsrotator_speed = models.PositiveIntegerField(default=1000)
    wordsrotator_animation_in = models.CharField(max_length=255, null=True, blank=True, help_text='See <a href="https://animate.style/">https://animate.style/</a> for options')
    wordsrotator_animation_out = models.CharField(max_length=255, null=True, blank=True, help_text='See <a href="https://animate.style/">https://animate.style/</a> for options')

    def get_word_list(self):
        return self.animated_text.split('|')


class LimitUserGroupNode(CMSPlugin):
    logged_in = models.BooleanField(default=True)
    logged_in_groups = models.ManyToManyField("auth.Group", blank=True)

    def __str__(self):
        return 'Logged in' if self.logged_in else 'Logged out'

    def copy_relations(self, oldinstance):
        self.logged_in_groups.set(oldinstance.logged_in_groups.all())


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

    class Meta:
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendars')


class CalendarItem(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, verbose_name=_('Calendar'))
    title = models.CharField(max_length=100, verbose_name=_('Title'))
    subtitle = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Subtitle'))
    dt_from = models.DateTimeField(verbose_name=_('Event begin'))
    dt_until = models.DateTimeField(null=True, blank=True, verbose_name=_('Event end'))
    full_day = models.BooleanField(default=False, verbose_name=_('Full day'))
    location = models.CharField(max_length=255, verbose_name=_('Location'))
    linked_page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Linked page'))
    linked_news = models.ForeignKey('NewsItem', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Linked News'))

    def __str__(self):
        return self.title

    def is_active(self):
        now = timezone.now()
        if self.dt_until:
            return (self.dt_until >= now) and (self.dt_from <= now)
        return self.dt_from.date() == now.date()

    def is_past(self):
        now = timezone.now()
        if self.dt_until:
            return (self.dt_until.date() < now.date()) and (self.dt_from.date() < now.date())
        return self.dt_from.date() < now.date()

    class Meta:
        verbose_name = _('Calendar item')
        verbose_name_plural = _('Calendar items')


class CalendarNode(CMSPlugin):
    calendars = models.ManyToManyField(Calendar, related_name='calendar_calendarnode_set')
    labeled_calendars = models.ManyToManyField(Calendar, blank=True, related_name='calendar_labeled_set')
    max_entries = models.PositiveIntegerField(default=5)
    history_entries_days = models.PositiveIntegerField(default=0)
    show_more_button = models.BooleanField(default=False)
    render_template = models.CharField(max_length=255, choices=(
        ('default', "Default"),
        ('table', "Table"),
        ('table2', "Table 2 (without head)"),
        ('table_editable', "Table (editable)"),
    ), default='default')
    linked_news_page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True)

    def copy_relations(self, oldinstance):
        # see https://docs.django-cms.org/en/latest/how_to/09-custom_plugins.html#for-foreign-key-relations-from-other-objects
        self.calendars.set(oldinstance.calendars.all())
        self.labeled_calendars.set(oldinstance.labeled_calendars.all())

    def get_calendar_items(self):
        calendar_items = CalendarItem.objects.filter(
            calendar__in=self.calendars.all()
        )
        history_datetime = timezone.now()
        if self.history_entries_days:
            history_datetime = timezone.now() - timezone.timedelta(days=self.history_entries_days)

        calendar_items = calendar_items.filter(
            models.Q(dt_from__gte=history_datetime) | models.Q(dt_until__gte=history_datetime)
        )

        calendar_items = calendar_items.order_by('dt_from').distinct()

        if calendar_items.count() > self.max_entries:
            calendar_items = calendar_items[:self.max_entries]

        # Add Link
        for item in calendar_items:
            if self.linked_news_page and item.linked_news:
                item.linked_url = reverse('gruene_cms_news:detail', kwargs={'slug': item.linked_news.slug})
            if item.linked_page:
                item.linked_url = item.linked_page.get_absolute_url()

        return calendar_items


class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField()
    url = models.URLField(null=True, blank=True)
    logo = FilerImageField(null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('News category')
        verbose_name_plural = _('News categories')


class NewsFeedReader(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(null=True, blank=True)
    author_user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    enable_for_auto_update = models.BooleanField(default=False, help_text=_('If checked, news will be synced automatically'))
    active_auto_update = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def fetch_feed(self):
        # Enter Lock
        self.active_auto_update = False
        self.save(update_fields=['active_auto_update'])

        # Parse Feed
        feed = feedparser.parse(self.url)
        got_updates = False
        for feed_entry in feed.entries:
            feed_entry_link = feed_entry.get('link')
            if feed_entry_link:
                existing_newsitem = NewsItem.objects.filter(
                    newsfeedreader_external_link=feed_entry_link
                )
                if not existing_newsitem.exists():
                    feed_entry_title = feed_entry.get('title')
                    feed_entry_summary = feed_entry.get('summary')

                    # RSS
                    if not feed_entry_summary:
                        feed_entry_summary = feed_entry.get('description')
                    
                    # extract image
                    feed_entry_content = feed_entry.get('content')
                    newsfeedreader_external_image_url = None
                    if feed_entry_content:
                        try:
                            feed_entry_content = feed_entry_content[0].value
                            #feed_entry_content = f'<html><body><div>{feed_entry_content}</div></body></html>'
                            bs_parsed = BeautifulSoup(feed_entry_content, 'html.parser')
                            img_elem = bs_parsed.find_all('img')[0]
                            if feed_entry_content:
                                img_src = img_elem['src']
                                if img_src:
                                    newsfeedreader_external_image_url = img_src
                        except (IndexError, KeyError):
                            newsfeedreader_external_image_url = None

                    # RSS: add missing
                    # Image from Page <meta property="og:image"> and
                    # Summary from <meta property="og:description">
                    if not newsfeedreader_external_image_url:
                        page = metadata_parser.MetadataParser(url=feed_entry_link, search_head_only=True)
                        newsfeedreader_external_image_url = page.get_metadata_link('image')
                        if not feed_entry_summary:
                            page_metadata_descriptions = page.parsed_result.get_metadatas('description')
                            if page_metadata_descriptions:
                                feed_entry_summary = page_metadata_descriptions[0]

                    if isinstance(feed_entry_summary, (tuple, list)):
                        feed_entry_summary = feed_entry_summary[0]
                    feed_entry_published_parsed = feed_entry.get('published_parsed')
                    feed_entry_keyswords = feed_entry.get('author_detail', {}).get('name', self.title)

                    dt = timezone.datetime.fromtimestamp(time.mktime(feed_entry_published_parsed))
                    published_from = timezone.make_aware(dt, timezone=timezone.get_current_timezone())
                    news_item_slug = slugify(feed_entry_title)[:50]
                    news_item = NewsItem(
                        title=feed_entry_title,
                        slug=news_item_slug,
                        summary=f'<p>{feed_entry_summary}</p>',
                        keywords=feed_entry_keyswords,
                        published_from=published_from,
                        newsfeedreader_source=self,
                        newsfeedreader_external_link=feed_entry_link,
                        newsfeedreader_external_image_url=newsfeedreader_external_image_url
                    )

                    news_item.save()
                    news_item.authors.set([self.author_user])
                    news_item.categories.set([self.category])
                    got_updates = True
        if got_updates:
            self.last_updated = timezone.now()
            self.save(update_fields=['last_updated'])

        # Release Lock
        self.active_auto_update = False
        self.save(update_fields=['active_auto_update'])

    class Meta:
        verbose_name = _('Newsfeed reader')
        verbose_name_plural = _('Newsfeed readers')


class NewsImage(models.Model):
    item = models.ForeignKey("NewsItem", on_delete=models.CASCADE)
    image = FilerImageField(on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('News image')
        verbose_name_plural = _('News images')


class NewsAttachment(models.Model):
    item = models.ForeignKey("NewsItem", on_delete=models.CASCADE)
    filefield = FilerFileField(on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    position = models.PositiveIntegerField(default=5)

    def __str__(self):
        if self.title:
            return self.title
        return str(self.filefield)

    class Meta:
        verbose_name = _('News attachment')
        verbose_name_plural = _('News attachments')


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
    insert_images = models.CharField(max_length=255, default='replace-marker', choices=(
        #('inside-hr', _('Inside HRs')),
        ('replace-marker', _('Replace Marker')),
    ))
    # For NewsReader
    newsfeedreader_source = models.ForeignKey(NewsFeedReader, null=True, blank=True, on_delete=models.CASCADE)
    newsfeedreader_external_link = models.URLField(null=True, blank=True)
    newsfeedreader_external_image_url = models.URLField(null=True, blank=True)

    @property
    def is_public(self):
        return True

    @property
    def keywords_list(self):
        return [x.strip() for x in self.keywords.split(',')]

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

    def get_all_images(self):
        images = [
            self.get_first_image()
        ]
        ni_qs = self.newsimage_set.order_by('position')
        if ni_qs.count() > 1:
            for news_image in ni_qs[1:]:
                images.append({
                    'url': news_image.image.url,
                    'alt_text': news_image.title,
                    'is_cat_img': False
                })
        return images

    def get_all_attachments(self):
        att = []
        for na in self.newsattachment_set.order_by('position'):
            mime_maintype = na.filefield.mime_maintype
            mime_subtype = na.filefield.mime_subtype
            if mime_maintype in ['audio', 'font', 'video']:
                icon_url = staticfiles_storage.url(f'filer/icons/file-{mime_maintype}.svg')
            elif mime_maintype == 'application' and mime_subtype in ['zip', 'pdf']:
                icon_url = staticfiles_storage.url(f'filer/icons/file-{mime_subtype}.svg')
            else:
                icon_url = staticfiles_storage.url('filer/icons/file-unknown.svg')

            att.append({
                'url': na.filefield.url,
                'title': str(na),
                'subtitle': na.subtitle,
                'size': na.filefield.size,
                'icon_url': icon_url
            })
        return att

    def get_related_objects(self):
        links = OrderedDict()
        links['calendar_items'] = self.calendaritem_set.all().order_by('dt_from')
        #links['external'] = []
        #links['categories'] = []
        links['keywords'] = self.keywords_list
        links['images'] = self.get_all_images()
        links['attachments'] = self.get_all_attachments()

        return links

    def get_first_image(self):
        news_image = self.newsimage_set.order_by('position').first()
        url = "/static/images/sunflower.svg"
        alt_text = ""
        is_cat_img = True
        if news_image:
            url = news_image.image.url
            alt_text = news_image.title
            is_cat_img = False
        elif self.newsfeedreader_external_image_url:
            url = self.newsfeedreader_external_image_url
            alt_text = self.title
            is_cat_img = False
        else:
            category = self.categories.filter(logo__isnull=False).first()
            if category:
                url = category.logo.url
                alt_text = category.title
                is_cat_img = True

        return {
            'url': url,
            'alt_text': alt_text,
            'is_cat_img': is_cat_img,
        }

    def _render_content(self):
        body = self.content
        news_images = list(self.newsimage_set.all().order_by('position'))
        soup = BeautifulSoup(body, 'html.parser')
        current_image_index = 0

        def create_img_tag(index):
            try:
                _news_image = news_images[index]
                _img_tag = soup.new_tag('img', attrs={
                    'src': _news_image.image.url,
                    'alt': _news_image.title,
                    'title': _news_image.title,
                    'class': 'news-image float-md-end imgshadow mt-sm-5 mb-sm-5 ms-md-5 rounded-3 img-fluid'
                })
                return _img_tag

            except IndexError:
                return None

        if self.insert_images == 'inside-hr':
            for hr_tag in soup.find_all('hr'):
                img_tag = create_img_tag(current_image_index)
                if DEBUG_NEWS:
                    print("render img_tag", hr_tag, img_tag)
                if img_tag:
                    hr_tag.addnext(img_tag)
                    soup.remove(hr_tag)
                    current_image_index += 1

        elif self.insert_images == 'replace-marker':
            marker_tags = soup.find_all("span", {'class': "marker"})
            for marker_tag in marker_tags:
                img_tag = create_img_tag(current_image_index)
                if DEBUG_NEWS:
                    print("render img_tag", marker_tag, img_tag)
                if img_tag is not None:
                    marker_tag.replace_with(img_tag)
                    current_image_index += 1

        body = str(soup)
        return body

    class Meta:
        verbose_name = _('News item')
        verbose_name_plural = _('News items')


class NewsListNode(CMSPlugin):
    categories = models.ManyToManyField(Category)
    render_template = models.CharField(max_length=20, choices=(
        ('tiles', "Tiles, Image and Summary"),
        ('table', "Table, Image and Summary"),
        ('card_v1', "Cards, Variant 1, two cols"),
        ('card_v2', "Cards, Variant 2, one col"),
        ('full', "Full"),
    ), default='tiles')
    max_entries = models.PositiveIntegerField(default=10)
    show_outdated = models.BooleanField(default=False)
    news_page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True)
    title_h = models.IntegerField(default=3, choices=(
        (1, 'h1'),
        (2, 'h2'),
        (3, 'h3'),
        (4, 'h4'),
    ))
    extra_row_classes = models.CharField(
        max_length=255, null=True, blank=True,
        help_text=_('Example: "mb-3" or "g-5"')
    )
    extra_col_classes = models.CharField(
        max_length=255, null=True, blank=True,
        help_text=_('Example: "col-12" or "col-12 col-sm-6 col-md-6 col-lg-12 col-xl-12 col-xxl-12" for two-col for small screens')
    )

    show_date = models.BooleanField(default=False)
    show_feed_title = models.BooleanField(default=False)
    show_newsitem_separator = models.BooleanField(default=False)
    show_category_image = models.BooleanField(default=False)
    extra_meta_classes = models.CharField(max_length=255, null=True, blank=True)
    enable_masonry = models.BooleanField(default=True)
    col_lg_config = models.CharField(max_length=15, null=True, blank=True, choices=NEWS_COL_CONFIG_CHOICES)
    col_xl_config = models.CharField(max_length=15, null=True, blank=True, choices=NEWS_COL_CONFIG_CHOICES)

    def __str__(self):
        return f'News {self.pk}'

    @property
    def subtitle_h(self):
        return self.title_h + 1

    @property
    def col_lg_others(self):
        if self.col_lg_config:
            col_config_splitted = [int(x) for x in self.col_lg_config.split(',')]
            col_config_others = col_config_splitted[-1]
            return col_config_others
        return 12

    @property
    def col_xl_others(self):
        if self.col_xl_config:
            col_config_splitted = [int(x) for x in self.col_xl_config.split(',')]
            col_config_others = col_config_splitted[-1]
            return col_config_others
        return 12

    def get_col_configs(self, default, col_config, news_items_count):
        col_config_by_items = [default] * news_items_count
        if col_config:
            col_config_splitted = [int(x) for x in col_config.split(',')]
            for i, x in enumerate(col_config_splitted):
                try:
                    col_config_by_items[i] = x
                except IndexError:
                    pass
        return col_config_by_items

    def get_news_items(self):
        categories = list(self.categories.all())
        news_items = NewsItem.objects.all()
        condition = models.Q(categories__in=categories)
        news_items = news_items.filter(condition).order_by('-published_from').distinct()
        if news_items.count() > self.max_entries:
            news_items = news_items[:self.max_entries]

        news_items_count = news_items.count()

        col_lg_config_by_items = self.get_col_configs(self.col_lg_others, self.col_lg_config, news_items_count)
        col_xl_config_by_items = self.get_col_configs(self.col_xl_others, self.col_xl_config, news_items_count)

        item_index = 0

        for news_item in news_items:
            first_image = news_item.get_first_image()
            news_item.first_image_url = first_image['url']
            news_item.first_image_alt_text = first_image['alt_text']
            news_item.first_image_is_cat_img = first_image['is_cat_img']
            news_item.show_first_image = True
            news_item.item_col_lg_config = col_lg_config_by_items[item_index]
            news_item.item_col_xl_config = col_xl_config_by_items[item_index]
            item_index += 1

            if news_item.newsfeedreader_external_link:
                news_item.link_to_url = news_item.newsfeedreader_external_link
                news_item.link_is_external = True
                news_item.detail_link = False
            else:
                anchor = f'#news-{news_item.slug}'
                news_page_url = self.news_page.get_absolute_url()
                news_item.link_to_url = f'{news_page_url}{anchor}'
                news_item.link_is_external = False
                news_item.detail_link = reverse('gruene_cms_news:detail', kwargs={'slug': news_item.slug})

            if news_item.first_image_is_cat_img and not self.show_category_image:
                news_item.show_first_image = False

        return news_items

    def copy_relations(self, oldinstance):
        # see https://docs.django-cms.org/en/latest/how_to/09-custom_plugins.html#for-foreign-key-relations-from-other-objects
        self.categories.set(oldinstance.categories.all())


class NewsPageConfig(models.Model):
    namespace = models.CharField(
        _("instance namespace"),
        default=None,
        max_length=100,
        unique=True,
    )
    paginate_by = models.PositiveIntegerField(
        _("paginate size"),
        blank=False,
        default=5,
    )
    render_template = models.CharField(max_length=100, choices=(
        ('detail', "Detail with Inline Images"),
        ('detail_img_content', "Detail with Images-Col and Content-Col"),
        ('detail_content_img', "Detail with Content-Col and Images-Col"),
        ('detail_img_then_content', "Detail with Images-Row then Content-Row"),
    ), default='detail')

    def __str__(self):
        return f'paginate_by={self.paginate_by} ns={self.namespace} render={self.get_render_template_display()}'


class TaskItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_('Category'))
    summary = HTMLField(blank=True, verbose_name=_('Task Summary'))
    assigned_to_users = models.ManyToManyField("auth.User", verbose_name=_('Assign Task to'))
    created_at = models.DateTimeField(auto_now_add=True)
    progress = models.PositiveIntegerField(default=0, verbose_name=_('Progress'))
    priority = models.PositiveIntegerField(default=0, choices=(
        (0, _('Normal')),
        (1, _('Warning')),
        (2, _('Danger')),
    ), verbose_name=_('Task Priority'))

    def get_priority_table_css_class(self):
        tr_class = {
            0: '',
            1: 'table-warning',
            2: 'table-danger',
        }[self.priority]

        if self.progress == 100:
            tr_class += ' text-decoration-line-through'
        return tr_class


class TaskComment(models.Model):
    task = models.ForeignKey(TaskItem, on_delete=models.CASCADE)
    comment = HTMLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.CASCADE)


class TaskNode(CMSPlugin):
    categories = models.ManyToManyField(Category)
    limit_own_tasks = models.BooleanField(default=False)
    include_obsolete = models.BooleanField(default=False)
    render_template = models.CharField(max_length=40, choices=(
        ('list', 'Task List'),
        ('list_with_assignments', 'Task List (with assignments)'),
        ('summary', 'Summary my Tasks')
    ), default='list')

    def copy_relations(self, oldinstance):
        self.categories.set(oldinstance.categories.all())

    def get_task_items(self, user=None):
        tasks = TaskItem.objects.all()
        if self.limit_own_tasks and user.is_authenticated:
            tasks = tasks.filter(assigned_to_users=user)
        if self.categories.exists():
            tasks = tasks.filter(category__in=self.categories.all())
        if not self.include_obsolete:
            tasks = tasks.filter(progress__lt=100)
        return tasks.order_by('created_at')



def get_local_path(base_path, subfolder=None):
    app_dir = settings.BASE_DIR / 'gruenecms_local'
    if subfolder:
        path = os.path.join(app_dir, base_path, subfolder)
    else:
        path = os.path.join(app_dir, base_path)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_local_webdav_path(basefolder=None, subfolder=None):
    return get_local_path('webdav', subfolder=subfolder)

def get_local_addressbook_path(subfolder=None):
    return get_local_path('addressbooks', subfolder=subfolder)

def get_local_contacts_path(subfolder=None):
    return get_local_path('contacts', subfolder=subfolder)


class NextCloudAccount(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    nextcloud_username = models.CharField(max_length=50)
    nextcloud_app_password = models.CharField(max_length=255)
    nextcloud_url = models.CharField(
        max_length=255,
        help_text=_('Without tailing slash'),
        default="https://wolke.netzbegruenung.de"
    )

    @property
    def local_webdav_path(self):
        return get_local_webdav_path(subfolder=str(self.pk))

    @property
    def local_addressbook_path(self):
        return get_local_addressbook_path(subfolder=str(self.pk))

    @property
    def local_contacts_path(self):
        return get_local_contacts_path(subfolder=str(self.pk))

    def get_scope_url(self, scope):
        dav = f'{self.nextcloud_url}/remote.php/dav'
        scope_url = {
            'files': f'{dav}/files/{self.nextcloud_username}',
            'addressbooks': f'{dav}/addressbooks/users/{self.nextcloud_username}',
            "calendars": f'{dav}/calendars/{self.nextcloud_username}'
        }[scope]
        return scope_url

    def get_webdavclient(self, scope):
        scope_url = self.get_scope_url(scope=scope)
        from webdav3.client import Client
        webdav_hostname = f'{scope_url}'
        options = {
            'webdav_hostname': webdav_hostname,
            'webdav_login': self.nextcloud_username,
            'webdav_password': self.nextcloud_app_password
        }
        client = Client(options)
        return client

    def list_file_shares(self):
        client = self.get_webdavclient(scope='files')
        return client.list()

    def list_addressbooks(self):
        client = self.get_webdavclient(scope='addressbooks')
        folder_list = client.list()
        remove_from_list = [
            f'{self.nextcloud_username}/',
            'z-server-generated--system/'
        ]
        for r in remove_from_list:
            if r in folder_list:
                folder_list.remove(r)
        return [slug.replace('/', '') for slug in folder_list]

    def download_via_requests(self, url, to_path):
        import requests
        from requests.auth import HTTPBasicAuth
        request = requests.get(url, auth=HTTPBasicAuth(self.nextcloud_username, self.nextcloud_app_password))
        open(to_path, 'wb').write(request.content)

    def download_addressbook(self, slug="contacts"):
        scope_url = self.get_scope_url(scope="addressbooks")
        url = f'{scope_url}/{slug}/?export'
        to_path = f'{self.local_addressbook_path}/{slug}.vcf'
        self.download_via_requests(url, to_path)

    def list_calendars(self):
        client = self.get_webdavclient(scope='calendars')
        folder_list = client.list()
        remove_from_list = [
            f'{self.nextcloud_username}/',
            f'aufgaben/',
            f'inbox/',
            f'outbox/',
            f'trashbin/',
        ]
        for r in remove_from_list:
            if r in folder_list:
                folder_list.remove(r)
        return [slug.replace('/', '') for slug in folder_list]

    def download_calendar(self, slug='personal'):
        scope_url = self.get_scope_url(scope="calendars")
        url = f'{scope_url}/{slug}/?export'
        to_path = f'{self.local_contacts_path}/{slug}.ics'
        self.download_via_requests(url, to_path)

    def create_calendaritems(self, files):
        import icalendar
        for full_path in files:
            with open(full_path) as f:
                calendar = icalendar.Calendar.from_ical(f.read())
                for event in calendar.walk('VEVENT'):
                    calendar_events.append(event)


class NextCloudCalendar(models.Model):
    account = models.ForeignKey(NextCloudAccount, on_delete=models.CASCADE)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    calendar_slug = models.CharField(max_length=255)



class WebDAVClient(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    webdav_hostname = models.CharField(max_length=255)
    webdav_login = models.CharField(max_length=50)
    webdav_app_password = models.CharField(max_length=255)
    webdav_path = models.CharField(max_length=255, null=True, blank=True, help_text='URL to replace: /remote.php/dav/files/KarrieCh/')
    entry_path = models.CharField(max_length=255, null=True, blank=True, help_text='i.e. 02_Kommunikation/02_Presse')
    entry_path_title = models.CharField(max_length=255, null=True, blank=True)
    local_path = models.FilePathField(null=True, blank=True, path=get_local_webdav_path, allow_files=False, allow_folders=True)
    access_groups = models.ManyToManyField("auth.Group", blank=True)
    enable_for_auto_update = models.BooleanField(default=False, help_text=_('If checked, folders will be synced automatically'))
    force_mimetype = models.CharField(max_length=255, null=True, blank=True, choices=(
        (None, _('Use file extensions')),
        ('application/csv',  _('.csv | Comma separated')),
        ('text/x-vcard',     _('.vcf | Contacts')),
        ('text/x-vcalendar', _('.vcs | Calendar')),
    ))

    def save(self, *args, **kwargs):
        super(WebDAVClient, self).save(*args, **kwargs)
        self.local_path = get_local_webdav_path(subfolder=str(self.pk))
        super(WebDAVClient, self).save(*args, **kwargs)

    def get_webdav_client(self):
        from webdav3.client import Client
        options = {'webdav_hostname': self.webdav_hostname, 'webdav_login': self.webdav_login, 'webdav_password': self.webdav_app_password}
        client = Client(options)
        return client

    def sync_folder(self):
        client = self.get_webdav_client()
        remote_path = self.entry_path or ""
        client.sync(remote_directory=remote_path, local_directory=self.local_path)

    def webdav_download_sync(self):
        client = self.get_webdav_client()
        remote_path = self.entry_path or ""
        client.download_sync(remote_path=remote_path, local_path=self.local_path)

    def get_tree_items(self, entry_path=None):
        local_path = self.local_path
        tree_level = 0

        def path_to_dict(path, sub_level):
            d = OrderedDict()
            d['name'] = os.path.basename(path)
            d['path'] = path.replace(self.local_path, '')
            d['level'] = sub_level
            if os.path.isdir(path):
                d['type'] = "folder"
                content = [path_to_dict(os.path.join(path, x), sub_level=sub_level + 1) for x in sorted(os.listdir(path))]
                d['content'] = content
            else:
                d['type'] = "file"
                d['mtype'] = mimetypes.guess_type(d['name'])[0]
                if d['mtype'] and d['mtype'].startswith('image/'):
                    d['type'] = "image"
            return d

        if entry_path:
            local_path = os.path.join(local_path, entry_path)

        tree = path_to_dict(local_path, sub_level=tree_level + 1)
        tree['name'] = self.entry_path_title or '/wolke'
        tree['level'] = tree_level

        return tree

    def __str__(self):
        if self.title:
            return f'{self.webdav_hostname} {self.title}'
        if self.entry_path:
            return f'{self.webdav_hostname} {self.entry_path}'
        return self.webdav_hostname


class LocalFolderNode(CMSPlugin):
    webdav_client = models.ForeignKey(WebDAVClient, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    show_root_node = models.BooleanField(default=False)
    extra_css_classes = models.CharField(max_length=255, default='folder-list small')
    entry_path = models.CharField(max_length=255, null=True, blank=True, help_text='i.e. 06_Sitzungsprotokolle/Steinweiler')


class DivNode(CMSPlugin):
    div_classes = models.CharField(max_length=255, default='container')
    extra_css_classes = models.CharField(max_length=255, null=True, blank=True)
    enable_radial_bg_1 = models.BooleanField(default=False)
    enable_radial_bg_2 = models.BooleanField(default=False)
    enable_radial_bg_3 = models.BooleanField(default=False)


class SimpleMenuNode(CMSPlugin):
    include_home_page = models.BooleanField(default=False)
    start_level = models.PositiveIntegerField(default=0, help_text=_('specify from which level the navigation should be rendered...'))
    to_level = models.PositiveIntegerField(default=1, help_text=_('...and at which level it should stop'))
    extra_inactive = models.PositiveIntegerField(default=0, help_text=_('specifies how many levels of navigation should be displayed if a node is not a direct ancestor or descendant of the current active node'))
    extra_active = models.PositiveIntegerField(default=1, help_text=_('specifies how many levels of descendants of the currently active node should be displayed'))
    extra_css_classes = models.CharField(max_length=255, null=True, blank=True)
    render_template = models.CharField(max_length=40, choices=(
        ('as_p', _('As paragraphs')),
        ('as_ul_nested', _('As ul, nested')),
        ('as_ul_flat', _('As ul, flat')),
        ('as_nav_subpages', _('As nav, subpages, horizontal')),
    ), default='as_p')
    


