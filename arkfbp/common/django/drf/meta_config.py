"""
Automatic crash project code.
"""
import importlib
import os

from django.apps import apps
from common.django.drf.generics import ViewsetMeta
from django.urls import path
from common.django.drf.flows.dispatch import Main as ModelViewSet
#from .generics import ModelViewSet
from arkfbp.common.django.app.automation.flows.meta_config.main import Main as MetaConfigView

from django.apps import apps
from rest_framework.routers import DefaultRouter
from utils.util import json_load

REQUIRED_FIELDS = ('name', 'type', 'meta', 'api', 'module')
DEFAULT_API_TYPES = {'create': 'POST', 'delete': 'DELETE', 'update': 'PATCH', 'retrieve': 'GET'}
ALLOW_HTTP_METHOD = ('POST', 'GET', 'DELETE', 'PUT', 'PATCH')


#def _import_serializer_class(self, location: str):
#    """
#    Resolves a dot-notation string to serializer class.
#    <app>.<SerializerName> will automatically be interpreted as:
#    <app>.serializers.<SerializerName>
#    """
#    pieces = location.split(".")
#    class_name = pieces.pop()
#
#    if pieces[len(pieces) - 1] != "serializers":
#        pieces.append("serializers")
#
#    module = importlib.import_module(".".join(pieces))
#    return getattr(module, class_name)

def parse_router(router_info):
    return None

def parse_env_from_conf(app_label, filename, conf):
    """从conf文件里面读取router, queryset, model, serializer 等、RESTAPI求值环境所需要的变量。"""
    router_info = conf.get('api', None)
    route_path = conf.get('name', None)
    model_name = conf.get('model', None)
    serializer_class_name = conf.get('serializer_class', None)

    model = None
    queryset = None
    serializer_class = None
    router = None
    try:
        model = apps.get_model(model_name)
    except FloatingPointError as e:
        print(e)
    queryset = model.objects.all()
    if serializer_class_name:
        serializer_class = importlib.import_module(serializer_class_name)
    if router_info:
        router = parse_router(router_info)
    else:
        router = DefaultRouter()
    return router, route_path, {
        'model': model,
        'queryset': queryset,
        'serializer_class': serializer_class
    }


class MetaConfigs:
    """从各个app/api_config里面取出含有"model"字段的conf，每个conf代表一个viewset和一系列url。"""

    def __init__(self, apps):
        self._apps = apps

    def get_urls(self):
        urlpatterns = []
        for app_label in self._apps:
            urls = self.get_urls_of_one_app(app_label)
            urlpatterns += urls
        return urlpatterns

    def get_urls_of_one_app(self, app_label):
        """从一个app的 api_config里面读出所有具有model定义的conf.json生成一套Viewset.
        """
        urlpatterns = []
        app_path = apps.get_app_config(app_label).path
        conf_path = os.path.join(app_path, 'api_config')
        for root, _, files in os.walk(conf_path):
            for file in files:
                if file.endswith('.json'):
                    data = json_load(os.path.join(conf_path, file))
                    #print('file', file)
                    filename = file.split('.')[0]
                    if 'model' in data:
                        viewset_name = f'{app_label}'
                        router, route_path, env = parse_env_from_conf(app_label, filename, data)
                        Viewset = ViewsetMeta(viewset_name, (ModelViewSet,), env)
                        #print(Viewset)
                        #print(Viewset)
                        router.register(route_path, Viewset)
                        urlpatterns += router.urls
        urlpatterns += self.config_url()
        return urlpatterns

    def config_url(self):
        """
        add config url
        """
        urlpatterns = []
        for app_label in self._apps:
            urlpatterns += self.config_url_of_one_app(app_label)
        return urlpatterns

    def config_url_of_one_app(self, app_label):
        urlpatterns = []
        app_path = apps.get_app_config(app_label).path
        conf_path = os.path.join(app_path, 'api_config')
        for root, _, files in os.walk(conf_path):
            for file in files:
                if file.endswith('.json'):
                    _cls_attrs = {'allow_http_method': ['GET'], 'file_dir': app_path, 'debug': False}
                    _cls_bases = (MetaConfigView, )
                    view_class = type('MetaConfig', _cls_bases, _cls_attrs)
                    urlpatterns += [path(f'meta_config/<meta_name>/', view_class.pre_as_view(), name='meta_config')]
        return urlpatterns
