from collections import OrderedDict

from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from . import models, forms

module_name = _('GruenenCMS')


@plugin_pool.register_plugin
class AggregatedDataNodePlugin(CMSPluginBase):
    model = models.AggregatedDataNode
    name = _('Aggregated Data Node')
    allow_children = False
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/aggregated_data_node.html'


@plugin_pool.register_plugin
class GrueneCMSImageBackgroundNodePlugin(CMSPluginBase):
    model = models.GrueneCMSImageBackgroundNode
    name = _('Image as Background')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/gruenecms_image_background_node.html'


@plugin_pool.register_plugin
class GrueneCMSAnimateTypingNodePlugin(CMSPluginBase):
    model = models.GrueneCMSAnimateTypingNode
    name = _('Animate Typing')
    text_enabled = True
    allow_children = False
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/gruenecms_animate_typing_node.html'
    fieldsets = [
        (None, {
            'fields': (
                ('animated_text', 'animation'),
            )
        }),
        (_('AnimateTyping settings'), {
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
        (_('Wordsrotator settings'), {
            'classes': ('collapse',),
            'fields': (
                'wordsrotator_stoponhover',
                'wordsrotator_speed',
                'wordsrotator_animation_in',
                'wordsrotator_animation_out',
            )
        }),
    ]


@plugin_pool.register_plugin
class LimitUserGroupNodePlugin(CMSPluginBase):
    model = models.LimitUserGroupNode
    name = _('Limit User/Group')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/limit_user_group_node.html'

    def render(self, context, instance, placeholder):
        context = super(LimitUserGroupNodePlugin, self).render(context, instance, placeholder)
        display_children = False
        matched_options = {
            'is_logged_in': None,
            'is_not_logged_in': None,
            'matched_user_group': None,
        }
        user = context['request'].user
        instance_groups = instance.logged_in_groups.all()
        if instance.logged_in and user.is_authenticated:
            if instance_groups.count() == 0:
                display_children = True
                matched_options['is_logged_in'] = True
            else:
                for user_group in user.groups.all():
                    if user_group in instance_groups:
                        display_children = True
                        matched_options['matched_user_group'] = user_group.name
                        break
        if (not instance.logged_in) and (not user.is_authenticated):
            display_children = True
            matched_options['is_not_logged_in'] = True

        context.update({
            'display_children': display_children,
            'matched_options': matched_options,
            'instance_groups': instance_groups,
            'user_groups': user.groups.all()
        })
        return context


@plugin_pool.register_plugin
class LoginFormNodePlugin(CMSPluginBase):
    model = models.LoginFormNode
    name = _('Login Form')
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/login_form_node.html'


@plugin_pool.register_plugin
class ChartJSNodePlugin(CMSPluginBase):
    model = models.ChartJSNode
    name = _('Chart')
    allow_children = False
    cache = True
    module = module_name
    render_template = 'gruene_cms/plugins/chartjs_node.html'

    def get_cache_expiration(self, request, instance, placeholder):
        # 10 Minuten in Sekunden
        if request.user.is_staff:
            return 60*1
        return 60*10

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
    model = models.CalendarNode
    name = _('Calendar')
    allow_children = False
    cache = True
    module = module_name

    def get_cache_expiration(self, request, instance, placeholder):
        # 10 Minuten in Sekunden
        if request.user.is_staff:
            return None
        return 60*10

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
        calendar_items = instance.get_calendar_items()
        labeled_calendars = list(instance.labeled_calendars.all())
        add_calitem_form = None
        user = context['request'].user
        if user.is_staff:
            time_obj = timezone.make_naive(timezone.now(), timezone=timezone.get_current_timezone()).time().replace(minute=0, second=0, microsecond=0)
            add_calitem_form = forms.CreateCalendarItemModelForm(initial={
                'date': timezone.now().date(),
                'time': time_obj.strftime("%H:%M")
            })

        context.update({
            'calendar_items': calendar_items,
            'labeled_calendars': labeled_calendars,
            'current_dt': timezone.now(),
            'add_calitem_form': add_calitem_form
        })

        return context


@plugin_pool.register_plugin
class NewsListNodePlugin(CMSPluginBase):
    model = models.NewsListNode
    name = _('News')
    allow_children = False
    cache = True
    module = module_name

    def get_cache_expiration(self, request, instance, placeholder):
        if request.user.is_staff:
            return None
        return timezone.now() + timezone.timedelta(minutes=10)

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'tiles': 'gruene_cms/plugins/news_tiles_node.html',
            'table': 'gruene_cms/plugins/news_table_node.html',
            'card_v1': 'gruene_cms/plugins/news_card_v1_node.html',
            'card_v2': 'gruene_cms/plugins/news_card_v2_node.html',
            'full': 'gruene_cms/plugins/news_full_node.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(NewsListNodePlugin, self).render(context, instance, placeholder)
        context.update({
            'news_items': instance.get_news_items(),
        })
        return context


@plugin_pool.register_plugin
class TaskNodePlugin(CMSPluginBase):
    model = models.TaskNode
    name = _('Task')
    text_enabled = False
    allow_children = False
    cache = False
    module = module_name
    fieldsets = [
        (None, {
            'fields': (
                ('render_template',),
            )
        }),
        (_('Filters'), {
            'classes': ('collapse',),
            'fields': (
                'categories',
                'limit_own_tasks',
            )
        }),
    ]

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'list': 'gruene_cms/plugins/task_node_list.html',
            'summary': 'gruene_cms/plugins/task_node_summary.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(TaskNodePlugin, self).render(context, instance, placeholder)
        user = context['request'].user
        task_items = instance.get_task_items(user=user)
        context.update({
            'task_items': task_items,
        })
        return context


@plugin_pool.register_plugin
class TaskInlineNodePlugin(TaskNodePlugin):
    text_enabled = True
    # parent_classes = ['TextPlugin']
    render_template = 'gruene_cms/plugins/task_node_summary.html'


@plugin_pool.register_plugin
class LocalFolderNodePlugin(CMSPluginBase):
    model = models.LocalFolderNode
    name = _('Local Folder')
    text_enabled = False
    allow_children = False
    cache = False
    module = module_name

    render_template = 'gruene_cms/plugins/local_folder_node.html'

    def render(self, context, instance, placeholder):
        context = super(LocalFolderNodePlugin, self).render(context, instance, placeholder)
        #user = context['request'].user
        tree_items = instance.webdav_client.get_tree_items(
            entry_path=instance.entry_path,
            # include_root_node=instance.show_root_node
        )
        context.update({
            'tree_items': tree_items,
            'show_root_node': instance.show_root_node,
            'webdav_client_object': instance.webdav_client,
            'extra_css_classes': instance.extra_css_classes,
        })
        return context


@plugin_pool.register_plugin
class DivNodePlugin(CMSPluginBase):
    model = models.DivNode
    name = _('Div Element')
    text_enabled = False
    allow_children = True
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/div_node_plugin.html'


@plugin_pool.register_plugin
class SimpleMenuNodePlugin(CMSPluginBase):
    model = models.SimpleMenuNode
    name = _('Simple Menu')
    allow_children = True
    cache = False
    module = module_name

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'as_p': 'gruene_cms/plugins/simplemenu_node_as_p.html',
            'as_ul_nested': 'gruene_cms/plugins/simplemenu_node_as_ul_nested.html',
            'as_ul_flat': 'gruene_cms/plugins/simplemenu_node_as_ul_flat.html',
            'as_nav_subpages': 'gruene_cms/plugins/simplemenu_node_as_nav_subpages.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(SimpleMenuNodePlugin, self).render(context, instance, placeholder)
        return context


@plugin_pool.register_plugin
class NewstickerItemListNodePlugin(CMSPluginBase):
    model = models.NewstickerItemListNode
    name = _('Newsticker List Node')
    allow_children = False
    cache = False

    def get_render_template(self, context, instance, placeholder):
        render_templates = {
            'default': 'gruene_cms/plugins/newsticker_node_default.html',
        }
        return render_templates[instance.render_template]

    def render(self, context, instance, placeholder):
        context = super(NewstickerItemListNodePlugin, self).render(context, instance, placeholder)
        newsticker_items = apps.get_model('newsticker.TickerItem').objects.all()
        newsticker_items = newsticker_items.filter(created_dt__gte=timezone.now() - timezone.timedelta(days=instance.limit_days))
        if instance.limit_categories.exists():
            newsticker_items = newsticker_items.filter(category__in=instance.limit_categories.all())

        newsticker_items = newsticker_items.order_by('-pub_dt__date', 'category', 'pub_dt')

        by_date = OrderedDict()
        for ni in newsticker_items:
            d = timezone.localtime(ni.pub_dt, timezone=timezone.get_current_timezone()).date()
            cat = ni.category
            if d not in by_date:
                by_date[d] = OrderedDict()

            if cat not in by_date[d]:
                by_date[d][cat] = [ni]
            else:
                by_date[d][cat].append(ni)

        context.update({
            'newsticker_items': newsticker_items,
            'by_date': by_date,
        })
        return context
