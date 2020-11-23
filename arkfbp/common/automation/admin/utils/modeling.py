"""
自动化项目，JSON Config建模相关.
"""
import copy
import os
import time
from importlib import import_module

from django.db import models

from arkfbp.executer import Executer
from arkfbp.node import (CharFieldNode, IntegerFieldNode, FloatFieldNode, ListSerializerNode, AnyFieldNode,
                         UUIDFieldNode, BooleanFieldNode, DateTimeFieldNode, ModelSerializerNode, SerializerNode,
                         PaginationNode)

from arkfbp.utils.util import get_class_from_path, json_load

# ModelSerializerNode metadata
_AUTO_MODEL_SERIALIZER_NODE_NAME = 'auto_model_serializer'
_AUTO_MODEL_SERIALIZER_NODE_KIND = 'auto_model_serializer'


class AutoModelSerializerNode(ModelSerializerNode, SerializerNode):
    """
    Auto Model SerializerNode
    """
    name = _AUTO_MODEL_SERIALIZER_NODE_NAME
    kind = _AUTO_MODEL_SERIALIZER_NODE_KIND

    # pylint: disable=too-many-locals, import-outside-toplevel, no-member,
    # pylint: disable=broad-except, unused-argument, too-many-branches, too-many-statements
    def handle(self, api_detail, model_mapping, *args, **kwargs):
        """
        handle model.
        """
        # pylint: disable=line-too-long

        index_value = None
        for key, value in api_detail.get(CONFIG_API_INDEX, {}).items():
            path = value if isinstance(value, str) else value.get(FIELD_SRC)
            index = path.split('.')[-1]
            index_value = kwargs.get(key, None)
            break

        handler = api_detail.get(API_TYPE, None)
        if handler == API_TYPE_MAPPING['create']:
            results = {}
            for model, fields in model_mapping.items():
                self.model = model
                # pylint: disable=consider-using-dict-comprehension
                collect_data = dict([(field[1], self.validated_data.get(field[1])) for field in fields])
                results[model] = self.create(**collect_data)
            response = {}
            for model, instance in results.items():
                struct, config = single_model_response(model, api_detail[API_RESPONSE], self.flow.config)
                node = get_serializer_node(struct, config, instance=instance)
                response.update(**node.data)
            return response

        if handler == API_TYPE_MAPPING['delete'] and index_value is not None:
            for key, value in api_detail[CONFIG_API_INDEX].items():
                model = search_available_model(key, value, self.flow.config)
                if model:
                    self.model = model
                    break
            try:
                instance = self.get_object(**{index: index_value})
            except Exception:
                return self.flow.shutdown({'error': 'No objects exists'}, response_status=400)
            self.delete(instance)
            return {'delete': 'success'}

        if handler == API_TYPE_MAPPING['update'] and index_value is not None:
            for key, value in api_detail[API_REQUEST].items():
                model = search_available_model(key, value, self.flow.config)
                if model:
                    self.model = model
                    break
            try:
                instance = self.get_object(**{index: index_value})
            except Exception:
                return self.flow.shutdown({'error': 'No objects exists'}, response_status=400)
            self.update(instance, **self.validated_data)
            return self.data

        if handler == API_TYPE_MAPPING['retrieve']:

            for key, value in api_detail[API_RESPONSE].items():
                model = search_available_model(key, value, self.flow.config)
                if model:
                    self.model = model
                    break

            pagination_config = api_detail.get('pagination')
            pagination = pagination_config.get('enabled', False) if pagination_config else False
            if pagination:
                page_query_param = 'page'
                page_size_query_param = 'page_size'
                for key, detail in api_detail[API_REQUEST].items():
                    if detail == '.pagination.page':
                        page_query_param = key
                    if detail == '.pagination.page_size':
                        page_size_query_param = key
                page = self.inputs.ds.pop(page_query_param, 1)
                page_size = self.inputs.ds.pop(page_size_query_param, 20)

            query_set = self.retrieve(**self.inputs.ds)
            node = get_serializer_node(api_detail[API_RESPONSE], self.flow.config, instance=query_set)

            if pagination:
                count_param = pagination_config.get('count_param', 'count')
                results_param = pagination_config.get('results_param', 'results')
                next_param = pagination_config.get('next_param', 'next')
                previous_param = pagination_config.get('previous_param', 'previous')
                paginated_response = pagination_config.get('paginated_response')
                if paginated_response:
                    paginated_response = get_class_from_path(paginated_response)
                pagination_node = PaginationNode()
                ret = Executer.start_node(pagination_node,
                                          self.flow,
                                          page_size=page_size,
                                          page=page,
                                          inputs=query_set,
                                          request=self.inputs,
                                          count_param=count_param,
                                          results_param=results_param,
                                          next_param=next_param,
                                          previous_param=previous_param,
                                          page_query_param=page_query_param,
                                          page_size_query_param=page_size_query_param,
                                          serializer_node=node,
                                          paginated_response=paginated_response)
                # 进行自定义重组数据结构
                ret = reset_response('pagination', ret, api_detail[API_RESPONSE], self.flow.config)

                return ret

            return node.data

        if handler == API_TYPE_MAPPING['custom']:
            handler_path = api_detail['flow']
            clz = import_module(f'{handler_path}.main')
            flow = clz.Main()
            ret = Executer.start_flow(
                flow,
                self.inputs,
                validated_data=self.validated_data,
            )
            return ret

        raise Exception('Invalid SerializerCore handler!')


# JSON config master fields definition
CONFIG_NAME = 'name'
CONFIG_TYPE = 'type'
CONFIG_MODULE = 'module'
CONFIG_META = 'meta'
CONFIG_API = 'api'
CONFIG_API_INDEX = 'index'

# field source definition
SOURCE_MODEL = 'model'
SOURCE_META = 'meta'
SOURCE_INTERNAL = 'internal'

# field config definition
OBJECT_TYPE = 'object'
ARRAY_TYPE = 'array'
ARRAY_TYPE_ITEM = 'item'
FIELD_TYPE = 'type'
FIELD_TITLE = 'title'
FIELD_SRC = 'src'
FIELD_REQUIRED = 'required'

# api config definition
API_TYPE = 'type'
API_REQUEST = 'request'
API_RESPONSE = 'response'

# extend for internal field
EXTEND_PAGINATION = 'pagination'

# meta字段的类型
META_FIELD_MAPPING = {
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

# META_FIELD_MAPPING的key与value的位置对调
REVERSE_META_FIELD_MAPPING = dict(zip(META_FIELD_MAPPING.values(), META_FIELD_MAPPING.keys()))

# 默认api处理类型
API_TYPE_MAPPING = {
    'create': 'create',
    'delete': 'delete',
    'update': 'update',
    'retrieve': 'retrieve',
    'custom': 'custom'
}

# model's fields <=> field nodes
MODEL_FIELD_MAPPING = {
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
    # models.DateField: DateFieldNode,
    models.DateTimeField:
    DateTimeFieldNode,
    # models.DecimalField: DecimalFieldNode,
    # models.EmailField: EmailFieldNode,
    # models.Field: ModelFieldNode,
    # models.FileField: FileFieldNode,
    models.FloatField:
    FloatFieldNode,
    # models.ImageField: ImageFieldNode,
    models.IntegerField:
    IntegerFieldNode,
    # models.NullBooleanField: NullBooleanFieldNode,
    models.PositiveIntegerField:
    IntegerFieldNode,
    models.PositiveSmallIntegerField:
    IntegerFieldNode,
    # models.SlugField: SlugFieldNode,
    models.SmallIntegerField:
    IntegerFieldNode,
    models.TextField:
    CharFieldNode,
    models.UUIDField:
    UUIDFieldNode,
    # models.TimeField: TimeFieldNode,
    # models.URLField: URLFieldNode,
    # models.GenericIPAddressField: IPAddressFieldNode,
    # models.FilePathField: FilePathFieldNode,
}


def get_api_config(method: str, api_config: dict) -> (str, dict):
    """
    get api config from meta config by request http method.
    """
    api_detail = api_config.get(method.lower())
    if not api_detail:
        raise Exception(f'No api config for http_method:{method}!')

    if CONFIG_API_INDEX in api_config.keys():
        api_detail.update(index=api_config[CONFIG_API_INDEX])

    return api_detail.get(CONFIG_TYPE, API_TYPE_MAPPING['custom']), api_detail


# pylint: disable=no-else-return, protected-access, too-many-nested-blocks
def import_field_config(field_name, field_detail, config):
    """
    import form local meta config or other meta config or model class.
    return < 字段来源, 字段路径, 字段具体配置信息, 完整meta config >.
    """
    _field_detail = {}
    if isinstance(field_detail, str):
        path = field_detail
    if isinstance(field_detail, dict):
        _field_detail = copy.deepcopy(field_detail)
        path = _field_detail.pop(FIELD_SRC, field_name)
    # 内部扩展的属性，不属于meta和model
    if path.startswith('.'):
        return SOURCE_INTERNAL, path, None, config
    # _path => ['user', 'username'] or ['username']
    _path = path.split('.')
    if len(_path) == 1:
        # {"meta": {"user": {"title":"","type":{}}}}
        #   _field_name => user
        #   field_config => {"title":"","type":{}}
        _field_name = _path[0]
        field_config = config[CONFIG_META][_field_name]
        return SOURCE_META, _field_name, field_config, config
    else:
        # {"user": {"model": "models.user.User"}}
        #   name => user
        #   detail => {"model": "models.user.User"}
        for name, detail in config[CONFIG_MODULE].items():
            if name == _path[0]:
                _field_name = _path[1]
                if SOURCE_MODEL in detail.keys():
                    cls = get_class_from_path(detail[SOURCE_MODEL])
                    for item in cls._meta.fields:
                        if _field_name == item.name:
                            field_type = MODEL_FIELD_MAPPING[item.__class__]
                            field_config = {
                                FIELD_TITLE: item.verbose_name,
                                FIELD_TYPE: {
                                    REVERSE_META_FIELD_MAPPING[field_type]: {}
                                },
                                **_field_detail
                            }
                            return SOURCE_MODEL, detail[SOURCE_MODEL], field_config, config
                if SOURCE_META in detail.keys():
                    file_path = os.getcwd()
                    for item in detail[SOURCE_META].split('.'):
                        file_path = os.path.join(file_path, item)
                    file_path = f'{file_path}.json'
                    meta_config = json_load(file_path)
                    return SOURCE_META, detail[SOURCE_META], meta_config[SOURCE_META][_field_name], meta_config

    raise Exception({'error': f'Path:{path} Config Not Exists!'})


# pylint: disable=too-many-locals
def get_serializer_node(show_fields, config, serializer_handler=AutoModelSerializerNode, instance=None):
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
        if source == SOURCE_INTERNAL:
            continue

        if source == SOURCE_META and OBJECT_TYPE in field_config[FIELD_TYPE].keys():
            node = get_serializer_node(field_config[FIELD_TYPE][OBJECT_TYPE],
                                       meta_config,
                                       serializer_handler=AutoModelSerializerNode,
                                       instance=instance)
            cls_attr.update({field: node})
            continue

        if source == SOURCE_META and ARRAY_TYPE in field_config[FIELD_TYPE].keys():
            child_node = get_serializer_node({ARRAY_TYPE_ITEM: field_config[FIELD_TYPE][ARRAY_TYPE][ARRAY_TYPE_ITEM]},
                                             meta_config,
                                             instance=instance)
            node = ListSerializerNode(child=child_node, instance=instance)
            cls_attr.update({field: node})
            continue

        if source == SOURCE_MODEL:
            source_name = detail.split('.')[-1] if isinstance(detail, str) else detail[FIELD_SRC].split('.')[-1]
            source_name = None if source_name == field else source_name
            cls_attr.update({field: get_field_node(field_config, config, source=source_name)})
            continue

    cls_attr.update({'show_fields': show_fields, 'config': config})
    _cls = type(cls_name, (serializer_handler, ), cls_attr)
    return _cls(instance=instance)


def get_field_node(field_config, config, source=None):
    """
    get field node.
    """
    required = field_config.get(FIELD_REQUIRED, False)
    field_type, field_attrs = tuple(field_config[FIELD_TYPE].items())[0][0], tuple(
        field_config[FIELD_TYPE].items())[0][1]
    if field_type == ARRAY_TYPE:
        return get_serializer_node(field_attrs, config, serializer_handler=ListSerializerNode)
    if field_type == OBJECT_TYPE:
        return get_serializer_node(field_attrs, config, serializer_handler=AutoModelSerializerNode)
    field_cls = META_FIELD_MAPPING[field_type]
    field_attrs.update(required=required)
    if source:
        field_attrs.update(source=source)
    return field_cls(**field_attrs)


def collect_model_mapping(fields, config):
    """
    fields => {"username":{"src":"model_user.username"}, "password":"password"}
    return: {models.User: ['username', 'password'], models.Group: ['id']}
    """
    model_mapping = {}
    for field, detail in fields.items():
        source, source_path, _, _ = import_field_config(field, detail, config)
        if source == SOURCE_MODEL:
            model_field = detail.split('.')[-1] if isinstance(detail, str) else detail[FIELD_SRC].split('.')[-1]
            cls = get_class_from_path(source_path)
            if cls not in model_mapping.keys():
                # (field, field_name) => (show_field, model_field)
                model_mapping[cls] = [(field, model_field)]
                continue
            model_mapping[cls].append((field, model_field))

    return model_mapping


def search_available_model(field_name, field_detail, config):
    """
    field_name => username
    field_detail => user or group.user
    {field_name: field_detail}
    """
    source, source_path, field_config, meta_config = import_field_config(field_name, field_detail, config)
    if source == SOURCE_INTERNAL:
        return None

    if source == SOURCE_MODEL:
        model = get_class_from_path(source_path)
        return model

    if OBJECT_TYPE in field_config[FIELD_TYPE].keys():
        for key, value in field_config[FIELD_TYPE][OBJECT_TYPE].items():
            model = search_available_model(key, value, meta_config)
            if model:
                return model

    if ARRAY_TYPE in field_config[FIELD_TYPE].keys():
        for key, value in field_config[FIELD_TYPE][ARRAY_TYPE].items():
            return search_available_model(ARRAY_TYPE_ITEM, value, meta_config)

    return None


def reset_response(extend, response, show_fields, config):
    """
    reset response because of `.pagination` and so on.
    """
    if extend == EXTEND_PAGINATION:
        # response
        #  {"page": 1, "page_size": 30, "count": "", "results":{}, "next": "", "previous": ""}
        for key, detail in show_fields.items():
            # 判断是否含有扩展的pagination字段，若存在将其加入ret中，并删除原始位置上的字段
            source, _, field_config, _ = import_field_config(key, detail, config)
            if source == SOURCE_INTERNAL:
                pass
            if source == SOURCE_META:
                if OBJECT_TYPE in field_config[FIELD_TYPE]:
                    for field, field_detail in field_config[FIELD_TYPE][OBJECT_TYPE].items():
                        if isinstance(field_detail, str) and field_detail.startswith(f'.{EXTEND_PAGINATION}'):
                            # 进行重构
                            # param => count or page or next or previous or results
                            param = field_detail.split('.')[-1]
                            response['results'][key].update(**{field: response[param]})
                    return response['results']
    return response


def single_model_response(model, struct, config):
    """
    reset response struct for single model.
    """
    _struct = {}
    _config = copy.deepcopy(config)
    for field, detail in struct.items():
        source, source_path, field_config, config = import_field_config(field, detail, config)
        if source == SOURCE_MODEL and source_path.split('.')[-1] == model.__name__:
            _struct.update(**{field: detail})

        if source == SOURCE_META and OBJECT_TYPE in field_config[FIELD_TYPE].keys():
            for key, value in field_config[FIELD_TYPE][OBJECT_TYPE].items():
                _source, _source_path, _, _ = import_field_config(key, value, config)
                if _source == SOURCE_MODEL:
                    if _source_path.split('.')[-1] != model.__name__:
                        del _config[SOURCE_META][source_path][FIELD_TYPE][OBJECT_TYPE][key]
                    else:
                        _struct.update(**{field: detail})

        if source == SOURCE_META and ARRAY_TYPE in field_config[FIELD_TYPE].keys():
            # 一般情况下，array不会出现在single_model_response中
            pass

    return _struct, _config
