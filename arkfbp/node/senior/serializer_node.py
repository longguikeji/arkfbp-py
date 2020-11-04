"""
Serializer Node
"""
import copy
# pylint: disable=no-name-in-module
from collections import MutableMapping, OrderedDict, Iterable
from importlib import import_module

from .field_node import FieldNode

# SerializerNode metadata
from ...executer import Executer
from ...utils.util import json_load


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
        self.instance = None

    def run(self, *args, **kwargs):
        """
        run node.
        """
        # serializer node以self.inputs作为输入，运行其所包含的field_nodes和serializer_nodes，
        # 其中每个子node的inputs都是初始的inputs，而不是每个前驱节点的outputs。
        # 当捕捉到flow状态异常时，将会在此终止流的执行。如果检测顺利，最终返回的还是self.inputs
        error_dict = {}
        inputs = self.inputs
        # pylint: disable=import-outside-toplevel
        from ...common.automation.siteapi.nodes.serializer import get_field_config

        for field, node in self.fields.items():
            # pylint: disable=no-member
            field_type, field_detail = get_field_config(field, self.config)
            if field_type == 'model_object':
                _inputs = inputs[field] if isinstance(inputs, dict) else inputs.ds[field]
                outputs = Executer.start_node(node, self.flow, inputs=_inputs)
                if not self.flow.valid_status():
                    error_dict.update(outputs)
                    continue
                # self.validated_data.update({node.source_field(field): node.validated_data})
            else:
                outputs = Executer.start_node(node, self.flow, inputs=inputs)
                if outputs:
                    error_dict.update(outputs)
                    continue
                model_attr = field_detail.get('model_attr', None)
                if model_attr:
                    # pylint: disable=protected-access
                    value = self.parent.model._default_manager.get(**{model_attr: node.show_value})
                else:
                    value = node.show_value
                self.validated_data.update({node.source_field(field): value})

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
        self._fields = fields
        return fields

    @property
    def _writable_fields(self):
        """
        writable fields.
        """
        for field in self._fields.values():
            if not field.read_only:
                yield field

    @property
    def _readable_fields(self):
        """
        readable fields.
        """
        for field in self._fields.values():
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

    @property
    def data(self):
        """
        instance -> dict.
        """
        if not all((hasattr(self, 'instance'), self.instance)):
            return {}

        if isinstance(self.instance, Iterable):
            objects = [self.to_representation(item) for item in list(self.instance)]
            # pylint: disable=no-member
            rsp_idx_key = self.api_detail.get('response_index_key', None)
            return {rsp_idx_key or f'{self.flow.config["name"]}_objects': objects}

        return self.to_representation(self.instance)

    # pylint: disable=no-member, import-outside-toplevel
    def to_representation(self, instance):
        """
        execute instance -> dict.
        """
        data = {}
        from ...common.automation.siteapi.nodes.serializer import SerializerCore, get_field_config

        for field in self.api_detail['response']:
            field_node = self._fields.get(field) if hasattr(self, '_fields') else self.fields.get(field)
            field_type, field_detail = get_field_config(field, self.config)
            if field_type == 'model_object':
                if field_node and not field_node.write_only:
                    # 存在可用的field node
                    query_set = field_node.retrieve(**{field_detail['index_key']: instance.pk})
                    field_node.instance = query_set[0] if query_set else {}
                    value = field_node.data
                else:
                    # 新建可用的field node
                    config = json_load(field_detail['config_path'])
                    field_node = SerializerCore().get_serializer_node(field_detail, config)
                    query_set = field_node.retrieve(**{field_detail['index_key']: instance.pk})
                    field_node.instance = query_set[0] if query_set else {}
                    value = field_node.data
                data.update({field: value})
                continue
            # 有现成的field node
            if field_node and not field_node.write_only:
                value = getattr(instance, field_node.source_field(field))
                # 用来判断一个外键的属性，并取得其指定的属性值 TODO
                model_attr = field_detail.get('model_attr', None)
                if model_attr:
                    value = getattr(value, model_attr)
            else:
                # 没有现成的field node，新建
                field_node = SerializerCore().get_field_node(field, self.config)
                value = getattr(instance, field_node.source_field(field))
                # 用来判断一个外键的属性，并取得其指定的属性值
                model_attr = field_detail.get('model_attr', None)
                if model_attr:
                    value = getattr(value, model_attr)
            data.update({field: value})
        return data


# ModelSerializerNode metadata
_MODEL_SERIALIZER_NODE_NAME = 'model_serializer'
_MODEL_SERIALIZER_NODE_KIND = 'model_serializer'


class ModelSerializerNode(SerializerNode):
    """
    Django Model Serializer Node
    """
    name = _MODEL_SERIALIZER_NODE_NAME
    kind = _MODEL_SERIALIZER_NODE_KIND
    # import path of the model
    model_path = None

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

    @property
    def model(self):
        """
        serializer node model.
        """
        try:
            model = self.get_model()
            return model
        except NotImplementedError as exception:
            if not self.model_path:
                raise Exception('Valid model-import-path Not exists!') from exception
            _list = self.model_path.split('.')
            model = getattr(import_module('.'.join(_list[:-2])), _list[-1])
            return model

    def get_model(self):
        """custom get model by user"""
        raise NotImplementedError

    def get_object(self, **kwargs):
        """
        get some objects.
        """
        obj = self.model.objects.get(**kwargs)
        return obj

    # pylint: disable=too-many-locals, import-outside-toplevel, no-member, broad-except, unused-argument
    def handle(self, handler, api_detail, *args, **kwargs):
        """
        handle model.
        """
        index = api_detail.get('index', None)
        index_value = kwargs.get(index, None)
        from ...common.automation.siteapi.nodes.serializer import get_field_config
        fields = api_detail.get('request', [])
        for field in fields:
            field_type, field_detail = get_field_config(field, self.config)
            if field_type == 'model_object':
                serializer_node = self._fields.get(field)
                ret = serializer_node.handle(field_detail['handler'], serializer_node.api_detail)

        if handler == 'delete' and index_value is not None:
            try:
                instance = self.get_object(**{index: index_value})
            except Exception:
                return self.flow.shutdown({'error': 'No objects exists'}, response_status=400)
            self.delete(instance)
            return {'delete': 'success'}

        if handler == 'update' and index_value is not None:
            try:
                instance = self.get_object(**{index: index_value})
            except Exception:
                return self.flow.shutdown({'error': 'No objects exists'}, response_status=400)
            self.update(instance, **self.validated_data)
            return self.data

        if handler == 'retrieve':
            page = self.inputs.ds.pop('page', None) or 1
            page_size = self.inputs.ds.pop('page_size', None) or api_detail.get('page_size', None)
            query_set = self.retrieve(**self.inputs.ds)

            def handle(queryset):
                self.instance = queryset
                return self.data

            from .. import PaginationNode
            ret = Executer.start_node(PaginationNode(),
                                      self.flow,
                                      page_size=page_size,
                                      page=page,
                                      handler=handle,
                                      inputs=query_set,
                                      request=self.inputs)
            return ret

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
