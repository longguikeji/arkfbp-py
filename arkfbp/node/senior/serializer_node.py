"""
Serializer Node
"""
import copy
# pylint: disable=no-name-in-module
from collections import MutableMapping, OrderedDict

from .field_node import FieldNode

# SerializerNode metadata
from ...executer import Executer

_NODE_NAME = 'serializer'
_NODE_KIND = 'serializer'


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


class SerializerNode(FieldNode, metaclass=SerializerNodeMetaclass):
    """
    Serializer Node.
    """
    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        """
        run node.
        """
        # serializer node以self.inputs作为输入，运行其所包含的field_nodes和serializer_nodes，
        # 其中每个子node的inputs都是初始的inputs，而不是每个前驱节点的outputs。
        # 当捕捉到flow状态异常时，将会在此终止流的执行。如果检测顺利，最终返回的还是self.inputs
        error_dict = {}
        for node in self.fields.values():
            outputs = Executer.start_node(node, self.flow)
            if outputs:
                error_dict = error_dict.update(outputs)
        return error_dict if error_dict else self.inputs

    @property
    def fields(self):
        """
        A dictionary such as {field_name: field_instance}.
        """
        fields = BindingDict(self)
        for key, value in self.get_fields().items():
            fields[key] = value
        return fields

    def get_fields(self):
        """
        Returns a dictionary of {field_name: field_instance}.
        """
        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer instance.
        # pylint: disable=no-member
        return copy.deepcopy(self._declared_fields)


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
