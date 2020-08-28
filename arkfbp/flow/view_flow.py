from django.http import HttpResponse
from django.utils.decorators import classonlymethod
from django.views import View

from ..flow import Flow, start_flow
from ..request import HttpRequest


class ViewFlow(Flow, View):
    """
    django view
    """

    # 需要手动设置流的访问方式
    allow_http_method = []
    response_type = HttpResponse
    response_status = 200

    @classmethod
    def set_http_method(cls, method: list):
        cls.allow_http_method = method

    def dispatch(self, request, *args, **kwargs):
        request = self.convert_request(request)
        if request.method.upper() in self.allow_http_method:
            return start_flow(self, request)
        return self.http_method_not_allowed(request, *args, **kwargs)

    @classonlymethod
    def pre_as_view(cls, http_method, **initkwargs):
        """
        Before executing the as_view function, pass it the `allow_http_method`
        """
        cls.set_http_method(http_method)
        return super().as_view(**initkwargs)

    def convert_request(self, request):
        return HttpRequest(request.environ)

    def shutdown(self, outputs, **kwargs):
        self.response_status = kwargs.get('response_status', self.response_status)
        super().shutdown(outputs)

    @property
    def response(self):
        self._response = self.response_type(self.outputs, status=self.response_status)
        return self._response
