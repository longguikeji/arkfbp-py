"""
Field Node.
"""
# pylint: disable=too-many-lines
import datetime
from typing import Mapping

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.timezone import utc
from pytz import InvalidTimeError

from ..function_node import FunctionNode
from ...utils.exceptions import ValidationError
from ...utils.formatting import LazyFormat


class SkipField(Exception):
    """
    SkipField Exception
    """


def get_attribute(instance, attrs):
    """
    Similar to Python's built in `getattr(instance, attr)`,
    but takes a list of nested attributes, instead of a single attribute.

    Also accepts either attribute lookup on objects or dictionary lookups.
    """
    for attr in attrs:
        try:
            # pylint: disable=isinstance-second-argument-not-valid-type
            if isinstance(instance, Mapping):
                instance = instance[attr]
            else:
                instance = getattr(instance, attr)
        except ObjectDoesNotExist:
            return None

    return instance


NOT_READ_ONLY_WRITE_ONLY = 'May not set both `read_only` and `write_only`'
NOT_READ_ONLY_REQUIRED = 'May not set both `read_only` and `required`'
NOT_REQUIRED_DEFAULT = 'May not set both `required` and `default`'
USE_READONLYFIELD = 'Field(read_only=True) should be ReadOnlyField'
MISSING_ERROR_MESSAGE = ('ValidationError raised by `{class_name}`, but error key `{key}` does '
                         'not exist in the `error_messages` dictionary.')

# FieldNode metadata
_FIELDNODE_NAME = 'field'
_FIELDNODE_KIND = 'field'


class FieldNode(FunctionNode):
    """
    base field node.
    """
    name = _FIELDNODE_NAME
    kind = _FIELDNODE_KIND

    default_validators = []
    default_error_messages = {'required': 'This field is required.', 'null': 'This field may not be null.'}

    # pylint: disable=too-many-arguments
    def __init__(self,
                 *args,
                 read_only=False,
                 write_only=False,
                 required=None,
                 source=None,
                 label=None,
                 help_text=None,
                 style=None,
                 error_messages=None,
                 validators=None,
                 allow_null=False,
                 **kwargs):
        super().__init__(*args, **kwargs)
        # if set required,it should be followed with read_only
        if required is None:
            required = not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), NOT_READ_ONLY_REQUIRED
        assert not (read_only and self.__class__ == FieldNode), USE_READONLYFIELD

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.source = source
        self.help_text = help_text
        self.style = {} if style is None else style
        self.allow_null = allow_null
        self.label = label

        if validators is not None:
            self.validators = list(validators)

        # These are set up by `.bind()` when the field is added to a serializer node.
        self.field_name = None
        self.parent = None
        self.show_value = None

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.source_attrs = None

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        """

        # In order to enforce a consistent style, we error if a redundant
        # 'source' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        assert self.source != field_name, ("It is redundant to specify `source='%s'` on field '%s' in "
                                           "serializer '%s', because it is the same as the field name. "
                                           "Remove the `source` keyword argument." %
                                           (field_name, self.__class__.__name__, parent.__class__.__name__))

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace('_', ' ').capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        self.source_attrs = self.source.split('.')

    def run(self, *args, **kwargs):
        """
        run all validators in node.
        then run validate function which is defined by user.
        """
        error_list = []
        try:
            self.show_value = self.get_value()
        except ValidationError as exception:
            error_list.append(exception.message_dict[self.field_name])
            return self.message_dict(error_list)

        for validator in self.validators:
            try:
                validator(self.show_value)
            except ValidationError as exception:
                error_list.append(exception.message_dict[self.field_name])

        return self.message_dict(error_list)

    def get_value(self):
        """
        get show value.
        """
        if isinstance(self.inputs, dict):
            ret = self.inputs.get(self.field_name, None)
        else:
            ret = self.inputs.ds.get(self.field_name, None)
        if ret is None and self.required:
            raise ValidationError({self.field_name: self.error_messages['required']})

        if ret == '':
            if self.allow_null or not self.required:
                return '' if getattr(self, 'allow_blank', False) else None
        return ret

    @property
    def validators(self):
        """
        get validators.
        """
        if not hasattr(self, '_validators'):
            self._validators = list(self.default_validators)
        return self._validators

    @validators.setter
    def validators(self, validators):
        """
        set validators.
        """
        self._validators = validators

    def source_field(self, field):
        """
        if source is None,return field.
        """
        return self.source or field

    def message_dict(self, error_list):
        """
        error message in dict.
        """
        return {} if not error_list else {self.field_name: error_list}

    def get_attribute(self, instance):
        """
        get attribute from instance.
        """
        try:
            return get_attribute(instance, self.source_attrs)
        except (KeyError, AttributeError):
            if self.allow_null:
                return None
            if not self.required:
                # pylint: disable=raise-missing-from
                raise SkipField()


# CharFieldNode metadata
_CHAR_FIELDNODE_NAME = 'char_field'
_CHAR_FIELDNODE_KIND = 'char_field'


class CharFieldNode(FieldNode):
    """
    string field node.
    """
    name = _CHAR_FIELDNODE_NAME
    kind = _CHAR_FIELDNODE_KIND

    default_error_messages = {
        'invalid': 'Not a valid string.',
        'blank': 'This field may not be blank.',
        'max_length': 'Ensure this field has no more than {max_length} characters,but it has {show_value} characters',
        'min_length': 'Ensure this field has at least {min_length} characters,but it has {show_value} characters',
    }

    def __init__(self, *args, max_length=None, min_length=None, allow_blank=False, trim_whitespace=True, **kwargs):
        super().__init__(*args, **kwargs)
        if max_length is not None:
            self.max_length = max_length
            self.validators.append(self.max_length_validator)
        if min_length is not None:
            self.min_length = min_length
            self.validators.append(self.min_length_validator)
        self.allow_blank = allow_blank
        self.trim_whitespace = trim_whitespace
        self.validators.append(self.allow_blank_validator)

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        return str(value)

    def max_length_validator(self, value):
        """
        max length validator.
        """
        if len(value) > self.max_length:
            message = LazyFormat(self.error_messages['max_length'], max_length=self.max_length, show_value=len(value))
            raise ValidationError({self.field_name: message})

    def min_length_validator(self, value):
        """
        min length validator.
        """
        if len(value) < self.min_length:
            message = LazyFormat(self.error_messages['min_length'], min_length=self.min_length, show_value=len(value))
            raise ValidationError({self.field_name: message})

    def allow_blank_validator(self, value):
        """
        allow blank validator.
        """
        if value == '' or (self.trim_whitespace and str(value).strip() == ''):
            if not self.allow_blank:
                raise ValidationError({self.field_name: self.error_messages['blank']})
            return ''


# IntegerFieldNode metadata
_INTEGER_FIELDNODE_NAME = 'integer_field'
_INTEGER_FIELDNODE_KIND = 'integer_field'


class IntegerFieldNode(FieldNode):
    """
    integer field node.
    """
    name = _INTEGER_FIELDNODE_NAME
    kind = _INTEGER_FIELDNODE_KIND

    default_error_messages = {
        'invalid': 'A valid integer is required.',
        'max_value': 'Ensure this value is less than or equal to {max_value}.',
        'min_value': 'Ensure this value is greater than or equal to {min_value}.',
    }

    def __init__(self, *args, max_value=None, min_value=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_value is not None:
            self.max_value = max_value
            self.validators.append(self.max_value_validator)
        if min_value is not None:
            self.min_value = min_value
            self.validators.append(self.min_value_validator)

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        return int(value)

    def max_value_validator(self, value):
        """
        max length validator.
        """
        if int(value) > self.max_value:
            message = LazyFormat(self.error_messages['max_value'], max_value=self.max_value, show_value=value)
            raise ValidationError({self.field_name: message})

    def min_value_validator(self, value):
        """
        min length validator.
        """
        if int(value) < self.min_value:
            message = LazyFormat(self.error_messages['min_value'], min_value=self.min_value, show_value=value)
            raise ValidationError({self.field_name: message})


# FloatFieldNode metadata
_FLOAT_FIELDNODE_NAME = 'float_field'
_FLOAT_FIELDNODE_KIND = 'float_field'


class FloatFieldNode(FieldNode):
    """
    float field node.
    """
    name = _FLOAT_FIELDNODE_NAME
    kind = _FLOAT_FIELDNODE_KIND

    default_error_messages = {
        'invalid': 'A valid number is required.',
        'max_value': 'Ensure this value is less than or equal to {max_value}.',
        'min_value': 'Ensure this value is greater than or equal to {min_value}.',
    }

    def __init__(self, *args, max_value=None, min_value=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_value is not None:
            self.max_value = max_value
            self.validators.append(self.max_value_validator)
        if min_value is not None:
            self.min_value = min_value
            self.validators.append(self.min_value_validator)

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        return float(value)

    def max_value_validator(self, value):
        """
        max length validator.
        """
        if float(value) > self.max_value:
            message = LazyFormat(self.error_messages['max_value'], max_value=self.max_value, show_value=value)
            raise ValidationError({self.field_name: message})

    def min_value_validator(self, value):
        """
        min length validator.
        """
        if float(value) < self.min_value:
            message = LazyFormat(self.error_messages['min_value'], min_value=self.min_value, show_value=value)
            raise ValidationError({self.field_name: message})


# UUIDFieldNode metadata
_UUID_FIELDNODE_NAME = 'uuid_field'
_UUID_FIELDNODE_KIND = 'uuid_field'


class UUIDFieldNode(FieldNode):
    """
    uuid field node.
    """
    name = _UUID_FIELDNODE_NAME
    kind = _UUID_FIELDNODE_KIND
    valid_formats = ('hex_verbose', 'hex', 'int', 'urn')

    default_error_messages = {
        'invalid': 'Must be a valid UUID.',
    }

    def __init__(self, *args, **kwargs):
        self.uuid_format = kwargs.pop('format', 'hex_verbose')
        if self.uuid_format not in self.valid_formats:
            raise ValueError('Invalid format for uuid representation. '
                             'Must be one of "{}"'.format('", "'.join(self.valid_formats)))
        super().__init__(*args, **kwargs)

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        if self.uuid_format == 'hex_verbose':
            return str(value)
        return getattr(value, self.uuid_format)


# BooleanFieldNode metadata
_BOOLEAN_FIELDNODE_NAME = 'boolean_field'
_BOOLEAN_FIELDNODE_KIND = 'boolean_field'


class BooleanFieldNode(FieldNode):
    """
    boolean field node.
    """
    name = _BOOLEAN_FIELDNODE_NAME
    kind = _BOOLEAN_FIELDNODE_KIND
    TRUE_VALUES = {'t', 'T', 'y', 'Y', 'yes', 'YES', 'true', 'True', 'TRUE', 'on', 'On', 'ON', '1', 1, True}
    FALSE_VALUES = {'f', 'F', 'n', 'N', 'no', 'NO', 'false', 'False', 'FALSE', 'off', 'Off', 'OFF', '0', 0, 0.0, False}
    NULL_VALUES = {'null', 'Null', 'NULL', '', None}
    default_error_messages = {
        'invalid': 'Must be a valid boolean.',
    }

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        if value in self.TRUE_VALUES:
            return True
        if value in self.FALSE_VALUES:
            return False
        if value in self.NULL_VALUES and self.allow_null:
            return None
        return bool(value)


# DateTimeFieldNode metadata
_DATETIME_FIELDNODE_NAME = 'datetime_field'
_DATETIME_FIELDNODE_KIND = 'datetime_field'


class DateTimeFieldNode(FieldNode):
    """
    datetime field node.
    """
    default_error_messages = {
        'invalid': 'Datetime has wrong format. Use one of these formats instead: {format}.',
        'date': 'Expected a datetime but got a date.',
        'make_aware': 'Invalid datetime for the timezone "{timezone}".',
        'overflow': 'Datetime value out of range.'
    }
    datetime_parser = datetime.datetime.strptime

    # pylint: disable=redefined-builtin
    def __init__(self, *args, format=None, input_formats=None, default_timezone=None, **kwargs):
        if format is not None:
            self.format = format
        if input_formats is not None:
            self.input_formats = input_formats
        if default_timezone is not None:
            self.timezone = default_timezone
        super().__init__(*args, **kwargs)

    # pylint: disable=raise-missing-from
    def enforce_timezone(self, value):
        """
        When `self.default_timezone` is `None`, always return naive datetimes.
        When `self.default_timezone` is not `None`, always return aware datetimes.
        """
        field_timezone = getattr(self, 'timezone', self.default_timezone())

        if field_timezone is not None:
            if timezone.is_aware(value):
                try:
                    return value.astimezone(field_timezone)
                except OverflowError:
                    raise ValidationError({self.field_name: self.error_messages['overflow']})

            try:
                return timezone.make_aware(value, field_timezone)
            except InvalidTimeError:
                message = LazyFormat(self.error_messages['make_aware'], timezone=field_timezone)
                raise ValidationError({self.field_name: message})
        elif (field_timezone is None) and timezone.is_aware(value):
            return timezone.make_naive(value, utc)
        return value

    # pylint: disable=no-self-use
    def default_timezone(self):
        """
        default timezone.
        """
        return timezone.get_current_timezone() if settings.USE_TZ else None

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        if not value:
            return None

        output_format = getattr(self, 'format', None)

        if output_format is None or isinstance(value, str):
            return value

        value = self.enforce_timezone(value)

        if output_format.lower() == 'iso-8601':
            value = value.isoformat()
            if value.endswith('+00:00'):
                value = value[:-6] + 'Z'
            return value
        return value.strftime(output_format)


# AnyFieldNode metadata
_ANY_FIELDNODE_NAME = 'any_field'
_ANY_FIELDNODE_KIND = 'any_field'


class AnyFieldNode(FieldNode):
    """
    any field node.
    """
    name = _ANY_FIELDNODE_NAME
    kind = _ANY_FIELDNODE_KIND

    default_error_messages = {}

    # pylint: disable=no-self-use
    def to_representation(self, value):
        """
        to representation value
        """
        return value
