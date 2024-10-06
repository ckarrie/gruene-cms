from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import AggregatedDataNode, GrueneCMSImageBackgroundNode, GrueneCMSAnimateTypingNode, LimitUserGroupNode, ChartJSNode

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
    allow_children = False
    cache = False
    module = module_name
    render_template = 'gruene_cms/plugins/gruenecms_animate_typing_node.html'


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
            timestamp__gte=timezone.now() - timezone.timedelta(hours=2)
        ).order_by('timestamp')
        for ah in dataset_qs:
            dataset.append(ah.value)
            labels.append(ah.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M"))

        context.update({
            'dataset_data': dataset,
            'labels_data': labels,
        })

        return context
