from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _

from .models import AggregatedDataNode, GrueneCMSImageBackgroundNode, GrueneCMSAnimateTypingNode


@plugin_pool.register_plugin
class AggregatedDataNodePlugin(CMSPluginBase):
    model = AggregatedDataNode
    name = _('Aggregated Data Node')
    allow_children = False
    cache = False
    render_template = 'gruene_cms/plugins/aggregated_data_node.html'


@plugin_pool.register_plugin
class GrueneCMSImageBackgroundNodePlugin(CMSPluginBase):
    model = GrueneCMSImageBackgroundNode
    name = _('GrueneCMS: Image as Background')
    allow_children = True
    cache = False
    render_template = 'gruene_cms/plugins/gruenecms_image_background_node.html'


@plugin_pool.register_plugin
class GrueneCMSAnimateTypingNodePlugin(CMSPluginBase):
    model = GrueneCMSAnimateTypingNode
    name = _('GrueneCMS: Animate Typing')
    allow_children = False
    cache = False
    render_template = 'gruene_cms/plugins/gruenecms_animate_typing_node.html'
