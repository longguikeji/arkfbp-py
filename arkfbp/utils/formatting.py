"""
Utility functions to return a formatted name and description.
"""


class LazyFormat:
    """
    Delay formatting until it's actually needed.
    Useful when the format string or one of the arguments is lazy.
    """
    __slots__ = ('format_string', 'args', 'kwargs', 'result')

    def __init__(self, format_string, *args, **kwargs):
        self.result = None
        self.format_string = format_string
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        if self.result is None:
            self.result = self.format_string.format(*self.args, **self.kwargs)
            self.format_string, self.args, self.kwargs = None, None, None
        return self.result

    def __mod__(self, value):
        return str(self) % value
