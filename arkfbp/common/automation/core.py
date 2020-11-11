"""
Automatic crash project code.
"""
import os

from django.urls import path
from .admin.main import Main as AdminView
from .meta_config.main import Main as MetaConfigView
from ...utils.util import json_load

REQUIRED_FIELDS = ('name', 'type', 'meta', 'api', 'module')
DEFAULT_API_TYPES = {'create': 'POST', 'delete': 'DELETE', 'update': 'PATCH', 'retrieve': 'GET'}
ALLOW_HTTP_METHOD = ('POST', 'GET', 'DELETE', 'PUT', 'PATCH')


class MetaConfig:
    """
    Meta config, it will expose to user.
    """

    default_view_flow = AdminView

    def __init__(self, data=None, file=None, view_flow=None, **kwargs):
        if data:
            assert isinstance(data, dict)
        if file:
            assert os.path.isfile(file)
            data = json_load(file)

        for item in REQUIRED_FIELDS:
            if item not in data.keys():
                raise Exception(f'Field:{item} must be contained in meta config file.')

        self.data = data
        self.view_flow = view_flow or self.default_view_flow
        self._cls_attrs = kwargs.get('cls_attrs', None)

    def get_urls(self):
        """
        所有的admin api通过一个ViewFlow统一入口。
        """
        urlpatterns = []
        # traverse all api in meta config.
        for url_suffix, details in self.data['api'].items():
            allow_http_method = []
            _cls_name = self.data['name'].capitalize()
            url_name = self.data['name']
            # traverse all http methods in the api config.

            # {"post":{"name":"", "type":"create", "request":{}, "response":{}}}
            #   http_method => post
            #   detail => {"name":"", "type":"create", "request":{}, "response":{}}
            for http_method, detail in details.items():
                _http_method = http_method.upper()
                if _http_method not in ALLOW_HTTP_METHOD:
                    continue

                _cls_name += f'{detail["name"].capitalize()}'
                url_name += f'-{detail["name"]}'

                allow_http_method.append(_http_method)
                detail.update(http_method=_http_method)
            # build the view class.
            _cls_attrs = {
                'config': self.data,
                'api_config': details,
                'allow_http_method': allow_http_method,
            }
            _cls_bases = (self.view_flow, )
            view_class = type(_cls_name, _cls_bases, _cls_attrs)
            urlpatterns += [path(url_suffix, view_class.pre_as_view(), name=url_name)]

        return urlpatterns


class MetaConfigs:
    """
    Multiple JSON files for Meta Config.
    """
    def __init__(self, file_dir):
        assert os.path.isdir(file_dir)
        self.file_dir = file_dir

    def get_urls(self):
        """
        encapsulate config meta.
        only support json file.
        """
        urlpatterns = []
        for root, _, files in os.walk(self.file_dir):
            for file in files:
                if file.endswith('.json'):
                    urlpatterns += MetaConfig(file=os.path.join(root, file)).get_urls()
        urlpatterns += self.config_url()
        return urlpatterns

    def config_url(self):
        """
        add config url
        """
        _cls_attrs = {'allow_http_method': ['GET'], 'file_dir': self.file_dir, 'debug': False}
        _cls_bases = (MetaConfigView, )
        view_class = type('MetaConfig', _cls_bases, _cls_attrs)
        return [path('meta_config/<meta_name>/', view_class.pre_as_view(), name='meta_config')]
