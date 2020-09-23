from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from ..flow import Flow
from ..flow.executer import FlowExecuter


class GlobalHookFlow(MiddlewareMixin, Flow):
    """
    Base Hook Flow for Django Web Framework
    When 'BaseHookFlow' is initialized, the 'set_mount' method needs
    to be overridden to specify where the hook should be opened.

    For example:
        class HookFlow(BaseHookFlow):
            def create_nodes(self):
                return [
                    {
                        'cls': StartNode,
                        'id': 'start',
                        'next': 'stop'
                    },
                    {
                        'cls': StopNode,
                        'id': 'stop'
                    }
                ]
            def set_mount(self):
                self.before_route = True
    """

    response_type = JsonResponse
    response_status = 200

    def __init__(self, get_response=None):
        self.before_route = False
        self.before_flow = False
        self.after_flow = False
        self.before_exception = False
        self.set_mount()
        super(GlobalHookFlow, self).__init__(get_response)

    def execute_hook(self, hook_switch, request, *args, **kwargs):
        return FlowExecuter.start_flow(self, request, *args, **kwargs) if hook_switch else None

    def process_request(self, request):
        return self.execute_hook(self.before_route, request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        flow_class = view_func.__dict__.get('view_class', None)
        return self.execute_hook(self.before_flow, request, flow_class=flow_class)

    def process_exception(self, request, exception):
        self.execute_hook(self.before_exception, request, exception=exception)

    def process_response(self, request, response):
        self.execute_hook(self.after_flow, request, response=response)
        return response

    def set_mount(self):
        """
        Sets the global hook flow mount location,
        which can be overridden by subclasses
        """

    def shutdown(self, outputs, **kwargs):
        self.response_status = kwargs.get('response_status', self.response_status)
        super().shutdown(outputs)

    @property
    def response(self):
        if not self.response_type:
            return self._response
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
