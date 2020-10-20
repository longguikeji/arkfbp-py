"""
All ArkFBP Exception
"""
from arkfbp.utils.formatting import LazyFormat


class ValidationError(Exception):
    """
    validation error
    """
    def __init__(self, message):
        """
        message should be a dict or a ValidationError's subclass.
        """
        super().__init__(message)

        if isinstance(message, ValidationError):
            message = message.error_dict

        if isinstance(message, LazyFormat):
            message = message.__str__()

        if isinstance(message, dict):
            self.error_dict = {}
            for field, messages in message.items():
                if isinstance(messages, ValidationError):
                    messages = messages.error_dict
                if isinstance(messages, LazyFormat):
                    messages = messages.__str__()
                self.error_dict[field] = messages
        self.message = message

    @property
    def message_dict(self):
        """
        return error message in dict
        """
        # Trigger an AttributeError if this ValidationError
        # doesn't have an error_dict.
        return self.error_dict if hasattr(self, 'error_dict') else self.message
