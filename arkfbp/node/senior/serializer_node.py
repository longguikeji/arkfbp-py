"""
Serializer Node
"""
import copy
# pylint: disable=no-name-in-module
from collections import MutableMapping, OrderedDict

from django.db import models

from .field_node import FieldNode, SkipField

# SerializerNode metadata
from ...executer import Executer


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
        msg = 'Object Delete Success!'
        instance.delete()
        return msg

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
