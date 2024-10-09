from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import AggregatedDataNode, \
    GrueneCMSImageBackgroundNode, \
    GrueneCMSAnimateTypingNode, \
    LimitUserGroupNode, \
    ChartJSNode, \
    CalendarNode, CalendarItem, \
    NewsListNode, NewsItem

module_name = _('GruenenCMS')


@plugin_pool.register_plugin
class AggregatedDataNodePlugin(CMSPluginBase):
    model = AggregatedDataNode
    name = _('Aggregated Data Node')
    allow_children = False
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/aggregated_data_node.html'


@plugin_pool.register_plugin
class GrueneCMSImageBackgroundNodePlugin(CMSPluginBase):
    model = GrueneCMSImageBackgroundNode
    name = _('Image as Background')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/gruenecms_image_background_node.html'


@plugin_pool.register_plugin
class GrueneCMSAnimateTypingNodePlugin(CMSPluginBase):
    model = GrueneCMSAnimateTypingNode
    name = _('Animate Typing')
    text_enabled = True
    allow_children = False
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/gruenecms_animate_typing_node.html'
    fieldsets = [
        (None, {
            'fields': (
                ('animated_text',),
            )
        }),
        (_('Advanced settings'), {
            'classes': ('collapse',),
            'fields': (
                'enable_animation',
                'type_speed',
                'type_delay',
                'remove_speed',
                'remove_delay',
                'cursor_speed',
            )
        }),
    ]


@plugin_pool.register_plugin
class LimitUserGroupNodePlugin(CMSPluginBase):
    model = LimitUserGroupNode
    name = _('Limit User/Group')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/limit_user_group_node.html'

    def render(self, context, instance, placeholder):
        context = super(LimitUserGroupNodePlugin, self).render(context, instance, placeholder)
        display_children = False
        user = context['request'].user
        if instance.logged_in and user.is_authenticated:
            if instance.logged_in_groups.count() == 0:
                display_children = True
            else:
                for user_group in user.groups.all():
                    if user_group in instance.logged_in_groups.all():
                        display_children = True
                        break
        if (not instance.logged_in) and (not user.is_authenticated):
            display_children = True

        context.update({
            'display_children': display_children
        })
        return context


@plugin_pool.register_plugin
class LoginFormNodePlugin(CMSPluginBase):
    model = LimitUserGroupNode
    name = _('Limit User')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/limit_user_group_node.html'


@plugin_pool.register_plugin
class ChartJSNodePlugin(CMSPluginBase):
    model = ChartJSNode
    name = _('Chart')
    allow_children = False
    cache = True
    module = module_name
    render_template = 'gruene_cms/plugins/chartjs_node.html'

    def render(self, context, instance, placeholder):
        context = super(ChartJSNodePlugin, self).render(context, instance, placeholder)
        dataset = []
        labels = []
        dataset_qs = instance.agg_datasource.aggregateddatahistory_set.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(hours=instance.dataset_history_hours),
            value__gt=0,
        ).order_by('timestamp')
        for ah in dataset_qs:
            dataset.append(ah.value)
            labels.append(ah.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M"))

        context.update({
            'dataset_data': dataset,
            'labels_data': labels,
        })

        return context


@plugin_pool.register_plugin
class CalendarNodePlugin(CMSPluginBase):
    model = CalendarNode
    name = _('Calendar')
    allow_children = False
    cache = False
    module = module_name

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'default': 'gruene_cms/plugins/calendar_node.html',
            'table': 'gruene_cms/plugins/calendar_node_table.html',
            'table2': 'gruene_cms/plugins/calendar_node_table_2.html',
            'table_editable': 'gruene_cms/plugins/calendar_node_table_editable.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(CalendarNodePlugin, self).render(context, instance, placeholder)

        calendar_items_qs = CalendarItem.objects.filter(
            calendar__in=instance.calendars.all()
        )
        history_datetime = timezone.now()
        if instance.history_entries_days:
            history_datetime = timezone.now() - timezone.timedelta(days=instance.history_entries_days)
        calendar_items_qs = calendar_items_qs.filter(
            dt_from__gte=history_datetime
        )

        calendar_items_qs = calendar_items_qs.order_by('dt_from')[:instance.max_entries]

        labeled_calendars = list(instance.labeled_calendars.all())

        context.update({
            'calendar_items': calendar_items_qs,
            'labeled_calendars': labeled_calendars,
            'current_dt': timezone.now()
        })

        return context


@plugin_pool.register_plugin
class NewsListNodePlugin(CMSPluginBase):
    model = NewsListNode
    name = _('News')
    allow_children = False
    cache = False
    module = module_name

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'tiles': 'gruene_cms/plugins/news_tiles_node.html',
            'table': 'gruene_cms/plugins/news_table_node.html',
            'full': 'gruene_cms/plugins/news_full_node.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(NewsListNodePlugin, self).render(context, instance, placeholder)
        context.update({
            'news_items': instance.get_news_items(),
        })
        return context
