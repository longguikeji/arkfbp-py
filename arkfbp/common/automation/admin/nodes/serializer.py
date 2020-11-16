"""
serializer
"""
import copy
import os
import time

from django.db import models

from arkfbp.executer import Executer
# pylint: disable=line-too-long
from arkfbp.node import (AutoModelSerializerNode, ListSerializerNode, FunctionNode, CharFieldNode, IntegerFieldNode,
                         FloatFieldNode, AnyFieldNode, UUIDFieldNode, BooleanFieldNode, DateTimeFieldNode)
from arkfbp.utils.util import json_load, get_class_from_path

FIELD_MAPPING = {
    'string': CharFieldNode,
    'integer': IntegerFieldNode,
    'float': FloatFieldNode,
    'object': AutoModelSerializerNode,
    'array': ListSerializerNode,
    'uuid': UUIDFieldNode,
    'any': AnyFieldNode,
    'boolean': BooleanFieldNode,
    'datetime': DateTimeFieldNode,
}

API_TYPE_MAPPING = {
    'create': 'create',
    'delete': 'delete',
    'update': 'update',
    'retrieve': 'retrieve',
}


# Editor your node here.
class SerializerCore(FunctionNode):
    """
    it will generate all serializer nodes and field nodes dynamically,
    finally return the result to the siteapi flow.
    """
    serializer_handler = AutoModelSerializerNode

    def run(self, *args, **kwargs):
        """
        initialize a master serializer node,
        then run this master node to validate request params,
        finally may run the handler function to contact with DB.
        """
        try:
            print('Initializing master serializer node...')
            _, api_detail = get_api_config(self.inputs.method, self.flow.api_config)
            self.intervene(api_detail)
            # api_detail => {"name":"create_user", "type":"create", "request":{}, "response":{}}
            serializer_node = self.get_serializer_node(api_detail['request'], self.flow.config)
            print('Done!')
            # 数据校验
            print('Running master serializer node...')
            outputs = Executer.start_node(serializer_node, self.flow)
            print('Done!')
            if not self.flow.valid_status():
                return outputs
            print('Running handle function...')
            # 获取涉及到的所有原生model的class list
            model_mapping = collect_model_mapping(api_detail['request'], self.flow.config)
            print('model_mapping is', model_mapping)
            # TODO 从相应的validated_data中获取指定model的字段值，然后每个model进行handler的处理
            ret = serializer_node.handle(api_detail, model_mapping, *args, **kwargs)
            print('Done!')
            return ret
        # pylint: disable=broad-except
        except Exception as exception:
            print('exception is', exception)
            return self.flow.shutdown(exception.__str__(), response_status=500)

    # pylint: disable=too-many-locals
    @classmethod
    def get_serializer_node(cls, show_fields, config, serializer_handler=None, instance=None):
        """
        Dynamically generate serializer node with
        field node which in request_config and response.
        Both of api_detail and config are not necessarily in the same file,
        because of model_object field exists.
        """
        cls_name = 'Serializer_%s' % str(time.time()).replace(".", "")
        cls_attr = {}
        for field, detail in show_fields.items():
            # {"username":{"src":"user.username"}}
            #   field => username
            #   detail -> {"src":"user.username"}
            source, _, field_config, meta_config = import_field_config(field, detail, config)
            if source == 'internal':
                continue
            if source == 'meta' and 'object' in field_config['type'].keys():
                node = cls.get_serializer_node(field_config['type']['object'],
                                               meta_config,
                                               serializer_handler=AutoModelSerializerNode,
                                               instance=instance)
                cls_attr.update({field: node})
                continue
            if source == 'meta' and 'array' in field_config['type'].keys():
                child_node = cls.get_serializer_node({'item': field_config['type']['array']['array_item']},
                                                     meta_config,
                                                     instance=instance)
                node = ListSerializerNode(child=child_node, instance=instance)
                cls_attr.update({field: node})
                continue
            cls_attr.update({field: get_field_node(field_config, config)})
        cls_attr.update({'show_fields': show_fields, 'config': config})
        # print('cls_attr is', cls_attr)
        _cls = type(cls_name, (serializer_handler or cls.serializer_handler, ), cls_attr)
        # print('_cls is', _cls)
        return _cls(instance=instance)

    def intervene(self, api_detail):
        """
        Change some properties of flow to interfere with the flow direction.
        """
        # debug or not
        self.flow.debug = api_detail.get('debug', True)


SERIALIZER_FIELD_MAPPING = {
    models.AutoField:
    IntegerFieldNode,
    models.BigIntegerField:
    IntegerFieldNode,
    models.BooleanField:
    BooleanFieldNode,
    models.CharField:
    CharFieldNode,
    models.CommaSeparatedIntegerField:
    CharFieldNode,
    # models.DateField: DateField,
    models.DateTimeField:
    DateTimeFieldNode,
    # models.DecimalField: DecimalField,
    # models.EmailField: EmailField,
    # models.Field: ModelField,
    # models.FileField: FileField,
    models.FloatField:
    FloatFieldNode,
    # models.ImageField: ImageField,
    models.IntegerField:
    IntegerFieldNode,
    # models.NullBooleanField: NullBooleanField,
    models.PositiveIntegerField:
    IntegerFieldNode,
    models.PositiveSmallIntegerField:
    IntegerFieldNode,
    # models.SlugField: SlugField,
    models.SmallIntegerField:
    IntegerFieldNode,
    models.TextField:
    CharFieldNode,
    models.UUIDField:
    UUIDFieldNode,
    # models.TimeField: TimeField,
    # models.URLField: URLField,
    # models.GenericIPAddressField: IPAddressField,
    # models.FilePathField: FilePathField,
}

FIELD_CONFIG_MAPPING = dict(zip(FIELD_MAPPING.values(), FIELD_MAPPING.keys()))


def get_api_config(method, api_config):
    """
    get api config by request http method.
    """
    api_detail = api_config.get(method.lower(), None)
    if not api_detail:
        raise Exception(f'No api config for http_method:{method}!')

    if 'index' in api_config.keys():
        api_detail.update(index=api_config['index'])

    api_type = api_detail.get('type', 'custom')
    return api_type, api_detail


# pylint: disable=no-else-return, protected-access, too-many-nested-blocks
def import_field_config(field_name, field_detail, config):
    """
    import form local meta config or other meta config or model class.
    return 字段来源, 字段路径, 字段具体配置信息
    """
    _field_detail = {}
    if isinstance(field_detail, str):
        path = field_detail
    if isinstance(field_detail, dict):
        _field_detail = copy.deepcopy(field_detail)
        path = _field_detail.pop('src', field_name)
    # 内部扩展的属性，不属于meta和model
    if path.startswith('.'):
        return 'internal', path, None, config
    # _path => ['user', 'username'] or ['username']
    _path = path.split('.')
    if len(_path) == 1:
        # {"meta": {"user": {"title":"","type":{}}}}
        #   _field_name => user
        #   field_config => {"title":"","type":{}}
        _field_name = _path[0]
        field_config = config['meta'][_field_name]
        return 'meta', _field_name, field_config, config
    else:
        # {"user": {"model": "models.user.User"}}
        #   name => user
        #   detail => {"model": "models.user.User"}
        for name, detail in config['module'].items():
            if name == _path[0]:
                _field_name = _path[1]
                if 'model' in detail.keys():
                    cls = get_class_from_path(detail['model'])
                    for item in cls._meta.fields:
                        if _field_name == item.name:
                            field_type = SERIALIZER_FIELD_MAPPING[item.__class__]
                            field_config = {
                                'title': item.verbose_name,
                                'type': {
                                    FIELD_CONFIG_MAPPING[field_type]: {}
                                },
                                **_field_detail
                            }
                            return 'model', detail['model'], field_config, config
                if 'meta' in detail.keys():
                    file_path = os.getcwd()
                    for item in detail['meta'].split('.'):
                        file_path = os.path.join(file_path, item)
                    file_path = f'{file_path}.json'
                    meta_config = json_load(file_path)
                    return 'meta', detail['meta'], meta_config['meta'][_field_name], meta_config

    raise Exception({'error': f'Path:{path} Config Not Exists!'})


def parse_field_config(field_config):
    """
    parse field config.
    """
    for field_type, field_attrs in field_config['type'].items():
        return field_type, field_attrs


def get_field_node(field_config, config):
    """
    get field node.
    """
    required = field_config.get('required', False)
    field_type, field_attrs = parse_field_config(field_config)
    if field_type == 'array':
        return SerializerCore.get_serializer_node(field_attrs, config, serializer_handler=ListSerializerNode)
    if field_type == 'object':
        return SerializerCore.get_serializer_node(field_attrs, config, serializer_handler=AutoModelSerializerNode)
    field_cls = FIELD_MAPPING[field_type]
    field_attrs.update(required=required)
    return field_cls(**field_attrs)


def collect_model_mapping(fields, config):
    """
    fields => {"username":{"src":"model_user.username"}, "password":"password"}
    return: {models.User: ['username', 'password'], models.Group: ['id']}
    """
    model_mapping = {}
    for field, detail in fields.items():
        source, source_path, _, _ = import_field_config(field, detail, config)
        if source == 'model':
            cls = get_class_from_path(source_path)
            if cls not in model_mapping.keys():
                model_mapping[cls] = [field]
                continue
            model_mapping[cls].append(field)

    return model_mapping


def search_available_model(field_name, field_detail, config):
    """
    field_name => username
    field_detail => user or group.user
    {field_name: field_detail}
    """
    source, source_path, field_config, meta_config = import_field_config(field_name, field_detail, config)
    if source == 'internal':
        return None

    if source == 'model':
        model = get_class_from_path(source_path)
        return model

    if 'object' in field_config['type'].keys():
        for key, value in field_config['type']['object'].items():
            model = search_available_model(key, value, meta_config)
            if model:
                return model

    if 'array' in field_config['type'].keys():
        for key, value in field_config['type']['array'].items():
            return search_available_model('item', value, meta_config)

    return None


def reset_response(extend, response, show_fields, config):
    """
    reset response because of `.pagination` and so on.
    """
    if extend == 'pagination':
        # response
        #  {"page": 1, "page_size": 30, "count": "", "results":{}, "next": "", "previous": ""}
        for key, detail in show_fields.items():
            # 判断是否含有扩展的pagination字段，若存在将其加入ret中，并删除原始位置上的字段
            source, _, field_config, _ = import_field_config(key, detail, config)
            if source == 'internal':
                # 进行重构 TODO
                pass
            if source == 'meta':
                if 'object' in field_config['type']:
                    for field, field_detail in field_config['type']['object'].items():
                        if isinstance(field_detail, str) and field_detail.startswith('.pagination'):
                            # 进行重构
                            # param => count or page or next or previous or results
                            param = field_detail.split('.')[-1]
                            # print('param is', param)
                            response['results'][key].update(**{field: response[param]})
                            # response[param]['']
                    return response['results']
    return response
