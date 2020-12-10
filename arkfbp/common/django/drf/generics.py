"""Process requests from django.

A flow is a django view which process request.
 We convert an interface in config.json to an APIView, and process requests with flows.
"""
from django.utils.decorators import classonlymethod
from rest_framework.generics import GenericAPIView as GenericAPIViewBase
from arkfbp.executer import Executer
from arkfbp.flow.base import Flow


# pylint: disable=abstract-method
class GenericAPIView(Flow, GenericAPIViewBase):
    """
    django view.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        override django view function dispatch.
        """
        if request.method.upper() in self.allow_http_method:
            return Executer.start_flow(self, request, *args, **kwargs)

    @classmethod
    def set_http_method(cls, method: list):
        """
        set http method.
        """
        cls.allow_http_method = method

    @classonlymethod
    def pre_as_view(cls, http_method=None, **initkwargs):
        """
        Before executing the as_view function, pass it the `allow_http_method`
        """
        if http_method:
            cls.set_http_method(http_method)
        return super().as_view(**initkwargs)

    def shutdown(self, outputs, **kwargs):
        """
        shutdown the flow.
        """
        self.response_status = kwargs.get('response_status', self.response_status)
        super().shutdown(outputs)

    @property
    def response(self):
        """
        generate a http response.
        """
        return self.outputs
