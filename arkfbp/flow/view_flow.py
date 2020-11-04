"""
View Flow.
"""
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import classonlymethod
from django.views import View

from arkfbp.executer import Executer
from .base import Flow


# pylint: disable=abstract-method
class ViewFlow(Flow, View):
    """
    django view
    """

    # 需要手动设置流的访问方式
    allow_http_method = []
    response_type = JsonResponse
    response_status = 200

    @classmethod
    def set_http_method(cls, method: list):
        """
        set http method.
        """
        cls.allow_http_method = method

    def dispatch(self, request, *args, **kwargs):
        """
        django view function dispatch.
        """
        if request.method.upper() in self.allow_http_method:
            return Executer.start_flow(self, request, *args, **kwargs)
        return self.http_method_not_allowed(request, *args, **kwargs)

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
        if not self.response_type:
            return self._response
        try:
            self._response = self.response_type(self.outputs, status=self.response_status)
        except TypeError:
            # 自动识别响应数据类型
            if isinstance(self.outputs, str):
                return HttpResponse(self.outputs, status=self.response_status)
            if isinstance(self.outputs, int):
                return HttpResponse(str(self.outputs), status=self.response_status)
            if isinstance(self.outputs, dict):
                return JsonResponse(self.outputs, status=self.response_status)
            self._response = self.outputs
            return self._response

        return self._response
