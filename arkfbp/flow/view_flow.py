from django.http import JsonResponse, HttpResponse
from django.utils.decorators import classonlymethod
from django.views import View

from ..flow import Flow
from ..flow.executer import FlowExecuter
from ..request import HttpRequest


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
        cls.allow_http_method = method

    def dispatch(self, request, *args, **kwargs):
        request = self.convert_request(request)
        if request.method.upper() in self.allow_http_method:
            return FlowExecuter.start_flow(self, request)
        return self.http_method_not_allowed(request, *args, **kwargs)

    @classonlymethod
    def pre_as_view(cls, http_method, **initkwargs):
        """
        Before executing the as_view function, pass it the `allow_http_method`
        """
        cls.set_http_method(http_method)
        return super().as_view(**initkwargs)

    @classmethod
    def convert_request(cls, _request):
        request = HttpRequest(_request.environ)
        request.__dict__.update(_request.__dict__)
        return request

    def shutdown(self, outputs, **kwargs):
        self.response_status = kwargs.get('response_status', self.response_status)
        super().shutdown(outputs)

    @property
    def response(self):
        try:
            self._response = self.response_type(self.outputs, status=self.response_status)
        except TypeError:
            # 自动识别响应数据类型
            if type(self.outputs) == str:
                return HttpResponse(self.outputs, status=self.response_status)
            if type(self.outputs) == int:
                return HttpResponse(str(self.outputs), status=self.response_status)
            if type(self.outputs) == dict:
                return JsonResponse(self.outputs, status=self.response_status)
        return self._response
