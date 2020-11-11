"""
Serializer Node
"""
import copy
# pylint: disable=no-name-in-module
from collections import MutableMapping, OrderedDict
from importlib import import_module

from django.db import models

from .field_node import FieldNode, SkipField

# SerializerNode metadata
from ...executer import Executer
from ...utils.util import get_class_from_path


class SerializerNodeMetaclass(type):
    """
    This metaclass sets a dictionary named `_declared_fields` on the class.

    Any instances of `Field` included as attributes on either the class
    or on any of its superclasses will be include in the
    `_declared_fields` dictionary.
    """
    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        """
        get declared fields dynamically from subclass.
        """
        fields = [(field_name, attrs.pop(field_name)) for field_name, obj in list(attrs.items())
                  if isinstance(obj, FieldNode)]

        # If this class is subclassing another Serializer, add that Serializer's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in reversed(bases):
            if hasattr(base, '_declared_fields'):
                # pylint: disable=protected-access
                fields = [(field_name, obj)
                          for field_name, obj in base._declared_fields.items() if field_name not in attrs] + fields

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super().__new__(cls, name, bases, attrs)


# SerializerNode metadata
_SERIALIZER_NODE_NAME = 'serializer'
_SERIALIZER_NODE_KIND = 'serializer'


class SerializerNode(FieldNode, metaclass=SerializerNodeMetaclass):
    """
    Serializer Node.
    """
    name = _SERIALIZER_NODE_NAME
    kind = _SERIALIZER_NODE_KIND
    many = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = kwargs.get('instance', None)

    def run(self, *args, **kwargs):
        """
        run node.
        """

        # serializer node以self.inputs作为输入，运行其所包含的field_nodes和serializer_nodes，
        # 其中每个子node的inputs都是初始的inputs，而不是每个前驱节点的outputs。
        # 当捕捉到flow状态异常时，将会在此终止流的执行。如果检测顺利，最终返回的还是self.inputs
        error_dict = {}
        inputs = self.inputs
        # 判断状态是否正常
        if not self.flow.valid_status():
            error_dict.update(inputs)
        # pylint: disable=import-outside-toplevel

        for field, node in self.fields.items():
            outputs = Executer.start_node(node, self.flow, inputs=inputs)
            if outputs:
                error_dict.update(outputs)
                continue
            print('node.show_value is', node.show_value)
            self.validated_data.update({node.source_field(field): node.show_value})

        return self.flow.shutdown(error_dict, response_status=400) if error_dict else self.inputs

    @property
    def fields(self):
        """
        A dictionary such as {field_name: field_instance}.
        """
        fields = BindingDict(self)
        for key, value in self.get_fields().items():
            fields[key] = value
        # pylint: disable=attribute-defined-outside-init
        return fields

    @property
    def _writable_fields(self):
        """
        writable fields.
        """
        for field in self.fields.values():
            if not field.read_only:
                yield field

    @property
    def _readable_fields(self):
        """
        readable fields.
        """
        for field in self.fields.values():
            if not field.write_only:
                yield field

    def get_fields(self):
        """
        Returns a dictionary of {field_name: field_instance}.
        """
        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer instance.
        # pylint: disable=no-member
        return copy.deepcopy(self._declared_fields)

    @property
    def validated_data(self):
        """
        validated data.
        """
        if not hasattr(self, '_validated_data'):
            self._validated_data = {}

        return self._validated_data

    @validated_data.setter
    def validated_data(self, data):
        """
        set validated data.
        """
        self._validated_data = data

    # pylint: disable=attribute-defined-outside-init
    @property
    def data(self):
        """
        instance -> dict.
        """
        if not hasattr(self, '_data'):
            if self.instance is not None:
                self._data = self.to_representation(self.instance)
            else:
                self._data = self.to_representation(self.validated_data)
        return self._data

    # pylint: disable=no-member
    def to_representation(self, instance):
        """
        execute instance -> dict.
        instance might be a dict or object.
        """
        ret = OrderedDict()
        fields = self._readable_fields
        for field in fields:
            try:
                if isinstance(field, SerializerNode):
                    ret[field.field_name] = field.to_representation(instance)
                else:
                    attribute = field.get_attribute(instance)
                    ret[field.field_name] = field.to_representation(attribute)
            except SkipField:
                continue
        return ret


# ListSerializerNode metadata
_LIST_SERIALIZER_NODE_NAME = 'list_serializer'
_LIST_SERIALIZER_NODE_KIND = 'list_serializer'


class ListSerializerNode(SerializerNode):
    """
    List serializer node.
    """
    name = _LIST_SERIALIZER_NODE_NAME
    kind = _LIST_SERIALIZER_NODE_KIND
    child = None
    many = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None, '`child` is a required argument in ListSerializerNode.'

    def to_representation(self, instance):
        """
        List of object instances -> List of dicts of primitive data types.
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = instance.all() if isinstance(instance, models.Manager) else instance
        return [self.child.to_representation(item)['item'] for item in iterable]


# ModelSerializerNode metadata
_MODEL_SERIALIZER_NODE_NAME = 'model_serializer'
_MODEL_SERIALIZER_NODE_KIND = 'model_serializer'


class ModelSerializerNode(SerializerNode):
    """
    Django Model Serializer Node
    """
    name = _MODEL_SERIALIZER_NODE_NAME
    kind = _MODEL_SERIALIZER_NODE_KIND
    model = None

    def create(self, **data):
        """
        model create.
        """
        # pylint: disable=protected-access
        self.instance = self.model._default_manager.create(**data)
        return self.instance

    def update(self, instance, **data):
        """
        model update.
        """
        instance.__dict__.update(**data)
        instance.save()
        self.instance = instance
        return instance

    @staticmethod
    def delete(instance):
        """
        model delete.
        """
        instance.delete()
        return 'delete success!'

    def retrieve(self, **data):
        """
        model retrieve.
        """
        # pylint: disable=protected-access
        query_set = self.model._default_manager.filter(**data).order_by()
        self.instance = query_set
        return query_set

    def get_object(self, **kwargs):
        """
        get some objects.
        """
        obj = self.model.objects.get(**kwargs)
        return obj


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
        from ...common.automation.admin.nodes.serializer import SerializerCore, search_available_model

        index_value = None
        for key, value in api_detail.get('index', {}).items():
            # TODO 校验index value的合法性
            # _, source_path, _, _ = import_field_config(key, value, self.flow.config)
            path = value if isinstance(value, str) else value.get('src')
            index = path.split('.')[-1]
            index_value = kwargs.get(key, None)
            break

        handler = api_detail.get('type', None)
        if handler == 'create':
            results = {}
            for model, field in model_mapping.items():
                self.model = model
                # pylint: disable=consider-using-dict-comprehension
                collect_data = dict([(item, self.validated_data.get(item, None)) for item in field])
                print('collect_data is', collect_data)
                results[model] = self.create(**collect_data)
            print('results is', results)
            # TODO 通过response参数新建一个serializer，将相关的参数与results结合后返回特定格式的数据
            self.instance = None
            for key, value in results.items():
                node = SerializerCore.get_serializer_node(api_detail['response'], self.flow.config, instance=value)
                return node.data

            return self.data

        if handler == 'delete' and index_value is not None:
            for key, value in api_detail['index'].items():
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

        if handler == 'update' and index_value is not None:
            for key, value in api_detail['request'].items():
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

        if handler == 'retrieve':

            for key, value in api_detail['response'].items():
                model = search_available_model(key, value, self.flow.config)
                if model:
                    self.model = model
                    break

            pagination_config = api_detail.get('pagination')
            pagination = pagination_config.get('enabled', False) if pagination_config else False
            if pagination:
                page_query_param = pagination_config.get('page_query_param', 'page')
                page_size_query_param = pagination_config.get('page_size_query_param', 'page_size')
                page = self.inputs.ds.pop(page_query_param, 1)
                page_size = self.inputs.ds.pop(page_size_query_param, 20)

            query_set = self.retrieve(**self.inputs.ds)
            node = SerializerCore.get_serializer_node(api_detail['response'], self.flow.config, instance=query_set)

            if pagination:
                from .. import PaginationNode
                count_param = pagination_config.get('count_param')
                results_param = pagination_config.get('results_param')
                next_param = pagination_config.get('next_param')
                previous_param = pagination_config.get('previous_param')
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
                return ret

            return node.data

        if handler == 'custom':
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


class BindingDict(MutableMapping):
    """
    This dict-like object is used to store fields on a serializer node.

    This ensures that whenever fields are added to the serializer we call
    `field.bind()` so that the `field_name` and `parent` attributes
    can be set correctly.
    """
    def __init__(self, serializer_node):
        self.serializer_node = serializer_node
        self.fields = OrderedDict()

    def __setitem__(self, key, node):
        self.fields[key] = node
        node.bind(field_name=key, parent=self.serializer_node)

    def __getitem__(self, key):
        return self.fields[key]

    def __delitem__(self, key):
        del self.fields[key]

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __repr__(self):
        return dict.__repr__(self.fields)


class ReturnDict(OrderedDict):
    """
    Return object from `serializer.data` for the `Serializer` class.
    Includes a backlink to the serializer instance for renderers
    to use if they need richer field information.
    """
    def __init__(self, *args, **kwargs):
        self.serializer = kwargs.pop('serializer')
        super().__init__(*args, **kwargs)

    def copy(self):
        return ReturnDict(self, serializer=self.serializer)

    def __repr__(self):
        return dict.__repr__(self)

    def __reduce__(self):
        # Pickling these objects will drop the .serializer backlink,
        # but preserve the raw data.
        return (dict, (dict(self), ))
